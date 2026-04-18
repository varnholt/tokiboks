#include "buttons.h"
#include <Arduino.h>
#include <array>

#define BUTTON_BLUE_GPIO_ID 4
#define BUTTON_YELLOW_GPIO_ID 2
#define BUTTON_RED_GPIO_ID 16
#define BUTTON_GREEN_GPIO_ID 22

static std::array<bool, 4> _button_states{false, false, false, false};

static std::array<bool, 4> read_states()
{
   return {
      digitalRead(BUTTON_BLUE_GPIO_ID) == LOW,
      digitalRead(BUTTON_RED_GPIO_ID) == LOW,
      digitalRead(BUTTON_YELLOW_GPIO_ID) == LOW,
      digitalRead(BUTTON_GREEN_GPIO_ID) == LOW,
   };
}

void buttons_setup()
{
   pinMode(BUTTON_BLUE_GPIO_ID, INPUT_PULLUP);
   pinMode(BUTTON_RED_GPIO_ID, INPUT_PULLUP);
   pinMode(BUTTON_YELLOW_GPIO_ID, INPUT_PULLUP);
   pinMode(BUTTON_GREEN_GPIO_ID, INPUT_PULLUP);

   _button_states = read_states();
}

std::array<bool, 4> buttons_loop()
{
   std::array<bool, 4> new_states = read_states();
   std::array<bool, 4> just_pressed = {false, false, false, false};

   for (int i = 0; i < 4; i++)
   {
      if (new_states[i] != _button_states[i])
      {
         Serial.print("button ");
         Serial.print(i);
         Serial.print(" changed to ");
         Serial.println(new_states[i] ? "pressed" : "released");

         if (new_states[i])
         {
            just_pressed[i] = true;
         }
      }
   }

   _button_states = new_states;
   return just_pressed;
}
