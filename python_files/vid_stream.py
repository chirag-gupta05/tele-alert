import cv2
import datetime as dt
import os
import time
import shutil
from dotenv import load_dotenv

# Load environment variables from.env file
load_dotenv()
stream_url = os.getenv("stream_id")

# Define the folder path where recordings will be saved
folder_path = "C:/Recordings_test"
desfolder_path = "C:/Recordings"

# Ensure the folder exists; create it if it doesn't
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Open the video stream
cap = cv2.VideoCapture(stream_url)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
last_motion_time = 0.0
buffer_time = 5.0

if not cap.isOpened():
    print("Error: Could not open video stream")
    exit()

prev_frame=None
motion_detected = False
recording = None

def desgen_filename():
    f_name = "/motion_" + dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + ".mp4"
    return desfolder_path+f_name

def gen_filename():
    f_name = "/motion_" + dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + ".mp4"
    return folder_path+f_name

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
FF = ''
# Display the video stream frame by frame
while True:
    ret, frame = cap.read()
    #display_frame=frame.copy()

    if not ret:
        break

    # Display the frame in a window
    # cv2.imshow('ESP32-CAM Stream', frame)

    # Convert to grayscale for easier processing
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to smooth the frame
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # If there is a previous frame, compare it with the current frame
    if prev_frame is not None:
        # Compute absolute difference between current and previous frame
        frame_diff = cv2.absdiff(prev_frame, gray)

        # Apply thresholding to detect changes
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)

        # Find contours in the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw bounding boxes around detected motion areas
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > 1000:  # Adjust size threshold as needed
                (x, y, w, h) = cv2.boundingRect(contour)
                #cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                motion_detected=True;
                #cv2.putText(display_frame, "Motion Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 1)

        if motion_detected:
            last_motion_time = time.time()
            if recording is None or not recording.isOpened():
                filename = gen_filename()
                FF = filename
                recording = cv2.VideoWriter(filename, fourcc, 20.0, (frame_width, frame_height))
                print (f"Recording started: {filename}")
            
            recording.write(frame)

        elif not motion_detected and time.time() - last_motion_time > buffer_time:
            if recording is not None and recording.isOpened():
                print(f"Recording stopped. File saved to: {filename}")
                recording.release()
                des = desgen_filename()

                r = shutil.copy(FF, des)
                print(r)
                recording = None  # Reset recording
        
        # cv2.imshow("Detection", display_frame)

    # Update the previous frame for the next loop
    prev_frame = gray

    # Exit the stream display when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video stream and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()