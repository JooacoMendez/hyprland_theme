#!/bin/bash

hyprctl dispatch submap rofi

rofi -show drun -theme ~/.config/rofi/launcher.rasi

hyprctl dispatch submap reset
