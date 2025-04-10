from roboflow import Roboflow
import cv2
import json
import serial
import time

rf = Roboflow(api_key="VK9dNheJEhVc82ujhDKY")
project = rf.workspace("dent-detection-tsf5p").project("dent_detection-u6d2r")
model = project.version(3).model

image_path = "D:/ATOMONE/YOLOv8_dataset/images/rms14.jpeg"

result = model.predict(image_path, confidence=40)
result.save("result.jpeg") 

image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"Error: Image {image_path} not found!")

image_height, image_width, _ = image.shape
print(f"Image Resolution: {image_width}x{image_height} px")

result_json = result.json()
#print("Full JSON Result:", json.dumps(result_json, indent=2))  

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

arduino = serial.Serial("COM8", 115200, timeout=1)
time.sleep(2) 

for x_real, y_real in converted_defects:
    data = f"{x_real},{y_real}\n"
    arduino.write(data.encode())  
    print(f"Sent to Arduino: {data}")
    time.sleep(1)  

arduino.close()