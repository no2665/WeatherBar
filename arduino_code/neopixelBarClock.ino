#include <Wire.h>
#include "RTClib.h"
#include <Adafruit_NeoPixel.h>
#include "pixelStruct.h"

#define LEDPIN 6
#define BTN1 8
#define BTN2 7

#define LDR A3

Adafruit_NeoPixel clock = Adafruit_NeoPixel(24, LEDPIN, NEO_RGB + NEO_KHZ800);

RTC_DS1307 RTC;

Pixel pixels[24];

int prevWeatherBrightness = 32;
int prevTimeBrightness = 255;

boolean btn1Pressed = false;
int btn1Counter = 0;
int delaySecs = 250;
int btnTimeTrig = 2000/delaySecs;
int lightDiff = 4;

long startOfBrightnessChange = 0;
boolean hasGotBrighter = false;
boolean hasGotDimmer = false;
long secsTillBrighter = 15; // 15 seconds
long secsTillDim = 15; // 15 seconds

Pixel normaliseColour(Pixel p);

void setup(){
  pinMode(BTN1, INPUT);
  pinMode(BTN2, INPUT);
  pinMode(LDR, INPUT);
  pinMode(LEDPIN, OUTPUT);
  Serial.begin(9600);
  clock.begin();
  clock.setBrightness(255);
  clock.show();
  
  Wire.begin();
  RTC.begin();
  
  if(!RTC.isrunning()){
    // following line sets the RTC to the date & time this sketch was compiled
    RTC.adjust(DateTime(__DATE__, __TIME__));
  }
  
  Pixel off = {0, 0, 0};
  for(int i = 0; i < 24; i++){
    pixels[i] = off;
  }
  
}

void loop(){
  if(button1Pressed()){
    if(btn1Pressed){
      if(++btn1Counter >= btnTimeTrig){
        // Enter edit time mode
        editTime();
        btn1Counter = 0;
      }
    } else {
      btn1Pressed = true;
    }
  } else {
    btn1Pressed = false;
    btn1Counter = 0;
  }
  
  int lightLevel = analogRead(LDR);
  // 0-10 All lights off at night
  // 60-70 TVs on at night
  // 330-360 Light on at night
  int lightMap = map(lightLevel, 0, 1023, 0, 100);
  
  int weatherBrightness = 0;
  int timeBrightness = 0;
  /*if(lightMap < 3){
    weatherBrightness = 0;
    timeBrightness = 0;
  } else if(lightMap < 7){
    weatherBrightness = 0;
    timeBrightness = 6;
  } else */if(lightMap < 29){
    // Half Bright
    weatherBrightness = 16;
    timeBrightness = 128;
  /*} else if(lightMap < 40){
    weatherBrightness = 24;
    timeBrightness = 255;*/
  } else {
    // Brightest
     weatherBrightness = 32;
     timeBrightness = 255;
  }
  
  if(weatherBrightness > prevWeatherBrightness 
    || timeBrightness > prevTimeBrightness){
    if(hasGotBrighter){
      long uNow = RTC.now().unixtime();
      if(uNow - startOfBrightnessChange >= secsTillBrighter){
        if(weatherBrightness > prevWeatherBrightness + lightDiff){
          weatherBrightness = prevWeatherBrightness + lightDiff;
        }
        if(timeBrightness > prevTimeBrightness + lightDiff){
          timeBrightness = prevTimeBrightness + lightDiff;
        }
        prevTimeBrightness = timeBrightness;
        prevWeatherBrightness = weatherBrightness;
      } else {
        weatherBrightness = prevWeatherBrightness;
        timeBrightness = prevTimeBrightness; 
      }
    } else {
      hasGotBrighter = true;
      hasGotDimmer = false;
      startOfBrightnessChange = RTC.now().unixtime();
      weatherBrightness = prevWeatherBrightness;
      timeBrightness = prevTimeBrightness; 
    }
  } else if(weatherBrightness < prevWeatherBrightness
    || timeBrightness < prevTimeBrightness){
    if(hasGotDimmer){
      long uNow = RTC.now().unixtime();
      if(uNow - startOfBrightnessChange >= secsTillDim){
        if(weatherBrightness < prevWeatherBrightness - lightDiff){
          weatherBrightness = prevWeatherBrightness - lightDiff;
        }
        if(timeBrightness < prevTimeBrightness - lightDiff){
          timeBrightness = prevTimeBrightness - lightDiff;    
        }
        prevTimeBrightness = timeBrightness;
        prevWeatherBrightness = weatherBrightness;
      } else {
        weatherBrightness = prevWeatherBrightness;
        timeBrightness = prevTimeBrightness; 
      }
    } else {
      hasGotDimmer = true;
      hasGotBrighter = false;
      startOfBrightnessChange = RTC.now().unixtime();
      weatherBrightness = prevWeatherBrightness;
      timeBrightness = prevTimeBrightness;  
    }
  } else if(weatherBrightness == prevWeatherBrightness){
    if(timeBrightness > prevTimeBrightness + lightDiff){
      timeBrightness = prevTimeBrightness + lightDiff;
    } else if(timeBrightness < prevTimeBrightness - lightDiff){
      timeBrightness = prevTimeBrightness - lightDiff;    
    }
    prevTimeBrightness = timeBrightness;
    hasGotDimmer = false;
    hasGotBrighter = false;
  }
  
  if(button2Pressed()){
    weatherBrightness = 32;
    timeBrightness = 255;
  }
  
  for(int i = 0; i < 24; i++){
    Pixel p = normaliseColour(pixels[i]);
    uint32_t colour = clock.Color((((long)p.red)*weatherBrightness)/255L,
      (((long)p.green)*weatherBrightness)/255L,
      (((long)p.blue)*weatherBrightness)/255L);
    clock.setPixelColor(i, colour);
  }
  
  DateTime now = RTC.now();
  int mins = now.minute();
  int hours = now.hour();
  
  long ledFade1 = map(mins, 0, 60, timeBrightness, weatherBrightness);
  long ledFade2 = map(mins, 0, 60, weatherBrightness, timeBrightness);
  
  Pixel colour1 = normaliseColour(pixels[hours]);
  if(colour1.red == 0 && colour1.green == 0 && colour1.blue == 0){
    Pixel i = {255, 255, 255};
    colour1 = i;
  }
  int nextHour = 0;
  if(hours != 23){
    nextHour = hours + 1;
  }
  Pixel colour2 = normaliseColour(pixels[nextHour]);
  if(colour2.red == 0 && colour2.green == 0 && colour2.blue == 0){
    Pixel i = {255, 255, 255};
    colour2 = i;
  }
  
  long c1R = (((long)colour1.red)*ledFade1)/255L;
  long c1G = (((long)colour1.green)*ledFade1)/255L;
  long c1B = (((long)colour1.blue)*ledFade1)/255L;
  uint32_t ledColour1 = clock.Color(c1R, c1G, c1B);
  
  long c2R = (((long)colour2.red)*ledFade2)/255L;
  long c2G = (((long)colour2.green)*ledFade2)/255L;
  long c2B = (((long)colour2.blue)*ledFade2)/255L;
  uint32_t ledColour2 = clock.Color(c2R, c2G, c2B);

  clock.setPixelColor(hours, ledColour1);
  if(hours == 23){
    clock.setPixelColor(0, ledColour2);
  } else {
    clock.setPixelColor(hours + 1, ledColour2);
  }
  
  checkSerialData();
  
  clock.show();
  delay(delaySecs);
}

