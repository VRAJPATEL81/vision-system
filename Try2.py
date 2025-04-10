import serial
import time
import cv2
import json

json_path = "D:/ATOMONE/YOLOv8_dataset/annotations/rms_34.json"
image_path = "D:/ATOMONE/YOLOv8_dataset/images/rms34.jpeg"

with open(json_path, "r") as file:
    metadata = json.load(file)

def get_metal_sheet_size():
    for item in metadata.get("boxes", []):  
        if item.get("label") == "Sheet":  
            if "width" in item and "height" in item:
                return float(item["width"]), float(item["height"])
    raise ValueError("Error: Metal sheet size not found in JSON.") 


def get_defect_coordinates():
    for item in metadata.get("boxes", []):
        if item.get("label") == "defect":  
            x_pixel = float(item["x"])                                 
            y_pixel = float(item["y"])
            defect = []
            defect.append((x_pixel, y_pixel))
    return defect


image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"Error: Image {image_path} not found!")

image_height, image_width, _ = image.shape  

metal_width_mm, metal_height_mm = get_metal_sheet_size()

mm_per_pixel_x = metal_width_mm / image_width
mm_per_pixel_y = metal_height_mm / image_height

print(f"Image Resolution: {image_width}x{image_height} px")
print(f"Metal Sheet Size: {metal_width_mm}x{metal_height_mm} mm")
print(f"Scaling Factors - X: {mm_per_pixel_x:.4f} mm/px, Y: {mm_per_pixel_y:.4f} mm/px")

defect_coordinates = get_defect_coordinates()
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
