#!/bin/bash

set -e

OFC_DIR="$HOME/Desktop/OFC"
SRC_DIR="$HOME/Downloads/OpenFreezeCenter-main"

echo "Installing required packages..."
sudo pacman -Syu --needed python python-virtualenv python-gobject python-cairo

echo "Creating application directory..."
mkdir -p "$OFC_DIR"

echo "Creating virtual environment..."
if [ ! -d "$OFC_DIR/bin" ]; then
    python -m venv "$OFC_DIR"
fi

echo "Copying project files..."
cp -f "$SRC_DIR/install.sh" "$OFC_DIR/"
cp -f "$SRC_DIR/file_1.sh" "$OFC_DIR/"
cp -f "$SRC_DIR/file_2.sh" "$OFC_DIR/"
cp -f "$SRC_DIR/OFC.py" "$OFC_DIR/"
cp -f "$SRC_DIR/README.md" "$OFC_DIR/"
cp -f "$SRC_DIR/LICENSE" "$OFC_DIR/"

if [ -f "$SRC_DIR/config.py" ]; then
    cp -f "$SRC_DIR/config.py" "$OFC_DIR/"
fi

chmod +x "$OFC_DIR/file_1.sh" "$OFC_DIR/file_2.sh"

echo "Preparing EC read/write..."
"$OFC_DIR/file_1.sh"
"$OFC_DIR/file_2.sh"

echo "Loading ec_sys now..."
sudo modprobe ec_sys write_support=1 || true

echo "Running Open Freeze Center..."
sudo "$OFC_DIR/bin/python" "$OFC_DIR/OFC.py"
