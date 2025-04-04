import os
import json
import logging
import multiprocessing
import time
from datetime import datetime
import watchdog.events
import watchdog.observers
from dotenv import load_dotenv
# Telegram Bot Libraries
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    ApplicationBuilder
)

load_dotenv()
# Configuration
BOT_TOKEN = os.getenv('telegram_api_key')
RECORDINGS_PATH = r'C:\Recordings'
REGISTERED_USERS_FILE = 'registered_users.json'
ADMIN_USER_ID = int(os.getenv('ADMIN_ID'))  # Your Telegram user ID for admin controls

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UserRegistryManager:
    @staticmethod
    def load_registered_users():
        """Load registered users from JSON file"""
        try:
            with open(REGISTERED_USERS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_registered_users(users):
        """Save registered users to JSON file"""
        with open(REGISTERED_USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)

class TelegramBotHandler:
    def __init__(self, token, recordings_path):
        self.token = token
        self.recordings_path = recordings_path
        self.registered_users = UserRegistryManager.load_registered_users()

    def start_bot(self):
        """Start the Telegram bot in a separate process"""
        from telegram.ext import ApplicationBuilder, CommandHandler
        
        # Create bot application
        application = ApplicationBuilder().token(self.token).build()

        # Register command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("register", self.register_command))
        application.add_handler(CommandHandler("list_recent", self.list_recent_recordings))
        application.add_handler(CommandHandler("remove_user", self.admin_remove_user))

        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        await update.message.reply_text(
            "Welcome to the Motion Detection Bot! "
            "Use /register to get access to motion detection files."
        )

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user registration"""
        user = update.effective_user
        user_id = str(user.id)

        # Check if user is already registered
        if user_id in self.registered_users:
            await update.message.reply_text("You are already registered!")
            return

        # Add user to registered users
        self.registered_users[user_id] = {
            'username': user.username or user.first_name,
            'full_name': f"{user.first_name} {user.last_name}" if user.last_name else user.first_name,
            'registered_at': datetime.now().isoformat()
        }
        UserRegistryManager.save_registered_users(self.registered_users)

        await update.message.reply_text(
            f"You have been registered, {self.registered_users[user_id]['full_name']}!"
        )

    async def list_recent_recordings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List recent motion detection recordings"""
        user_id = str(update.effective_user.id)

        # Check user authorization
        if user_id not in self.registered_users:
            await update.message.reply_text("You are not authorized. Use /register first.")
            return

        # Get recent recordings
        try:
            recent_files = sorted(
                [f for f in os.listdir(self.recordings_path) if f.endswith('.mp4')],
                key=lambda x: os.path.getctime(os.path.join(self.recordings_path, x)),
                reverse=True
            )[:5]  # Get 5 most recent files

            if not recent_files:
                await update.message.reply_text("No recent recordings found.")
                return

            # Send file list
            response = "Recent recordings:\n" + "\n".join(recent_files)
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error listing recordings: {e}")
            await update.message.reply_text("An error occurred while listing recordings.")

    async def admin_remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a user from the registered users list (admin-only)"""
        # Check if the user is the admin
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("You are not authorized to use this command.")
            return

        # Check if a username was provided
        if not context.args:
            await update.message.reply_text("Please provide a user ID to remove.")
            return

        user_to_remove = context.args[0]
        if user_to_remove in self.registered_users:
            removed_user = self.registered_users.pop(user_to_remove)
            UserRegistryManager.save_registered_users(self.registered_users)
            await update.message.reply_text(
                f"User {removed_user['username']} has been removed from registered users."
            )
        else:
            await update.message.reply_text("User not found in the registered users list.")

    def send_motion_file(self, file_path, queue):
        """Send motion detection file to registered users"""
        from telegram.ext import ApplicationBuilder
        import asyncio

        async def send_files():
            try:
                application = ApplicationBuilder().token(self.token).build()
                
                for user_id, user_info in self.registered_users.items():
                    try:
                        with open(file_path, 'rb') as video:
                            await application.bot.send_video(
                                chat_id=user_id, 
                                video=video, 
                                caption=f"Motion detected: {os.path.basename(file_path)}"
                            )
                        logger.info(f"Sent {file_path} to user {user_info['username']}")
                    except Exception as e:
                        logger.error(f"Error sending file to {user_id}: {e}")
                
                # Signal completion
                queue.put(True)
            except Exception as e:
                logger.error(f"Critical error in send_files: {e}")
                queue.put(False)

        asyncio.run(send_files())

class MotionFileHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, bot_handler, queue):
        self.bot_handler = bot_handler
        self.queue = queue

    def on_created(self, event):
        """Called when a new file is created"""
        if not event.is_directory and event.src_path.endswith('.mp4'):
            logger.info(f"New motion detection file: {event.src_path}")
            
            # Create a separate process to send the file
            process = multiprocessing.Process(
                target=self.bot_handler.send_motion_file, 
                args=(event.src_path, self.queue)
            )
            process.start()

def run_file_watcher(bot_handler, queue):
    """Run the file system watcher"""
    event_handler = MotionFileHandler(bot_handler, queue)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, RECORDINGS_PATH, recursive=False)
    
    try:
        observer.start()
        logger.info("Motion detection file watcher started.")
        
        # Keep the process alive
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"File watcher error: {e}")
    finally:
        observer.stop()
        observer.join()

def main():
    # Create a queue for inter-process communication
    queue = multiprocessing.Queue()

    # Create bot handler
    bot_handler = TelegramBotHandler(BOT_TOKEN, RECORDINGS_PATH)

    # Create processes for bot and file watcher
    bot_process = multiprocessing.Process(target=bot_handler.start_bot)
    watcher_process = multiprocessing.Process(
        target=run_file_watcher, 
        args=(bot_handler, queue)
    )

    try:
        # Start both processes
        bot_process.start()
        watcher_process.start()

        # Wait for both processes
        bot_process.join()
        watcher_process.join()

    except KeyboardInterrupt:
        logger.info("Stopping processes...")
    finally:
        # Terminate processes if they are still running
        bot_process.terminate()
        watcher_process.terminate()

if __name__ == '__main__':
    main()