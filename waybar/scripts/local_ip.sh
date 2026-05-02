#!/usr/bin/env bash

ip route get 1.1.1.1 | grep -oP 'src \K[\d.]+'
