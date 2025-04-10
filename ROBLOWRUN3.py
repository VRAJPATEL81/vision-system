import serial
import time
import cv2
import json
from roboflow import Roboflow

#Step 1: Receive Image from Arduino 
ser = serial.Serial('COM8', 115200, timeout=10)
file_path = "captured_image.jpg"

print("Waiting for image from Arduino...")
while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if "START_IMAGE" in line:
        print("Start marker received. Receiving image...")
        break

with open(file_path, "wb") as file:
    while True:
        chunk = ser.read(128)
        if b"END_IMAGE" in chunk:
            chunk = chunk.split(b"END_IMAGE")[0]  # Remove END_IMAGE from data
            file.write(chunk) 
            print("End marker received. Image saved.")
            break
        file.write(chunk)

ser.close()
print(f"Image saved successfully as {file_path}")

#Step 2: Run Roboflow Model Prediction
rf = Roboflow(api_key="VK9dNheJEhVc82ujhDKY")
project = rf.workspace("dent-detection-tsf5p").project("dent_detection-u6d2r")
model = project.version(3).model

result = model.predict(file_path, confidence=40)
result.save("result.jpeg")

image = cv2.imread(file_path)
if image is None:
    raise FileNotFoundError(f"Error: Image {file_path} not found!")

image_height, image_width, _ = image.shape
print(f"Image Resolution: {image_width}x{image_height} px")

result_json = result.json()

metal_width_mm = None
metal_height_mm = None
defect_coordinates = []

for prediction in result_json["predictions"]:
    label = prediction.get("class")
    if label == "Sheet":
        metal_width_mm = float(prediction.get("width", 0))
        metal_height_mm = float(prediction.get("height", 0))
    elif label == "defect":
        x_pixel = float(prediction.get("x", 0))
        y_pixel = float(prediction.get("y", 0))
        defect_coordinates.append((x_pixel, y_pixel))

if metal_width_mm is None or metal_height_mm is None:
    raise ValueError("Error: Metal sheet size not found in predictions.")

print(f"Metal Sheet Size: {metal_width_mm}x{metal_height_mm} mm")

mm_per_pixel_x = metal_width_mm / image_width
mm_per_pixel_y = metal_height_mm / image_height
print(f"Scaling Factors - X: {mm_per_pixel_x:.4f} mm/px, Y: {mm_per_pixel_y:.4f} mm/px")

print("Raw Defect Coordinates (px):", defect_coordinates)

converted_defects = []
for x_pixel, y_pixel in defect_coordinates:
    x_real = round(x_pixel * mm_per_pixel_x, 2)
    y_real = round(y_pixel * mm_per_pixel_y, 2)
    converted_defects.append((x_real, y_real))

print("Converted Defect Coordinates (mm):", converted_defects)

#Step 3: Send Converted Coordinates to Arduino
arduino = serial.Serial("COM8", 115200, timeout=1)
time.sleep(2)  # Let Arduino reset

for x_real, y_real in converted_defects:
    data = f"{x_real},{y_real}\n"
    arduino.write(data.encode())
    print(f"Sent to Arduino: {data}")
    time.sleep(1)  # Delay between sends

arduino.close()
print("All defect coordinates sent to Arduino.")
