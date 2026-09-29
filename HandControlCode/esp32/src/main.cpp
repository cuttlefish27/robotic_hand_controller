#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>
#include <Wire.h>

// put function declarations here:
#define SDA 21
#define SCL 22

#define ServMin 150
#define ServMax 600



Adafruit_PWMServoDriver pca9685 = Adafruit_PWMServoDriver(0x40);

void setServo(uint8_t channel, int angle) {
  angle = constrain(angle,0,180);
  int pulse = map(angle, 0, 180, ServMin, ServMax);
  pca9685.setPWM(channel, 0, pulse);
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Wire.begin();

  pca9685.begin();
  pca9685.setPWMFreq(50);
  
}

void loop() {
  if(Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    int space1 = cmd.indexOf(' ');
    int space2 = cmd.indexOf(' ', space1 + 1);
    int space3 = cmd.indexOf(' ', space2 + 1);
    int space4 = cmd.indexOf(' ', space3 + 1);
    int space5 = cmd.indexOf(' ', space4 + 1);
    int space6 = cmd.indexOf(' ', space5 + 1);

  float theta0 = cmd.substring(0, space1).toFloat();
  float theta1 = cmd.substring(space1 + 1, space2).toFloat();
  float curl = cmd.substring(space2 + 1, space3).toFloat();
  float thumbRot = cmd.substring(space3 + 1, space4).toFloat();
  float thumbPinch = cmd.substring(space4 + 1, space5).toFloat();
  float theta2 = cmd.substring(space5 + 1, space6).toFloat();
  float theta3 = cmd.substring(space6).toFloat();


  
  


  

  setServo(0, theta0);
  setServo(1, theta1);
  setServo(2, curl);
  setServo(3, thumbRot);
  setServo(4, thumbPinch);
  setServo(5, theta2);
  setServo(6, theta3);

  }
}

// put function definitions here:
