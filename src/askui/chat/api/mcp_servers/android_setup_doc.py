ANDROID_SETUP_GUIDE = """
# Guide: Setting Up Android Devices

This guide explains how to prepare **Android Emulators** and **real Android devices** for automation with AskUI.

---

## Android Emulator

Automating an emulator with AskUI is straightforward once the emulator is installed and running.

### 1. Install Android Studio
- Download and install **Android Studio** from the [official website](https://developer.android.com/studio).

### 2. Create an Emulator with AVD Manager
1. Open **Android Studio**.
2. Go to **More Actions → Virtual Device Manager**.
3. Click **Create Virtual Device…**.
4. Choose a hardware profile (e.g., Pixel 5) → **Next**.
5. Select a system image (preferably one with the Play Store). Download may take a few minutes → **Next**.
6. Configure options if needed → **Finish**.

📖 Reference: [Create and manage virtual devices](https://developer.android.com/studio/run/managing-avds)

### 3. Start the Emulator
1. In **AVD Manager**, click the **Play** button next to your emulator.
2. Wait until the emulator boots fully.

---

## Real Android Devices

AskUI can also automate **physical Android devices** once ADB is installed.

### 1. Enable Developer Options & USB Debugging
1. On your device, go to **Settings → About phone**.
2. Tap **Build number** seven times to enable Developer Options.
3. Go back to **Settings → Developer Options**.
4. Enable **USB Debugging**.

📖 Reference: [Enable adb debugging on your device](https://developer.android.com/studio/command-line/adb#Enabling)

### 2. Install ADB (Platform-Tools)
1. Download **Platform-Tools** from the [official ADB source](https://developer.android.com/studio/releases/platform-tools).
2. Extract the ZIP to a folder, e.g.:
   - Windows: `C:\\platform-tools`
   - macOS/Linux: `~/platform-tools`

📖 Reference: [Android Debug Bridge](https://developer.android.com/studio/command-line/adb)

### 3. Add ADB to PATH
- **Windows**
  1. Press `Win + S`, search for **Environment Variables**, and open it.
  2. Click **Environment Variables…**.
  3. Under **System variables → Path**, click **Edit…**.
  4. Add the path to your `platform-tools` folder.
  5. Save with **OK**.

- **macOS/Linux**
  Add this line to your shell config (`~/.bash_profile`, `~/.zshrc`, or `~/.bashrc`):
  ```bash
  export PATH="$PATH:/path/to/platform-tools"
  ```
  Then save and reload your shell.

### 4. Verify Device Connection
1. Connect your device via USB.
   - On first connection, confirm the **USB Debugging Allow prompt** on your device.
2. Open a terminal and run:
   ```bash
   adb devices
   ```
   Expected output:
   ```
   List of devices attached
   1234567890abcdef    device
   ```
---
"""
