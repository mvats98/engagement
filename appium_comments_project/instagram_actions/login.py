import os
import json
import time
import subprocess
import re
from pathlib import Path
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from test_element import click_save_button, click_skip_button
import xml.etree.ElementTree as ET
from selenium.webdriver.support import expected_conditions as EC
from config import DEVICE_ID
LOGIN_STATUS_FILE = "login_status.json"
import xml.etree.ElementTree as ET
from appium.webdriver.common.appiumby import AppiumBy

def extract_username_from_ui_dump(driver):
     xml_source = driver.page_source
     root = ET.fromstring(xml_source)
     for elem in root.iter():
         text = elem.attrib.get('text', '')
         resource_id = elem.attrib.get('resource-id', '')
         if resource_id.endswith("action_bar_title") and text.strip():
             return text.strip()
     return None


def confirm_login(driver, username):
    
    def extract_username_from_ui_dump():
        xml_source = driver.page_source
        root = ET.fromstring(xml_source)
        for elem in root.iter():
            text = elem.attrib.get('text', '')
            resource_id = elem.attrib.get('resource-id', '')
            if resource_id.endswith("action_bar_title") and text.strip():
                return text.strip()
        return None
    
    time.sleep(3)
    page_source = driver.page_source
    if username.lower() in page_source.lower():
        print(f"[✔] Confirmed @{username} loaded via UI source.")
        print(f"👤 Currently logged in as: {username}")
        save_login_status({username: "logged_in"})
        time.sleep(10)
        return True
    else:
        print(f"[❌] @{username} not found in page source. SWITCHING ACCOUNT.")
        reset_login_status()
        return False

