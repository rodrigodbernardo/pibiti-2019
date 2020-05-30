//#include <I2Cdev.h>
#include <WebSocketClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ArduinoOTA.h>
#include <Wire.h>
#include <ArduinoJson.h>
#include "private_keys.h"
//#include "function.h"

#define num_capturas 2500
#define num_sensor 3

#define sda D6
#define scl D5

#define lPin D4

const uint8_t MPU_ADDR = 0x68;
const uint8_t WHO_AM_I = 0x75;
const uint8_t PWR_MGMT_1 = 0x6B;
const uint8_t GYRO_CONFIG = 0x1B;  //REGISTRADOR RESPONSAVEL POR CONFIGURAR A ESCALA DO GIROSCOPIO
const uint8_t ACCEL_CONFIG = 0x1C; //REGISTRADOR RESPONSAVEL POR CONFIGURAR A ESCALA DO ACELEROMETRO
const uint8_t ACCEL_XOUT = 0x3B;
const uint8_t GYRO_SCALE = 0b00000000;
const uint8_t ACCEL_SCALE = 0b00001000;

int16_t buff[7];

int16_t acel[num_capturas][num_sensor];
int16_t giro[num_capturas][num_sensor];
int16_t temp[num_capturas];

unsigned long timer = 0;
unsigned long prevMillis = 0;

String menu = "";
String output;
String captureStatus = "stop";
String numberOfSamples = "";

char *host;

boolean led_state = 0;

WiFiClient client;
ESP8266WiFiMulti wifiMulti;
WebSocketClient webSocketClient;
StaticJsonDocument<200> jsonData;

void setup() {
  Serial.begin(500000);
  Wire.begin(sda, scl);
  wifiStart();
  sensorStart();
  //otaStart();
  pinMode(lPin, OUTPUT);
}

