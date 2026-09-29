#include <Arduino.h>


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("Starting ...");
}

void loop() {
  // put your main code here, to run repeatedly:
  int data = analogRead(32);
  float volt = map(data, 0, 4095, 0, 3300)/1000.0;
  Serial.println(volt);
  delay(100);
}
