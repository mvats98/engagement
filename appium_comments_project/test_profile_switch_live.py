"""Live test: python test_profile_switch_live.py --device phone1

Stop comment workers first and keep Appium running. Requires two logged-in
Instagram accounts. This switches once and leaves the resulting account open.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', default='phone1', help='Name or UDID in devices.json')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    devices = json.loads((root / 'devices.json').read_text(encoding='utf-8-sig'))['devices']
    device = next((d for d in devices if args.device in (d['name'], d['udid'])), None)
    if device is None:
        parser.error('Device not found in devices.json')

    os.environ['INSTAGRAM_DEVICE_ID'] = device['udid']
    os.environ['INSTAGRAM_APPIUM_SERVER'] = device['appium_server']
    os.environ['INSTAGRAM_SYSTEM_PORT'] = str(device['system_port'])
    if not shutil.which('adb'):
        sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if sdk:
            os.environ['PATH'] += os.pathsep + str(Path(sdk) / 'platform-tools')
    if not shutil.which('adb'):
        parser.error('adb is not available; add Android platform-tools to PATH')

    # Import after setting the selected phone's configuration.
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from instagram_actions.login import switch_account, extract_username_from_ui_dump
    from utils.appium_utils import start_appium_session

    driver = start_appium_session()
    try:
        driver.activate_app('com.instagram.android')

        def open_profile():
            tab = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(
                (AppiumBy.ID, 'com.instagram.android:id/profile_tab')))
            tab.click()
            time.sleep(2)
            return extract_username_from_ui_dump(driver)

        before = open_profile()
        print(f"Device: {device['name']} ({device['udid']})")
        print(f'Before: {before or "unknown"}')
        switch_account(driver, before or '')
        time.sleep(5)
        after = open_profile()
        print(f'After:  {after or "unknown"}')
        if before and after and before != after:
            print('PASS: account changed.')
            return 0
        print('NOT CONFIRMED: username unchanged or unreadable. Check the phone screen.')
        return 1
    finally:
        driver.quit()


if __name__ == '__main__':
    raise SystemExit(main())
