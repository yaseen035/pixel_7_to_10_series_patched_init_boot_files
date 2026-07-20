# Pixel 7 to 9 Series Patched init_boot Files

Welcome! This repository contains Magisk-patched `init_boot` files for the Google Pixel 7, 8, and 9 series. You can use these files to easily root your device.

## Supported Devices

* **Pixel 7 Series:** Pixel 7 (panther), Pixel 7 Pro (cheetah), Pixel 7a (lynx)
* **Pixel 8 Series:** Pixel 8 (shiba), Pixel 8 Pro (husky), Pixel 8a (akita)
* **Pixel 9 Series:** Pixel 9 (tokay), Pixel 9 Pro (caiman), Pixel 9 Pro XL (komodo), Pixel 9 Pro Fold (comet), Pixel 9a (tegu)

## Requirements

* An Unlocked Bootloader.
* Android SDK Platform-Tools (ADB & Fastboot) installed on your computer.
* Python 3 (only if using the automated script).

## Method 1: Automated Script (Windows)

`pixel_flash_tool.py` automates the whole process.

### Setup
1. Clone this repository.
2. Place `pixel_flash_tool.py` in the repository root (same folder as `Magisk-v30.7.apk`).
3. Connect your phone via USB with USB debugging enabled.

### Run
```bash
python pixel_flash_tool.py
```

### What it does
1. Detects if the device is in normal (adb) or fastboot mode.
2. If in adb mode: checks if Magisk is already installed, installs it if not, then reboots to bootloader.
3. If already in fastboot mode: skips the above steps.
4. Reads device codename and current slot via `fastboot getvar`.
5. Automatically selects the latest available build for your device.
6. Lets you choose Patched or Original image.
7. Flashes `init_boot` and reboots the device.

## Method 2: Manual (All Platforms)

### Step 1: Download Files
Download the patched `init_boot` image for your specific phone model from this repository. Also, download the `Magisk-v30.7.apk` included here.

### Step 2: Enter Fastboot Mode
Turn off your phone. Turn it on by holding the **Power** and **Volume Down** buttons together until you see the Fastboot Mode screen. Connect your phone to your computer with a USB cable.

### Step 3: Flash the Patched File
Open your computer terminal or command prompt. Type the following command and press Enter:
```bash
fastboot flash init_boot <drag_and_drop_your_downloaded_image_file_here>
```

### Step 4: Reboot
After the flashing is done, type this command to restart your phone:
```bash
fastboot reboot
```

### Step 5: Complete Installation in Magisk App
1. Once your phone turns on normally, install and open the Magisk app.
2. If a popup appears saying **"Requires Additional Setup"**, click **CANCEL** (do not click OK).
3. On the Magisk home screen, click the **Install** button next to Magisk.
4. Choose **Direct Install (Recommended)** from the options and tap **LET'S GO**.
5. Once the installation process is finished, tap the **Reboot** button in the bottom right corner.

You are fully rooted!
