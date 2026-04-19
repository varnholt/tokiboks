#include "buttons.h"
#include <Arduino.h>
#include <array>
#include <cstdint>

namespace
{

constexpr uint8_t BUTTON_BLUE_GPIO_ID = 4;
constexpr uint8_t BUTTON_YELLOW_GPIO_ID = 2;
constexpr uint8_t BUTTON_RED_GPIO_ID = 16;
constexpr uint8_t BUTTON_GREEN_GPIO_ID = 22;

std::array<bool, 4> _button_states{false, false, false, false};

std::array<bool, 4> read_states()
{
   return {
      digitalRead(BUTTON_BLUE_GPIO_ID) == LOW,
      digitalRead(BUTTON_RED_GPIO_ID) == LOW,
      digitalRead(BUTTON_YELLOW_GPIO_ID) == LOW,
      digitalRead(BUTTON_GREEN_GPIO_ID) == LOW,
   };
}

}  // namespace

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
   auto new_states = read_states();
   auto just_pressed = std::array<bool, 4>{};

   for (int32_t i = 0; i < static_cast<int32_t>(new_states.size()); ++i)
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
