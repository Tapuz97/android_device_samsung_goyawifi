#!/bin/bash
set -euo pipefail
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
mkdir -p "$project/evidence/offline-v23"
g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -g \
    "$project/scripts/test_t110_window_slots.cpp" -o /tmp/t110-window-slots-test
/tmp/t110-window-slots-test | tee "$project/evidence/offline-v23/window-ownership-test.log"
