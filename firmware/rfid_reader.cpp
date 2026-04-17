#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include "rfid_reader.h"

#define SS_PIN  15
#define RST_PIN 27

static MFRC522 rfid(SS_PIN, RST_PIN);
static MFRC522::Uid _last_uid;

static String build_uid_string()
{
    String uid_string;

    for (byte index = 0; index < rfid.uid.size; index++)
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
    if (rfid.PICC_IsNewCardPresent() == false)
    {
        _last_uid.size = 0;
        return "";
    }

    if (rfid.PICC_ReadCardSerial() == false)
    {
        return "";
    }

    if (_last_uid.size == rfid.uid.size &&
        memcmp(_last_uid.uidByte, rfid.uid.uidByte, rfid.uid.size) == 0)
    {
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
        return "";
    }

    _last_uid = rfid.uid;

    String uid_string = build_uid_string();

    Serial.print("UID: ");
    Serial.println(uid_string);

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();

    return uid_string;
}
