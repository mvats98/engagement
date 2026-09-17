"""Standalone account-menu test. Stop comment workers and keep Appium running.

python test_account_menu_live.py --device phone1 --username YOUR_INSTAGRAM_USERNAME
Main switching code is not used or modified. No comments are posted.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
import xml.etree.ElementTree as ET


def bounds(node):
    values = [int(v) for v in re.findall(r'\d+', node.get('bounds', ''))]
    if len(values) != 4:
        raise RuntimeError('Element bounds unavailable')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', default='phone1', help='Configured name or UDID')
    parser.add_argument('--username', required=True, help='Exact account to select')
    parser.add_argument('--max-scrolls', type=int, default=25, help='Safety limit per direction')
    args = parser.parse_args()
    target = args.username.lstrip('@').strip()
    if not re.fullmatch(r'[A-Za-z0-9_.]+', target) or args.max_scrolls < 1:
        parser.error('Provide a valid username and positive scroll limit')
    root = Path(__file__).resolve().parent
    devices = json.loads((root / 'devices.json').read_text(encoding='utf-8-sig'))['devices']
    device = next((d for d in devices if args.device in (d['name'], d['udid'])), None)
    if device is None:
        parser.error('Device not found in devices.json')
    guard = socket.socket()
    try:
        guard.bind(('127.0.0.1', 47999))
    except OSError:
        guard.close()
        parser.error('Comment runner is active. Stop it before this test.')
    os.environ['INSTAGRAM_DEVICE_ID'] = device['udid']
    os.environ['INSTAGRAM_APPIUM_SERVER'] = device['appium_server']
    os.environ['INSTAGRAM_SYSTEM_PORT'] = str(device['system_port'])
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if sdk:
        os.environ['PATH'] += os.pathsep + str(Path(sdk) / 'platform-tools')
    adb = shutil.which('adb')
    if not adb:
        guard.close()
        parser.error('ADB not found')

    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from utils.appium_utils import start_appium_session
    from instagram_actions.login import extract_username_from_ui_dump

    def adb_input(*values):
        subprocess.run([adb, '-s', device['udid'], 'shell', 'input',
                        *map(str, values)], check=True, timeout=15)

    output = root / 'live_account_menu_results' / device['name']
    output.mkdir(parents=True, exist_ok=True)
    driver = None
    try:
        driver = start_appium_session()
        wait = WebDriverWait(driver, 15)
        driver.activate_app('com.instagram.android')
        profile_locator = (AppiumBy.ID, 'com.instagram.android:id/profile_tab')
        profile = wait.until(EC.element_to_be_clickable(profile_locator))
        r = profile.rect
        x, y = int(r['x'] + r['width']/2), int(r['y'] + r['height']/2)
        adb_input('swipe', x, y, x, y, 1000)
        print(f'Long-pressed Profile at ({x}, {y}); looking for @{target}', flush=True)
        time.sleep(2)
        known = {a['username'].casefold() for a in device['accounts']} | {target.casefold()}

        def menu_state():
            source = driver.page_source
            tree = ET.fromstring(source)
            # Restrict searching and swiping to an account-containing scrollable list.
            lists = [n for n in tree.iter() if n.get('scrollable') == 'true'
                     and any(c.get('text', '').lstrip('@').casefold() in known for c in n.iter())]
            if not lists:
                raise RuntimeError('Could not identify the account menu list; no blind taps or swipes performed')
            menu = min(lists, key=lambda n: len(list(n.iter())))
            rows = list(menu.iter())
            signature = tuple((n.get('text'), n.get('bounds')) for n in rows if n.get('text'))
            match = next((n for n in rows if n.get('text', '').lstrip('@').casefold() == target.casefold()), None)
            return source, menu, signature, match

        # Swipe bottom-to-top first to reveal accounts farther down the list,
        # then search above if needed. Repeated views end each pass.
        selected = False
        for direction in ('down', 'up'):
            seen = set()
            for step in range(args.max_scrolls + 1):
                source, menu, signature, match = menu_state()
                (output / 'menu.xml').write_text(source, encoding='utf-8')
                if match is not None:
                    left, top, right, bottom = bounds(match)
                    adb_input('tap', (left+right)//2, (top+bottom)//2)
                    print(f'Selected @{target}', flush=True)
                    selected = True
                    break
                if signature in seen:
                    break
                if step == args.max_scrolls:
                    raise RuntimeError('Scroll limit reached; target not found in the inspected portion')
                seen.add(signature)
                left, top, right, bottom = bounds(menu)
                x = (left+right)//2
                low, high = int(top+(bottom-top)*.8), int(top+(bottom-top)*.2)
                start, end = (high, low) if direction == 'up' else (low, high)
                adb_input('swipe', x, start, x, end, 400)
                time.sleep(1)
            if selected:
                break
        if not selected:
            raise RuntimeError(f'@{target} was not found in the account menu')
        time.sleep(4)
        wait.until(EC.element_to_be_clickable(profile_locator)).click()
        wait.until(lambda d: (extract_username_from_ui_dump(d) or '').casefold() == target.casefold())
        print(f'PASS: active account confirmed as @{target}', flush=True)
        return 0
    finally:
        try:
            if driver:
                try:
                    (output / 'after.xml').write_text(driver.page_source, encoding='utf-8')
                    driver.save_screenshot(str(output / 'after.png'))
                finally:
                    driver.quit()
        finally:
            guard.close()


if __name__ == '__main__':
    raise SystemExit(main())
