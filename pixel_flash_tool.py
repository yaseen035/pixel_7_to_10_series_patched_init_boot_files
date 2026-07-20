import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MAGISK_APK = os.path.join(REPO_ROOT, "Magisk-v30.7.apk")

CODENAME_MAP = {
    "husky": "husky_for_Pixel_8_Pro",
    "shiba": "shiba_for_Pixel_8",
    "akita": "akita_for_Pixel_8a",
    "caiman": "caiman_for_Pixel_9_Pro",
    "komodo": "komodo_for_Pixel_9_Pro_XL",
    "tokay": "tokay_for_Pixel_9",
    "comet": "comet_for_Pixel_9_Pro_Fold",
    "tegu": "tegu_for_Pixel_9a",
    "cheetah": "cheetah_for_Pixel_7_Pro",
    "panther": "panther_for_Pixel_7",
    "lynx": "lynx_for_Pixel_7a",
}


def run(cmd, capture=True):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if capture:
        out = (result.stdout or "") + (result.stderr or "")
        print(out.strip())
        return out
    return ""


def check_tool(name):
    from shutil import which
    if which(name) is None:
        sys.exit(f"[ERROR] '{name}' not found in PATH. Install platform-tools and add to PATH.")


def wait_adb_device():
    print("\nWaiting for device (adb)...")
    run(["adb", "wait-for-device"], capture=False)


def wait_fastboot_device():
    print("\nWaiting for device (fastboot)...")
    run(["fastboot", "wait-for-device"], capture=False)


def install_magisk():
    if not os.path.isfile(MAGISK_APK):
        sys.exit(f"[ERROR] Magisk apk not found at {MAGISK_APK}")
    print("\nInstalling Magisk APK...")
    out = run(["adb", "install", "-r", MAGISK_APK])
    if "Success" not in out:
        sys.exit("[ERROR] Magisk install failed.")
    print("[OK] Magisk installed.")


def get_fastboot_var(var):
    out = run(["fastboot", "getvar", var])
    for line in out.splitlines():
        if line.startswith(f"{var}:"):
            return line.split(":", 1)[1].strip()
    return None


def choose_from_list(title, options):
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        sel = input("Enter number: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(options):
            return options[int(sel) - 1]
        print("Invalid choice, try again.")


def is_fastboot_mode():
    out = run(["fastboot", "devices"])
    return bool(out.strip())


def is_magisk_installed():
    out = run(["adb", "shell", "pm", "list", "packages", "com.topjohnwu.magisk"])
    return "com.topjohnwu.magisk" in out


def main():
    check_tool("adb")
    check_tool("fastboot")

    if is_fastboot_mode():
        print("[INFO] Device already in fastboot mode. Skipping adb steps.")
    else:
        wait_adb_device()

        if is_magisk_installed():
            print("[INFO] Magisk already installed. Skipping install step.")
        else:
            install_magisk()

        run(["adb", "reboot", "bootloader"], capture=False)

    wait_fastboot_device()
    time.sleep(2)

    product = get_fastboot_var("product")
    current_slot = get_fastboot_var("current-slot")
    if not product:
        sys.exit("[ERROR] Could not read device product via fastboot getvar.")

    print(f"\nDetected device codename: {product}")
    print(f"Current slot: {current_slot}")

    folder_name = CODENAME_MAP.get(product)
    if not folder_name:
        sys.exit(f"[ERROR] No matching repo folder for codename '{product}'.")

    device_dir = os.path.join(REPO_ROOT, folder_name)
    if not os.path.isdir(device_dir):
        sys.exit(f"[ERROR] Folder not found: {device_dir}")

    builds = sorted([
        d for d in os.listdir(device_dir)
        if os.path.isdir(os.path.join(device_dir, d))
    ])
    if not builds:
        sys.exit(f"[ERROR] No build folders found in {device_dir}")

    build = builds[-1]
    build_dir = os.path.join(device_dir, build)
    print(f"\nSelected build: {build}")

    image_type = choose_from_list(
        "Select image to flash:",
        ["Patched (Magisk)", "Original"]
    )

    if image_type == "Patched (Magisk)":
        candidates = [f for f in os.listdir(build_dir) if f.startswith("patched_")]
    else:
        candidates = [f for f in os.listdir(build_dir) if f == "init_boot.img"]

    if not candidates:
        sys.exit(f"[ERROR] No matching image found in {build_dir}")

    image_file = candidates[0]
    image_path = os.path.join(build_dir, image_file)

    print("\n===== FLASH SUMMARY =====")
    print(f"Product      : {product}")
    print(f"Build        : {build}")
    print(f"Image type   : {image_type}")
    print(f"Target file  : {image_path}")
    print(f"Current slot : {current_slot}")
    print("==========================")

    print("\nFlashing init_boot...")
    out = run(["fastboot", "flash", "init_boot", image_path])
    if "OKAY" not in out and "Finished" not in out and "error" in out.lower():
        sys.exit("[ERROR] Flash failed. Device not rebooted.")

    print("[OK] Flash complete.")
    input("\nPress Enter to reboot device...")
    run(["fastboot", "reboot"], capture=False)
    print("\nDone. Device rebooting.")


if __name__ == "__main__":
    main()
