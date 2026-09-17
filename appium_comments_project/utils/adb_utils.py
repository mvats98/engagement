import subprocess
import time


def force_stop_instagram(DEVICE_ID, package_name):
    subprocess.run(['adb', '-s', DEVICE_ID, 'shell', 'am', 'force-stop', package_name], check=False)
    time.sleep(2)


def start_instagram(DEVICE_ID, package_name):
    activity = f'{package_name}/com.instagram.mainactivity.InstagramMainActivity'
    subprocess.run(['adb', '-s', DEVICE_ID, 'shell', 'am', 'start', '-n', activity], check=False)
    time.sleep(3)


def is_instagram_running(DEVICE_ID, package_name):
    result = subprocess.run(['adb', '-s', DEVICE_ID, 'shell', 'dumpsys', 'activity'],
                            capture_output=True, text=True, check=False)
    return package_name.lower() in result.stdout.lower()
