#!/bin/bash

CONF="/etc/modules-load.d/ec_sys.conf"

echo "Enabling ec_sys module load at boot..."

sudo mkdir -p /etc/modules-load.d

if grep -q "^ec_sys$" "$CONF" 2>/dev/null; then
    echo "ec_sys already configured."
else
    echo "ec_sys" | sudo tee -a "$CONF" > /dev/null
    echo "ec_sys added."
fi