void checkSerialData(){
  String y = "";
  while(Serial.available()){
    delay(3);
    char c = Serial.read();
    y += c;
  } 
  if(y != ""){
    String codeStr;
    char* rest;
    for(int i = 0; i < y.length() && y[i] != ','; i++){
      codeStr += y[i];
      rest = &(y[i+2]);
    }
    int num = 0;
    int code = codeStr.toInt();
    switch(code){
      case 0: num = code0(rest); 
              Serial.print("0,");
              Serial.print(num);
              Serial.print(",");
              Serial.print(pixels[num].red);
              Serial.print(",");
              Serial.print(pixels[num].green);
              Serial.print(",");
              Serial.println(pixels[num].blue);
              break;
      case 1: code1(rest);
              Serial.print("1,");
              Serial.print(pixels[1].red);
              Serial.print(",");
              Serial.print(pixels[1].green);
              Serial.print(",");
              Serial.println(pixels[1].blue);
              break;
      case 2: code2(); 
              Serial.println("2");
              break;
    }
  }
}

//Change the colour of an individual pixel
int code0(String data){
  String pixelNum;
  String rest;
  for(int i = 0; i < data.length() && data[i] != ','; i++){
    pixelNum += data[i];
    rest = &(data[i+2]);
  }
  
  int* a = getColourFromString(rest);

  int pNum = pixelNum.toInt();

  Pixel p = {a[0], a[1], a[2]};
  if(pNum < 24 && pNum >= 0){ 
    pixels[pNum] = p;
    return pNum;
  } else {
    return 25;
  }
}

// Change all pixels to the colour stored in data
void code1(String data){
  int* a = getColourFromString(data);
  Pixel p = {a[0], a[1], a[2]};
  for(int i = 0; i < 24; i++){
    pixels[i] = p;
  } 
}

