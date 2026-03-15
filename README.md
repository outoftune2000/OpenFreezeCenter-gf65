# OpenFreezeCenter (OFC)

OpenFreezeCenter is a Linux GUI utility for controlling MSI laptop fan behavior and battery charge threshold through EC (embedded controller) access.

If you do not want to run the GUI, try OpenFreezeCenter-Lite (CLI):
https://github.com/YoCodingMonster/OpenFreezeCenter-Lite

## Features
- Fan profile selection: `Auto`, `Basic`, `Advanced`, `Cooler Booster`
- CPU/GPU temperature monitoring (current/min/max)
- CPU/GPU fan RPM monitoring
- Battery charge threshold control (`50` to `100`)

## Important Notes
- This app writes EC values and needs root privileges.
- The scripts enable `ec_sys` write support (`write_support=1`).
- First install may require a reboot for stable EC read/write behavior.
- Incorrect EC values can be risky on unsupported hardware. Use carefully.

## Installation / Update

The current `install.sh` is written for **Arch-based systems** (`pacman`).

1. Put the source folder at:
   - `~/Downloads/OpenFreezeCenter-main`
2. Make scripts executable:
   - `chmod +x install.sh file_1.sh file_2.sh`
3. Run installer:
   - `./install.sh`

What `install.sh` does:
- Installs dependencies: `python`, `python-virtualenv`, `python-gobject`, `python-cairo`
- Creates app directory: `~/Desktop/OFC`
- Creates a virtual environment in `~/Desktop/OFC`
- Copies project files into `~/Desktop/OFC`
- Configures EC module settings via `file_1.sh` and `file_2.sh`
- Loads `ec_sys` module
- Launches OFC with sudo

## Running

Run from the app directory:

```bash
cd ~/Desktop/OFC
./install.sh
```

## Supported Hardware (tested)
- MSI GF65 10UE

## Supported Linux Distro (tested)
- Arch-based distros (current installer uses `pacman`)

## Issue Format

Use this format when opening issues:

`ISSUE # [CPU] - [LAPTOP MODEL] - [LINUX DISTRO]`

Example:

`ISSUE # i7-11800H - MSI GP76 11UG - Arch Linux`

## Project Goals
- [x] Fan control GUI
- [x] Basic temperature and RPM monitoring
- [ ] Advanced and basic GUI control improvements
- [x] Battery threshold
- [ ] Webcam control
