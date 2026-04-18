# Firmware C++ Style Guide

## Language & standard
- C++23, Arduino/ESP32 target
- All firmware code lives in `firmware/`

## Naming
- Expressive, unabbreviated variable names — no single-letter or shortened names
- Module-level state variables prefixed with `_` (e.g. `_credentials_json`)

## Types
- Use `#include <cstdint>` and prefer `int32_t`, `uint8_t` etc. over raw `int`, `byte`
- No C-style casts — use `static_cast<T>` exclusively
- Use `auto` / `const auto` wherever the type is clear from context

## Const correctness
- Mark every variable `const` that is not mutated
- Prefer `const auto` over `auto` unless reassignment is needed

## Control flow
- All `if` / `else` blocks must use curly braces, no exceptions
- Prefer `!expr` over `expr == false`
- Prefer `str.isEmpty()` over `str.length() > 0` / `str == ""`

## Encapsulation
- File-local symbols go in an anonymous `namespace { }` — never `static`
- Compile-time constants use `constexpr`, never `#define`

## Formatting
- Formatted by clang-format using `_clang-format` at the repo root
- Run `clang-format -i` on all changed `.cpp` / `.h` / `.ino` files before committing
