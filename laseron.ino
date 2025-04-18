#include <Wire.h> 
#include <ArduCAM.h>
#include <SPI.h>
#include "memorysaver.h"

#define CS 7
#define BUF_SIZE 128
#define LASER_PIN 9

ArduCAM myCAM(OV2640, CS);
uint8_t buffer[BUF_SIZE];

void setup() {
    Serial.begin(115200);
    Wire.begin();
    SPI.begin();

    pinMode(CS, OUTPUT);
    digitalWrite(CS, HIGH);
    pinMode(LASER_PIN, OUTPUT);
    digitalWrite(LASER_PIN, LOW);

    delay(1000);
    Serial.println("ArduCAM + KY-008 Laser Setup Ready");

    // Initialize ArduCAM
    myCAM.write_reg(0x07, 0x80); delay(100);
    myCAM.write_reg(0x07, 0x00); delay(100);
    myCAM.set_format(JPEG);
    myCAM.InitCAM();
    myCAM.OV2640_set_JPEG_size(OV2640_1600x1200);
    delay(1000);
}

void loop() {
    // Step 1: Capture and send image
    Serial.println("Capturing Image...");
    myCAM.flush_fifo();
    myCAM.clear_fifo_flag();
    myCAM.start_capture();

    while (!myCAM.get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK));
    Serial.println("Capture Done!");

    uint32_t length = myCAM.read_fifo_length();
    Serial.println("Image Size: " + String(length));

    if (length >= 262143 || length == 0) {
        Serial.println("ERROR: Invalid image size!");
        return;
    }

    Serial.println("START_IMAGE");  
    myCAM.CS_LOW();

    while (length > 0) {
        uint8_t toRead = (length < BUF_SIZE) ? length : BUF_SIZE;
        myCAM.CS_LOW();
        for (uint32_t i = 0; i < toRead; i++) {
            buffer[i] = myCAM.read_fifo();
        }
        myCAM.CS_HIGH();
        Serial.write(buffer, toRead);
        length -= toRead;
        delay(5);  // Prevents buffer overflow
    }

    myCAM.CS_HIGH();
    Serial.println("END_IMAGE"); 
    Serial.flush();

    // Step 2: Wait for coordinates from Python and trigger laser
    Serial.println("Waiting for defect coordinates...");
    String data = "";
    unsigned long startTime = millis();
    while ((millis() - startTime) < 10000) {  // 10 second timeout
        if (Serial.available()) {
            data = Serial.readStringUntil('\n');
            break;
        }
    }

    if (data.length() > 0) {
        int commaIndex = data.indexOf(',');
        if (commaIndex != -1) {
            float X = data.substring(0, commaIndex).toFloat();
            float Y = data.substring(commaIndex + 1).toFloat();

            Serial.print("Received Defect at: X = ");
            Serial.print(X);
            Serial.print(" mm, Y = ");
            Serial.println(Y);

            // Trigger laser
            digitalWrite(LASER_PIN, HIGH);
            delay(2000);
            digitalWrite(LASER_PIN, LOW);
        }
    } else {
        Serial.println("No defect coordinates received.");
    }

    delay(2000);  // Wait before next capture cycle
}
