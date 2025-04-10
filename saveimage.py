import serial

ser = serial.Serial('COM8', 115200, timeout=10)  

file_path = "captured_image.jpg"

while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if "START_IMAGE" in line:
        print("Start marker received. Receiving image...")
        break

with open(file_path, "wb") as file:
    while True:
        chunk = ser.read(128)  
        if b"END_IMAGE" in chunk:
            print("End marker received. Image saved.")
            break
        file.write(chunk)

ser.close()
print(f"Image saved successfully as {file_path}")
    