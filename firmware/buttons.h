#pragma once
#include <array>

enum BUTTON_ID
{
   BUTTON_BLUE = 0,
   BUTTON_RED = 1,
   BUTTON_YELLOW = 2,
   BUTTON_GREEN = 3,
};

void buttons_setup();

// Returns an array where true means that button was just pressed this loop iteration
std::array<bool, 4> buttons_loop();
