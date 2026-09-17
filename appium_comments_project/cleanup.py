import subprocess

DEVICE_ID = "192.168.31.43:34063"

import subprocess

def clean_device(device_id, system_port):
    print(f"🧹 Cleaning device: {device_id} (Port {system_port})")
    try:
        subprocess.run(["adb", "-s", device_id, "shell", "am", "force-stop", "io.appium.uiautomator2.server"], check=True)
        subprocess.run(["adb", "-s", device_id, "shell", "am", "force-stop", "io.appium.uiautomator2.server.test"], check=True)
        subprocess.run(["adb", "-s", device_id, "forward", "--remove", f"tcp:{system_port}"], check=True)
        subprocess.run(["adb", "-s", device_id, "shell", "settings", "delete", "global", "hidden_api_policy_pre_p_apps"], check=True)
        subprocess.run(["adb", "-s", device_id, "shell", "settings", "delete", "global", "hidden_api_policy_p_apps"], check=True)
        subprocess.run(["adb", "-s", device_id, "shell", "settings", "delete", "global", "hidden_api_policy"], check=True)
        print("✅ Cleanup successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Cleanup failed: {e}")

# Run this before any new Appium session
clean_device("192.168.31.43:34063", 8202)
