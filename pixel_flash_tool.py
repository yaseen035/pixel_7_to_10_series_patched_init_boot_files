import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PLATFORM_TOOLS_DIR = os.path.join(REPO_ROOT, "platform-tools")
INIT_BOOTS_DIR = os.path.join(REPO_ROOT, "init_boots")
MAGISK_APK = os.path.join(INIT_BOOTS_DIR, "Magisk-v30.7.apk")

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


def tool_path(name):
    local = os.path.join(PLATFORM_TOOLS_DIR, f"{name}.exe")
    return local if os.path.isfile(local) else name


def run(cmd, capture=True):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if capture:
        out = (result.stdout or "") + (result.stderr or "")
        print(out.strip())
        return out
    return ""


def check_tool(name):
    path = tool_path(name)
    if path == name:
        from shutil import which
        if which(name) is None:
            sys.exit(f"[ERROR] '{name}' not found in {PLATFORM_TOOLS_DIR} or PATH.")


def wait_adb_device():
    print("\nWaiting for device (adb)...")
    run([tool_path("adb"), "wait-for-device"], capture=False)


def wait_fastboot_device():
    print("\nWaiting for device (fastboot)...")
    while True:
        out = run([tool_path("fastboot"), "devices"])
        if out.strip():
            break
        time.sleep(1)


def install_magisk():
    if not os.path.isfile(MAGISK_APK):
        sys.exit(f"[ERROR] Magisk apk not found at {MAGISK_APK}")
    print("\nInstalling Magisk APK...")
    out = run([tool_path("adb"), "install", "-r", MAGISK_APK])
    if "Success" not in out:
        sys.exit("[ERROR] Magisk install failed.")
    print("[OK] Magisk installed.")


def get_fastboot_var(var):
    out = run([tool_path("fastboot"), "getvar", var])
    for line in out.splitlines():
        if line.startswith(f"{var}:"):
            return line.split(":", 1)[1].strip()
    return None


def get_adb_build_id():
    out = run([tool_path("adb"), "shell", "getprop", "ro.build.id"])
    return out.strip().splitlines()[-1].strip() if out.strip() else ""


def find_build_folder(device_dir, build_id):
    for d in os.listdir(device_dir):
        if os.path.isdir(os.path.join(device_dir, d)) and d.lower() == build_id.lower():
            return d
    return None


def read_latest_txt(device_dir):
    path = os.path.join(device_dir, "latest.txt")
    if os.path.isfile(path):
        with open(path) as f:
            return f.read().strip()
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
    out = run([tool_path("fastboot"), "devices"])
    return bool(out.strip())


def is_magisk_installed():
    out = run([tool_path("adb"), "shell", "pm", "list", "packages", "com.topjohnwu.magisk"])
    return "com.topjohnwu.magisk" in out


def main():
    check_tool("adb")
    check_tool("fastboot")

    if not os.path.isdir(INIT_BOOTS_DIR):
        sys.exit(f"[ERROR] 'init_boots' folder not found at {INIT_BOOTS_DIR}")

    image_type = choose_from_list(
        "Select image to flash:",
        ["Patched (Magisk)", "Original"]
    )

    build_id = None

    if is_fastboot_mode():
        print("[INFO] Device already in fastboot mode. Skipping adb steps.")
        print("[WARN] Can't read exact build ID via adb in this mode. Will use latest.txt if available.")
    else:
        wait_adb_device()

        if image_type == "Patched (Magisk)":
            if is_magisk_installed():
                print("[INFO] Magisk already installed. Skipping install step.")
            else:
                install_magisk()
        else:
            print("[INFO] Original image selected. Skipping Magisk install.")

        build_id = get_adb_build_id()
        if build_id:
            print(f"[INFO] Current build ID (adb): {build_id}")
        else:
            print("[WARN] Could not read build ID via adb.")

        run([tool_path("adb"), "reboot", "bootloader"], capture=False)

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

    device_dir = os.path.join(INIT_BOOTS_DIR, folder_name)
    if not os.path.isdir(device_dir):
        sys.exit(f"[ERROR] Folder not found: {device_dir}")

    build = None
    if build_id:
        build = find_build_folder(device_dir, build_id)
        if not build:
            print(f"[WARN] No folder matches build ID '{build_id}'.")

    if not build:
        latest = read_latest_txt(device_dir)
        if latest:
            build = find_build_folder(device_dir, latest)
        if not build:
            sys.exit(
                "[ERROR] Could not determine correct build. "
                f"Add a 'latest.txt' file in {device_dir} with the correct build folder name, "
                "or boot the device normally so adb can read the build ID."
            )

    build_dir = os.path.join(device_dir, build)
    print(f"\nSelected build: {build}")

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
    out = run([tool_path("fastboot"), "flash", "init_boot", image_path])
    if "OKAY" not in out and "Finished" not in out and "error" in out.lower():
        sys.exit("[ERROR] Flash failed. Device not rebooted.")

    print("[OK] Flash complete.")
    input("\nPress Enter to reboot device...")
    run([tool_path("fastboot"), "reboot"], capture=False)
    print("\nDone. Device rebooting.")


if __name__ == "__main__":
    main()
