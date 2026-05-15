#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include <ESP32Servo.h>

#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

#define WIFI_SSID "Alu"
#define WIFI_PASSWORD "12344321"

//FIREBASE
#define API_KEY "enter firebase api kye"
#define DATABASE_URL "https://realtime-143c9-default-rtdb.firebaseio.com/"


FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

Servo servo;


bool signupOK = false;
bool lastState = false;

//SETUP
void setup() {

  Serial.begin(115200);

  servo.attach(13);
  servo.write(0);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }

  Serial.println("\nWiFi Connected");

  // Firebase config
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  if (Firebase.signUp(&config, &auth, "", "")) {

    Serial.println("Firebase SignUp OK");
    signupOK = true;

  } else {

    Serial.println("SignUp Failed");
    Serial.println(config.signer.signupError.message.c_str());
  }

  config.token_status_callback = tokenStatusCallback;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}


void loop() {

  if (!Firebase.ready() || !signupOK) return;

  if (Firebase.RTDB.getBool(&fbdo, "/DoorSystem/status")) {

    bool state = fbdo.boolData();

    Serial.print("Door: ");
    Serial.println(state);

    // trigger only once
    if (state == true && lastState == false) {

      Serial.println("OPENING DOOR");

      servo.write(90);
      delay(3000);
      servo.write(0);

      Serial.println("CLOSING DOOR");

      Firebase.RTDB.setBool(&fbdo, "/DoorSystem/status", false);
    }

    lastState = state;

  } else {

    Serial.println("Firebase Error:");
    Serial.println(fbdo.errorReason());
  }

  delay(500);
}