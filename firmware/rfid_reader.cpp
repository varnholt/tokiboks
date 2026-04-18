#include "rfid_reader.h"
#include <Arduino.h>
#include <MFRC522.h>
#include <SPI.h>
#include <cstdint>

namespace
{

constexpr uint8_t SS_PIN = 15;
constexpr uint8_t RST_PIN = 27;

MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::Uid _last_uid;

String build_uid_string()
{
   String uid_string;

   for (uint8_t index = 0; index < rfid.uid.size; ++index)
   {
      if (rfid.uid.uidByte[index] < 0x10)
      {
         uid_string += "0";
      }

      uid_string += String(rfid.uid.uidByte[index], HEX);
   }

   uid_string.toUpperCase();
   return uid_string;
}

}  // namespace

void rfid_setup()
{
   // sck, miso, mosi, ss
   SPI.begin(14, 26, 13, SS_PIN);

   rfid.PCD_Init();
   rfid.PCD_DumpVersionToSerial();

   _last_uid.size = 0;
}

String rfid_loop()
{
   if (!rfid.PICC_IsNewCardPresent())
   {
      _last_uid.size = 0;
      return "";
   }

   if (!rfid.PICC_ReadCardSerial())
   {
      return "";
   }

   if (_last_uid.size == rfid.uid.size && memcmp(_last_uid.uidByte, rfid.uid.uidByte, rfid.uid.size) == 0)
   {
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
      return "";
   }

   _last_uid = rfid.uid;

   const auto uid_string = build_uid_string();

   Serial.print("UID: ");
   Serial.println(uid_string);

   rfid.PICC_HaltA();
   rfid.PCD_StopCrypto1();

   return uid_string;
}
