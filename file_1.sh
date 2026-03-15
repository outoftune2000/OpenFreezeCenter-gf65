#!/bin/bash

CONF="/etc/modprobe.d/ec_sys.conf"

echo "Enabling EC write support..."

sudo mkdir -p /etc/modprobe.d

if grep -q "^options ec_sys write_support=1$" "$CONF" 2>/dev/null; then
    echo "EC write support already enabled."
else
    echo "options ec_sys write_support=1" | sudo tee -a "$CONF" > /dev/null
    echo "EC write support enabled."
fi