def switch_account(driver, username):
    """Open the account menu with ADB and select the exact requested account."""
    target = username.lstrip('@').strip()
    if not re.fullmatch(r'[A-Za-z0-9_.]+', target):
        raise ValueError('A valid target username is required')
    device_id = driver.capabilities.get('appium:udid') or driver.capabilities.get('udid') or DEVICE_ID

    def adb_input(*values):
        subprocess.run(
            ['adb', '-s', device_id, 'shell', 'input', *map(str, values)],
            check=True, timeout=15,
        )

    def node_bounds(node):
        values = [int(v) for v in re.findall(r'\d+', node.get('bounds', ''))]
        if len(values) != 4:
            raise RuntimeError('Account menu element bounds unavailable')
        return values

    known = {target.casefold()}
    profile_coordinates = None
    config_path = Path(__file__).resolve().parents[1] / 'devices.json'
    if config_path.exists():
        for device in json.loads(config_path.read_text(encoding='utf-8-sig'))['devices']:
            if device['udid'] == device_id:
                known.update(a['username'].casefold() for a in device['accounts'])
                profile_coordinates = device.get('profile_coordinates')
    current = extract_username_from_ui_dump(driver)
    if current:
        known.add(current.casefold())

    wait = WebDriverWait(driver, 15)
    profile_locator = (AppiumBy.ID, 'com.instagram.android:id/profile_tab')
    profile = wait.until(EC.element_to_be_clickable(profile_locator))
    rect = profile.rect
    x, y = int(rect['x'] + rect['width']/2), int(rect['y'] + rect['height']/2)
    # Some phones report clipped tab bounds; use their inspected icon center.
    if profile_coordinates is not None:
        x, y = profile_coordinates
    adb_input('swipe', x, y, x, y, 1000)
    print(f'Long-pressed Profile at ({x}, {y}) on {device_id}; selecting @{target}', flush=True)
    time.sleep(2)

    def menu_state():
        tree = ET.fromstring(driver.page_source)
        lists = [n for n in tree.iter() if n.get('scrollable') == 'true'
                 and any(c.get('text', '').lstrip('@').casefold() in known for c in n.iter())]
        if not lists:
            raise RuntimeError('Account menu list not found')
        menu = min(lists, key=lambda n: len(list(n.iter())))
        rows = list(menu.iter())
        signature = tuple((n.get('text'), n.get('bounds')) for n in rows if n.get('text'))
        match = next((n for n in rows if n.get('text', '').lstrip('@').casefold() == target.casefold()), None)
        return menu, signature, match

    try:
        selected = False
        # Swipe bottom-to-top first to reveal accounts farther down the list.
        for direction in ('down', 'up'):
            seen = set()
            for step in range(26):
                menu, signature, match = menu_state()
                if match is not None:
                    left, top, right, bottom = node_bounds(match)
                    adb_input('tap', (left+right)//2, (top+bottom)//2)
                    selected = True
                    break
                if signature in seen:
                    break
                if step == 25:
                    raise RuntimeError(f'Scroll limit reached searching for @{target}')
                seen.add(signature)
                left, top, right, bottom = node_bounds(menu)
                x = (left+right)//2
                low, high = int(top+(bottom-top)*.8), int(top+(bottom-top)*.2)
                start, end = (high, low) if direction == 'up' else (low, high)
                adb_input('swipe', x, start, x, end, 400)
                time.sleep(1)
            if selected:
                break
        if not selected:
            raise RuntimeError(f'@{target} not found in account menu')
    except Exception:
        # Dismiss the menu so the runner cannot mistake a listed username
        # for the active account on its next login check.
        driver.press_keycode(4)
        raise

    time.sleep(4)
    wait.until(EC.element_to_be_clickable(profile_locator)).click()
    wait.until(lambda d: (extract_username_from_ui_dump(d) or '').casefold() == target.casefold())
    print(f'Active account confirmed as @{target}', flush=True)
    return True

def load_login_status():
    if os.path.exists(LOGIN_STATUS_FILE):
        with open(LOGIN_STATUS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_login_status(status):
    with open(LOGIN_STATUS_FILE, "w") as f:
        json.dump(status, f)

def login_if_needed(driver, username, password):
    login_status = load_login_status()

    if login_status.get(username) == "logged_in":
        print(f"✅ {username} already logged in. Skipping login.")
        return

    try:
        perform_login(driver, username, password)
    except Exception as e:
        driver.save_screenshot(f"{username}_login_error.png")
        print(f"❌ Login failed for {username}, screenshot saved.")
        return
        raise e
        
def dump_ui(driver, username):
    os.makedirs("ui_dumps", exist_ok=True)
    ui_dump = driver.page_source
    dump_path = f"ui_dumps/{username}_login_dump.xml"
    with open(dump_path, "w", encoding="utf-8") as f:
        f.write(ui_dump)
    return ui_dump

def is_logged_in_from_ui_dump(ui_dump):
    try:
        root = ET.fromstring(ui_dump)
        for elem in root.iter():
            if 'content-desc' in elem.attrib and 'profile' in elem.attrib['content-desc'].lower():
                return True
            if 'text' in elem.attrib and 'your story' in elem.attrib['text'].lower():
                return True
    except Exception as e:
        print(f"❌ Error parsing UI dump: {e}")
    return False
        
def perform_login(driver, username, password):
    wait = WebDriverWait(driver, 60)
    print(f"🔐 Attempting to login: {username}")

    try:
       avatar_tab = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("com.instagram.android:id/tab_avatar")')
       avatar_tab.click()
       print("✅ Clicked on avatar tab.")
    except Exception as e:
        print(f"❌ Avatar tab not found:")
        device_id = DEVICE_ID
        x, y = 972, 2151
        for _ in range(3):
            os.system(f'adb -s {device_id} shell input tap {x} {y}')
        print(f"✅ Tapped on 'profile' button at coordinates ({x}, {y}) using ADB commands.")
        

    
    # ---- Simplified login check logic (1 attempt + fallback UI check) ----
    try:
        wait.until(EC.presence_of_element_located(
            (AppiumBy.XPATH, "//android.widget.FrameLayout[contains(@content-desc, 'Profile')]")
        ))
        print(f"✅ {username} logged in successfully. Instagram home screen loaded.")
    
        login_status = load_login_status()
        login_status[username] = "logged_in"
        save_login_status(login_status)
    
    except Exception as e:
        print(f"❌ {username} login failed — home screen not detected.")
    
    
        print("🕵️ Checking UI dump for possible silent login success...")
        ui_dump = dump_ui(driver, username)
        if is_logged_in_from_ui_dump(ui_dump):
            print(f"✅ Login detected from UI dump for {username}. Marking as logged in.")
            login_status = load_login_status()
            login_status[username] = "logged_in"
            save_login_status(login_status)
        else:
            print(f"❌ Login failed completely for {username}. No profile indicators found.")

  
def reset_login_status():
    if os.path.exists(LOGIN_STATUS_FILE):
        os.remove(LOGIN_STATUS_FILE)
        print("🔄 login_status.json reset.")
    else:
        print("ℹ️ login_status.json does not exist.")
