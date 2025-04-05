# ESP32-CAM Motion Detection with Telegram Alerts

This project uses the ESP32-CAM module to detect motion and send real-time video alerts to registered users via a Telegram bot. The system is integrated with Python for backend processing and leverages custom Arduino libraries.

---

## 📁 Project Structure

```
ESP32CAM_MOTION_DETECTION/
│
├── arduino_files/
│   ├── includes/        # Contains modified/custom Arduino libraries
│   └── motion_detection/
│       ├── esp32cam_code.ino    # Main Arduino sketch
│       ├── credentials.h            # Contains sensitive credentials (ignored in version control)
│       └── .gitignore
│
├── python_files/
|   ├── telegram_bot.py
|   ├── vid_stream.py
|   ├── registered_users.json	  # ignored in version control
|   ├── .env			  # ignored in version control
|   └── .gitignore
└── .gitignore

```

---

## 📦 Arduino Dependencies

> Ensure these libraries are available in the Arduino IDE:

- `esp_camera.h` (modified; placed in `includes`)
- `WiFi.h`
- `ESPAsyncWebSrv.h`
- `AsyncTCP.h`
- `camera_pins.h`

📌 **Note:** Some of the default ESP32-CAM libraries like `app_httpd.h` were modified. Please use the provided `includes` folder and do **not rely on official versions** to ensure compatibility.

---

## ⚙️ Required Python Packages

Install these before running the Python scripts:

```bash
pip install python-dotenv watchdog opencv-python python-telegram-bot
```

Other used standard libraries:
- `multiprocessing`
- `logging`
- `json`
- `shutil`
- `os`
- `datetime`

---

## 🔐 Credentials Handling

- Credentials (like `WIFI_SSID`, `WIFI_PASSWORD`, `BOT_TOKEN`, etc.) are stored in `credentials.h` and `.env`.
- `credentials.h` and other files is **gitignored** and should be created manually using the following template:

```cpp
// credentials.h
#pragma once
#define WIFI_SSID "your-ssid"
#define WIFI_PASSWORD "your-password"
```

---

## 🔧 Setup Instructions

1. **Arduino Side**
   - Open `esp32cam_code.ino` in Arduino IDE.
   - Select board: **ESP32CAM AI Thinker Module**
   - Flash the sketch to your ESP32-CAM.

2. **Python Side**
   - Place `.env` file in `python_files/` with:

     ```
     BOT_TOKEN=your-telegram-bot-token
     ADMIN_ID=your-admin-id
     ```

   - Run:

     ```bash
     python telegram_bot.py
     ```

---

## 📝 Notes

- Only **custom Arduino libraries** are tracked via Git to avoid exposing global/core libraries.
- .gitignore is configured to exclude credentials.h to avoid leaking credentials.
- Custom libraries are tracked if inside arduino_code/includes/.
- Developed and tested on Windows using VS Code and Arduino IDE.

---
