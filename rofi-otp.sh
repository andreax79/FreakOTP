#!/usr/bin/env bash
TOKEN=$(freakotp .ls | rofi -dmenu -p Token -i)
if [ -n "${TOKEN}" ]; then
    OTP=$(freakotp "${TOKEN}")
    echo -n "${OTP}" | xclip -selection clipboard
    rofi -e "${TOKEN}  <b>${OTP}</b>" -markup
fi