void loop() {
  handshakeTest();
  
  for(int tentativa = 0; client.connected() && tentativa < 25 && menu == "";tentativa++){ //25 tentativas de conexao
    delay(1000);
    
    //Serial.println("\nServidor encontrado. Aguardando comandos.");
    Serial.printf("%d tentativas de 25.\n\n",tentativa+1);
    webSocketClient.getData(menu);

    if (menu == "1") {
      //webSocketClient.getData(output);  //Somente um olá do servidor

      //delay(5000);
      numberOfSamples = "";
      for (int tentativa = 0; client.connected() && numberOfSamples == "" && tentativa < 25;tentativa++) {
        webSocketClient.getData(numberOfSamples);
        Serial.printf("%d tentativas de 25.\n",tentativa+1);
        delay(1000);
      }

      if(numberOfSamples == "")
        break;

      //Serial.println("hey2");
      int _numberOfSamples = numberOfSamples.toInt();
      //webSocketClient.sendData("Pronto");

      delay(100);
      webSocketClient.getData(captureStatus);
      while (captureStatus == "continue") {
        Serial.println("\nCaptura iniciada.");
        timer = millis();                                                                     //Contador de tempo de captura
        for (int i = 0; i < _numberOfSamples; i++)                                                //LE O SENSOR E ARMAZENA SEUS DADOS EM acel[][], giro[][] E temp[][]
        {
          sensorRead();
          for (int j = 0; j < 3; j++)
          {
            acel[i][j] = buff[j];
            giro[i][j] = buff[j + 4];
          }
          temp[i] = buff[3];
        }
        timer = millis() - timer;

        webSocketClient.sendData((String)timer);
        //Serial.printf("Tempo de captura = %i ms\n", timer);
        Serial.println("Enviando dados. Aguarde...");

        delay(100);                                                                         //Delay para o servidor python nao se atrasar (nunca se sabe)
        sendSensorData(_numberOfSamples);
        delay(100);
        
        Serial.println("Envio Concluído");
        webSocketClient.sendData((String)timer);
        webSocketClient.getData(captureStatus);
      }
    }
    else if (menu == "2") {
      delay(2000);  // tempo para o servidor python se preparar para o envio de dados.
      sendLiveData();
    }
    else if (menu == "3")
      ESP.restart();
      
    menu = "";
  }
  //Serial.println("HEY");
}
void wifiStart() {
  wifiMulti.addAP("IFCE-LARI", passLari);
  wifiMulti.addAP("lapisco.ifce.edu.br", passLapisco);
  wifiMulti.addAP("AndroidAP", passRedmi);
  wifiMulti.addAP("FLAVIO_02", passCasa);

  WiFi.mode(WIFI_STA);
  
  while (wifiMulti.run() != WL_CONNECTED)
  {
    delay(100);
    Serial.print(".");
  }

  Serial.println("\n\nCONNECTED TO " + WiFi.SSID());
  Serial.print("IP ADRESS: ");
  Serial.println(WiFi.localIP());

  if (WiFi.SSID() == "IFCE-LARI")
    host = hostLari;
  else if (WiFi.SSID() == "lapisco.ifce.edu.br")
    host = hostLapisco;
  else if (WiFi.SSID() == "AndroidAP")
    host = hostRedmi;
  else if (WiFi.SSID() == "FLAVIO_02")
    host = hostCasa;
}
void sensorStart() {
  sensorWrite(PWR_MGMT_1, 0);             //ACORDA O SENSOR
  sensorWrite(GYRO_CONFIG, GYRO_SCALE);   //CONFIGURA A ESCALA DO GIROSCÓPIO - +-250 °/s
  sensorWrite(ACCEL_CONFIG, ACCEL_SCALE); //CONFIGURA A ESCALA DO ACELERÔMETRO - +-4G
}
/*
  void otaStart()
  {
  ArduinoOTA.setPassword(otaPass);
  ArduinoOTA.onStart([](){
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH){
      type = "sketch";
    }
    else{
      type = "filesystem";
    }
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("ERRO AO INICIAR OTA: %u",error);
  });
  ArduinoOTA.begin();
  }
*/
void sensorWrite(int reg, int val) {
  Wire.beginTransmission(MPU_ADDR); // inicia comunicação com endereço do MPU6050
  Wire.write(reg);                  // envia o registro com o qual se deseja trabalhar
  Wire.write(val);                  // escreve o valor no registro
  Wire.endTransmission();           // termina a transmissão
}
void sensorRead() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(ACCEL_XOUT);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, (uint8_t)14);

  for (int i = 0; i < 7; i++)
    buff[i] = Wire.read() << 8 | Wire.read();
  //delay(1);
  yield();
}
void sendLiveData() {
  while (client.connected())
  {
    output = "";
    sensorRead();

    jsonData["acx"] = buff[0];
    jsonData["acy"] = buff[1];
    jsonData["acz"] = buff[2];

    jsonData["temp"] = buff[3];

    jsonData["gyx"] = buff[4];
    jsonData["gyy"] = buff[5];
    jsonData["gyz"] = buff[6];

    serializeJson(jsonData, output);
    Serial.println(output);
    webSocketClient.sendData(output);

    delay(100);
  }
  handshakeTest();
}
void sendSensorData(int numberOfSamples) {
  timer = millis();
  for (int i = 0; i < numberOfSamples; i++)
  {
    //char label[7][4] = {"acx", "acy", "acz", "tem", "gyx", "gyy", "gyz"};
    output = "";
    for (int j = 0; j < 3; j++) {
      output += (String)acel[i][j];
      output += ",";
    }
    for (int j = 0; j < 3; j++) {
      output += (String)giro[i][j];
      output += ",";
    }
    output += (String)temp[i];

    webSocketClient.sendData(output);
  }
  timer = millis() - timer;
}
int handshakeTest() {
  led_state = !led_state;
  
  if (!client.connect(host, port_WS)){
    Serial.println("\nIncapaz de encontrar o servidor.");
    return 0;
  }
  
  webSocketClient.path = "/";
  webSocketClient.host = host;

  if (!webSocketClient.handshake(client)){
    return 0;
  }
  return 1;
}