void code2(){
  for(int i = 0; i < 24; i++){
    Serial.print(i);Serial.print(":");
    Serial.print(pixels[i].red);Serial.print(",");
    Serial.print(pixels[i].green);Serial.print(",");
    Serial.println(pixels[i].blue);
    delay(10);
  } 
}

int* getColourFromString(String data){
  String red;
  String rest;
  for(int i = 0; i < data.length() && data[i] != ','; i++){
    red += data[i];
    rest = &(data[i+2]);
  }
  
  String green;
  String restTmp = rest;
  for(int i = 0; i < restTmp.length() && restTmp[i] != ','; i++){
    green += restTmp[i];
    rest = &(restTmp[i+2]);
  }
  
  String blue;
  restTmp = rest;
  for(int i = 0; i < restTmp.length() && restTmp[i] != ','; i++){
    blue += restTmp[i];
  }
  int r = red.toInt();
  int g = green.toInt();
  int b = blue.toInt();
  if(r > 255) r = 255;
  if(b > 255) b = 255;
  if(g > 255) g = 255;
  if(r < 0) r = 0;
  if(b < 0) b = 0;
  if(g < 0) g = 0;
  int a[] = {r, g, b};
  return a;
}

Pixel normaliseColour(Pixel p){
  if(p.red == 255 || p.green == 255 || p.blue == 255){
    return p;
  }
  Pixel i = {0, 0, 0};
  if(p.red > p.green && p.red >= p.blue){
    i.red = 255;
    i.green = (int) (((float) p.green / (float) p.red) * 255.f);
    i.blue = (int) (((float) p.blue / (float) p.red) * 255.f);
  } else if(p.green >= p.red && p.green > p.blue){
    i.green = 255;
    i.red = (int) (((float) p.red / (float) p.green) * 255.f);
    i.blue = (int) (((float) p.blue / (float) p.green) * 255.f);
  } else if(p.blue > p.red && p.blue >= p.green){
    i.blue = 255;
    i.green = (int) (((float) p.green / (float) p.blue) * 255.f);
    i.red = (int) (((float) p.red / (float) p.blue) * 255.f);
  } else if(p.red == p.green && p.green == p.blue && p.red != 0){
    i.red = 255;
    i.blue = 255;
    i.green = 255;
  }
  return i;
}

boolean button1Pressed(){
  if(digitalRead(BTN1) == HIGH) return true;
  return false;
}

boolean button2Pressed(){
  if(digitalRead(BTN2) == HIGH) return true;
  return false;
}

void editTime(){
  flashLEDs();
  int counter = 0;
  int hours = 0;
  clock.setPixelColor(hours, 255, 255, 255);
  clock.show();
  while(!(button1Pressed() & button2Pressed())){
    if(button1Pressed()){
      clock.setPixelColor(hours, 0, 0, 0);
      if(--hours < 0) hours = 23;
      clock.setPixelColor(hours, 255, 255, 255);
      clock.show();
    } 
    if(button2Pressed()){
      clock.setPixelColor(hours, 0, 0, 0);
      if(++hours > 23) hours = 0;
      clock.setPixelColor(hours, 255, 255, 255);
      clock.show();
    }
    delay(200);
  }
  flashLEDs();
  int minutes = 0;
  while(!(button1Pressed() & button2Pressed())){
    if(button1Pressed()){
      if(--minutes < 0) minutes = 59;
    }
    if(button2Pressed()){
      if(++minutes > 59) minutes = 0;
    }
    for(int i = 0; i < 24; i++){
      switch(minutes/24){
        case 0:
          if(i < minutes) clock.setPixelColor(i, 255, 255, 255);
          else clock.setPixelColor(i, 0, 0, 0);
          break;
        case 1:
          if(i < minutes - 24) clock.setPixelColor(i, 255, 0, 0);
          else clock.setPixelColor(i, 255, 255, 255);
          break;
        case 2:
          if(i < minutes - 48) clock.setPixelColor(i, 0, 255, 0);
          else clock.setPixelColor(i, 255, 0, 0);
      }
    }
    clock.show();
    delay(200);
  }
  flashLEDs();
  RTC.adjust(DateTime(2014, 11, 5, hours, minutes, 0));
}

void flashLEDs(){
  int d = 1000/24;
  for(int i = 0; i < 24; i++){
    clock.setPixelColor(i, 0, 0, 0);
  }
  clock.show();
  delay(d);
  for(int i = 0; i < 24; i++){
    clock.setPixelColor(i, 255, 255, 255);
    clock.show();
    delay(d);
  }
  for(int i = 0; i < 24; i++){
    clock.setPixelColor(i, 0, 0, 0);
    clock.show();
    delay(d);
  }
}

