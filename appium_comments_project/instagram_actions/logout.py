import os
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.adb_utils import force_stop_instagram, start_instagram
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.interaction import Interaction
from selenium.webdriver.common.action_chains import ActionChains
from config import DEVICE_ID

device_id= DEVICE_ID  # Set your device ID here
LOGIN_STATUS_FILE = "login_status.json"

def click_options_button(driver, device_id="emulator-5554", bounds="[622,77][706,175]"):
    """Tries all available strategies to click the 'Options' button safely."""
    
    # Method 1: Accessibility ID
    try:
        print("🎯 Trying ACCESSIBILITY_ID...")
        driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Options").click()
        print("✅ Clicked using ACCESSIBILITY_ID")
        return True
    except Exception as e1:
        print(f"⚠️ ACCESSIBILITY_ID failed: {e1}")

        # Method 2: UIAutomator
        try:
            print("🎯 Trying ANDROID_UIAUTOMATOR...")
            driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR, 
                'new UiSelector().description("Options")'
            ).click()
            print("✅ Clicked using UIAutomator")
            return True
        except Exception as e2:
            print(f"⚠️ UIAUTOMATOR failed: {e2}")

            # Method 3: XPath
            try:
                print("🎯 Trying XPATH...")
                driver.find_element(
                    AppiumBy.XPATH, 
                    '//android.widget.Button[@content-desc="Options"]'
                ).click()
                print("✅ Clicked using XPath")
                return True
            except Exception as e3:
                print(f"⚠️ XPath failed: {e3}")

                # Method 4: Class name + index
                try:
                    print("🎯 Trying CLASS_NAME + index...")
                    buttons = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
                    buttons[3].click()
                    print("✅ Clicked using CLASS_NAME[3]")
                    return True
                except Exception as e4:
                    print(f"⚠️ CLASS_NAME + index failed: {e4}")

                    # Method 5: ADB tap using bounds
                    try:
                        print("🎯 Trying ADB tap using bounds...")
                        import re
                        match = re.findall(r"\d+", bounds)
                        if len(match) == 4:
                            x1, y1, x2, y2 = map(int, match)
                            x = (x1 + x2) // 2
                            y = (y1 + y2) // 2
                            os.system(f'adb -s {device_id} shell input tap {x} {y}')
                            print(f"✅ Clicked using ADB tap at ({x}, {y})")
                            return True
                    except Exception as e5:
                        print(f"❌ All methods failed: {e5}")

    return False

def incorrect_password(driver):
    """Handles the 'Incorrect Password' dialog by clicking 'OK'."""
    try:
        ok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.ID, "android:id/button1"))
        )
        if ok_button.text.strip().lower() == "ok":
            ok_button.click()
            print("✅ Clicked 'OK' on incorrect password popup.")
            force_stop_instagram() 
        else:
            print(f"⚠️ Found button1 but text was: {ok_button.text}")
    except Exception as e:
        print("❌ Failed to click 'OK' for incorrect password dialog:", e)
        capture_error(driver, "incorrect_password_ok")

def confirm_you_own(driver):
    force_stop_instagram() 
    start_instagram()
    
def incorrect_username(driver):
    """Handles the 'Incorrect Username' dialog by clicking 'TRY AGAIN'."""
    try:
        try_again_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.ID, "android:id/button1"))
        )
        if try_again_button.text.strip().lower() == "try again":
            try_again_button.click()
            print("✅ Clicked 'TRY AGAIN' on incorrect username popup.")
            force_stop_instagram() 
        else:
            print(f"⚠️ Found button1 but text was: {try_again_button.text}")
    except Exception as e:
        print("❌ Failed to click 'TRY AGAIN' for incorrect username dialog:", e)
        capture_error(driver, "incorrect_username_try_again")    
    
def capture_error(driver, step_name):
    """Capture screenshot + UI dump on error with a timestamp."""
    timestamp = int(time.time())
    os.makedirs("errors", exist_ok=True)

    screenshot_path = f"errors/{step_name}_{timestamp}.png"
    # Save screenshot
    driver.save_screenshot(screenshot_path)

# UI recovery map (extend this as needed)
UI_RECOVERY_MAP = {
    "help us confirm that it's you": "confirm_its_you",
    "help us confirm that you own this account": "confirm_you_own",
    "record a video of yourself": "confirm_its_you",
    "we removed your comment": "removed_comment",
    "we removed some content or messages": "removed_comment",
    "we noticed suspicious activity": "handle_suspicious_login",
    "incorrect password": "incorrect_password",
    "incorrect username": "incorrect_username"}

def extract_dominant_text(xml):
    try:
        root = ET.fromstring(xml)
        max_size = 0
        dominant_text = None

        for node in root.iter():
            text = node.attrib.get("text", "").strip()
            size = int(node.attrib.get("textSize", "0").replace("px", "")) if "textSize" in node.attrib else 0
            bold = "bold" in node.attrib.get("font", "").lower() or "bold" in text.lower()

            if text and (bold or size > max_size):
                max_size = size
                dominant_text = text

        return dominant_text or "Unrecognized UI pattern"
    except Exception as e:
        print("❌ Failed to extract dominant text:", e)
        return "Unrecognized UI pattern"


from xml.etree import ElementTree as ET
def handle_ui_based_failure(driver, username):
    try:
        page_source = driver.page_source.lower()

        # ✅ Step 1: Known phrase match
        for phrase, function_name in UI_RECOVERY_MAP.items():
            if phrase.lower() in page_source:  # normalize match
                print(f"⚠️ Matched phrase: '{phrase}'. Executing: {function_name}()")

                # Log reason
                with open("restricted_usernames.txt", "a") as f:
                    f.write(f"{username} - {phrase}\n")

                # Comment out account in accounts.py
                try:
                    filepath = os.path.abspath("accounts.py")
                    with open(filepath, "r") as f:
                        lines = f.readlines()
                    with open(filepath, "w") as f:
                        for line in lines:
                            if f'"{username}"' in line and not line.strip().startswith("#"):
                                f.write(f"# {line}")
                            else:
                                f.write(line)
                    print(f"🛑 Account {username} has been commented out in accounts.py")
                except Exception as file_error:
                    print(f"❌ Failed to comment out {username}: {file_error}")

                # Call recovery function
                if function_name in globals():
                    globals()[function_name](driver)
                else:
                    print(f"❌ Function '{function_name}' not defined.")
                return True

        # ✅ Step 2: Fallback — No known phrase matched
        print("ℹ️ No matching UI phrase found. Attempting to extract dominant error text...")
        error_phrase = extract_dominant_text(driver.page_source)

        if error_phrase:
            timestamp = int(time.time())

            # Log fallback phrase
            with open("restricted_usernames.txt", "a") as f:
                f.write(f"{username} - {error_phrase} [fallback]\n")

            # Save full UI XML for analysis
            os.makedirs("errors", exist_ok=True)
            xml_path = f"errors/fallback_ui_{username}_{timestamp}.xml"
            try:
                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"📄 UI XML saved for {username}: {xml_path}")
            except Exception as xml_error:
                print(f"❌ Failed to save fallback UI for {username}:", xml_error)

            # Comment out this account as well
            try:
                filepath = os.path.abspath("accounts.py")
                with open(filepath, "r") as f:
                    lines = f.readlines()
                with open(filepath, "w") as f:
                    for line in lines:
                        if f'"{username}"' in line and not line.strip().startswith("#"):
                            f.write(f"# {line}")
                        else:
                            f.write(line)
                print(f"🛑 Account {username} has been commented out in accounts.py (fallback mode)")
            except Exception as file_error:
                print(f"❌ Failed to comment out {username}: {file_error}")

        return False

    except Exception as e:
        print("❌ Error while analyzing UI:", e)
        return False
    
    
    
def removed_comment(driver):
    """Clicks the 'Cancel' button shown after a comment is removed."""
    try:
        cancel_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Cancel"))
        )
        cancel_button.click()
        print("✅ Clicked the 'Cancel' button after comment removal.")
    except Exception as e:
        print("❌ Failed to click the 'Cancel' button:", e)
        capture_error(driver, "removed_comment_cancel")        

def confirm_its_you(driver):
    wait = WebDriverWait(driver, 10)

    # Step 1: Click Menu
    try:
        menu_button = driver.find_element(AppiumBy.XPATH, '//android.widget.Button[@content-desc="Menu"]')
        menu_button.click()
        print("✅ Clicked the Menu button.")
    except Exception as e:
        print("❌ Could not click Menu button:", e)
        capture_error(driver, "confirm_menu_button")
        return

        
    # Wait for any "Log out <username>" text (username may vary)
    try:
        logout_text = wait.until(EC.presence_of_element_located((
            AppiumBy.XPATH,
            '//android.view.View[starts-with(@text, "Log out")]'
        )))
        print("✅ Found 'Log out <username>' element.")
    except Exception as e:
        print("❌ Could not find logout text element:", e)
        capture_error(driver, "logout_text_detected")
    

    try:
      print("👉 Tapping logout via coordinates using W3C actions...")
  
      finger = PointerInput("touch", "finger")
      actions = ActionChains(driver)
      actions.w3c_actions = ActionBuilder(driver, mouse=finger)  # ✅ attach pointer device
  
      actions.w3c_actions.pointer_action.move_to_location(178, 1254)
      actions.w3c_actions.pointer_action.pointer_down()
      actions.w3c_actions.pointer_action.pointer_up()
  
      actions.perform()
      print("✅ Tapped on 'Log out' via coordinates.")
    except Exception as e:
        print("❌ Failed to tap using W3C coordinates:", e)
        capture_error(driver, "logout_button_tap_coordinates")
        
        
    try:
     logout_confirm_button = WebDriverWait(driver, 10).until(
         EC.element_to_be_clickable((AppiumBy.ID, "com.instagram.android:id/igds_alert_dialog_primary_button")))
     logout_confirm_button.click()
     print("✅ Confirmed logout from dialog.")
    except Exception as e:
        print("❌ Failed to click 'Log out' confirmation button:", e)
        capture_error(driver, "logout_confirm_dialog")
    
    try:
        ok_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
            AppiumBy.ID, "com.instagram.android:id/primary_button")))
        if ok_button.text.strip().lower() == "ok":
            ok_button.click()
            print("✅ Clicked on 'OK' button.")
        else:
            print(f"⚠️ Found primary_button but text was: {ok_button.text}")
    except Exception as e:
        print("❌ Failed to click 'OK' button:", e)
        capture_error(driver, "ok_button_click")
    
    
    # Optional: Restart Instagram on failure
    force_stop_instagram()
    start_instagram()        



def remove_profile_from_settings(driver ,username):
    """Handles 'Remove profiles from this device' flow with retries and screenshot on failure."""
    retry_count = 0
    max_retries = 15
    wait = WebDriverWait(driver, 30)
    while retry_count < max_retries:
        try:
            remove_profiles_button = wait.until(EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "Remove profiles from this device")
            ))
            remove_profiles_button.click()
            print("✅ Clicked 'Remove Profiles from This Device'!")
            time.sleep(2)
            device_id = DEVICE_ID
            x, y = 360 ,1475
            #for _ in range(3):
            os.system(f'adb -s {device_id} shell input tap {x} {y}')
            print(f"✅ Tapped on coordinates ({x}, {y}) using ADB.")
                 
        except Exception as e:
            print("ℹ️ 'Remove Profiles' button not found.")
            capture_error(driver, "remove_profiles_button")

        try:
            remove_button = wait.until(EC.element_to_be_clickable(
                (AppiumBy.XPATH, "//android.view.View[@content-desc='Remove']")
            ))
            remove_button.click()
            print("✅ Clicked 'Remove'!")
            time.sleep(2)
        except Exception as e:
            print("ℹ️ 'Remove' button not found.")
            capture_error(driver, "remove_button")
            handle_ui_based_failure(driver,username)

        try:
            final_remove = wait.until(EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "Remove")
            ))
            final_remove.click()
            print("✅ Clicked final confirmation 'Remove'!")
            time.sleep(2)
        except Exception as e:
            print("ℹ️ Final 'Remove' button not found.")
            capture_error(driver, "final_remove")
            handle_ui_based_failure(driver,username)

        # Check if "Settings" is still visible
        try:
            settings_button = wait.until(EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "Settings")
            ))
            settings_button.click()
            print("🔁 'Settings' still visible. Retrying removal process...")
            time.sleep(2)
            retry_count += 1
        except:
            print("✅ Successfully removed the Instagram profile!")
            break
    else:
        print("❌ Max retries reached. Profile may not be removed successfully.")
        capture_error(driver, "remove_profile_failed")
        handle_ui_based_failure(driver,username)

import time

def wait_for_settings_or_accounts(driver, wait_time=5, retry_delay=5):
    """
    Taps on coordinates, waits, and checks for either 'Settings and activity' or 'Accounts Centre'
    using Appium page_source instead of ADB.
    """
    device_id = DEVICE_ID
    x, y = 664, 126                
    while True:
        # Tap the target element 3 times using ADB
        for _ in range(3):
            os.system(f'adb -s {device_id} shell input tap {x} {y}')
        print(f"✅ Tapped on coordinates ({x}, {y}) using ADB.")
        
        time.sleep(wait_time)

        try:
            ui_dump = driver.page_source
            if "Settings and activity" in ui_dump or "Accounts Centre" in ui_dump:
                print("✅ Found expected UI element in Appium dump. Proceeding...")
                break
            else:
                print("🔁 Expected UI elements not found. Retrying...")
        except Exception as e:
            print(f"❌ Error fetching page source: {e}. Retrying...")

        time.sleep(retry_delay)

def open_settings_and_wait_for_remove(driver, username, device_id):
    wait= WebDriverWait(driver, 30)
    x, y = 665, 120

    while True:
        
        try:
            print("🧭 Trying to click 'Settings' via Accessibility ID...")
            settings_button = wait.until(EC.element_to_be_clickable(
                (AppiumBy.ACCESSIBILITY_ID, "Settings")
            ))
            settings_button.click()
            print("✅ Opened 'Settings' via Accessibility ID.")
            time.sleep(2)
        except Exception as e1:
            print(f"⚠️ Accessibility ID failed: {type(e1).__name__} → {e1}")
            print("📲 Trying fallback tap using ADB...")
            for _ in range(3):
                os.system(f'adb -s {device_id} shell input tap {x} {y}')
            print(f"✅ Tapped on 'Settings' using ADB at ({x}, {y})")
            time.sleep(2)
        try:
           print("🕵️ Dumping UI to check for 'Remove profiles from this device'...")
           ui_dump = driver.page_source
    
           if "Remove profiles from this device" in ui_dump:
               print("✅ Text found in UI dump. Proceeding...")
               remove_profile_from_settings(driver, username)
               break
           else:
               print("🔁 Text not found in UI dump. Retrying...\n")
               time.sleep(2)
               continue
    
        except Exception as e:
            print(f"❌ Error while checking UI dump: {e}")
            time.sleep(2)
            continue

def logout(driver, username):
    
    if not os.path.exists(LOGIN_STATUS_FILE):
        print("ℹ️ login_status.json does not exist. Skipping logout.")
        return

    wait = WebDriverWait(driver, 10)
    
    try:
        profile_button = wait.until(EC.element_to_be_clickable(
            (AppiumBy.XPATH, "//android.widget.FrameLayout[@content-desc='Profile']")
        ))
        profile_button.click()
        print("✅ clicked profile button")
        time.sleep(2)
        
    except Exception as e:
        print("❌ Failed to click 'Profile'")
        capture_error(driver, "profile_button")
        device_id = DEVICE_ID
        x, y = 644, 1434
        for _ in range(3):
            os.system(f'adb -s {device_id} shell input tap {x} {y}')
        print(f"✅ Tapped on 'profile' button at coordinates ({x}, {y}) using ADB commands.")

    driver.background_app(1)
    print("🔄 Backgrounded app for 2 seconds to get option/menu button .")
    time.sleep(2)

    
    # try:
    #     menu_button = wait.until(EC.element_to_be_clickable(
    #         (AppiumBy.ACCESSIBILITY_ID, "Options")
    #     ))
    #     menu_button.click()
    #     print("✅ clicked options button")
    #     time.sleep(2)
    # except Exception as e:
    #     print("❌ Failed to click 'Options'")
    #     capture_error(driver, "options_button")

    wait_for_settings_or_accounts(driver)
    
    for _ in range(7):
        driver.swipe(600, 700, 600, 50)
        time.sleep(1)

    try:
        logout_button = wait.until(EC.element_to_be_clickable(
            (AppiumBy.XPATH, "//android.widget.Button[@text='Log out']")
        ))
        logout_button.click()
        time.sleep(2)
    except Exception as e:
        print("❌ Failed to click 'Log out'")
        capture_error(driver, "logout_button")
        handle_ui_based_failure(driver,username)

    try:
        confirm_buttons = driver.find_elements(AppiumBy.XPATH, "//android.widget.Button[@text='Log out']")
        if confirm_buttons:
            confirm_buttons[0].click()
            time.sleep(2)
    except Exception as e:
        print("ℹ️ Confirm logout button not found.")
        capture_error(driver, "confirm_logout")
        handle_ui_based_failure(driver,username)

    try:
        not_now_button = wait.until(EC.element_to_be_clickable(
            (AppiumBy.ID, "com.instagram.android:id/negative_button")
        ))
        not_now_button.click()
        print("✅ Clicked 'Not Now' to continue logout!")
        time.sleep(2)
    except:
        print("ℹ️ 'Not Now' button not shown. Continuing...")

   
    try:
        final_logout_button = wait.until(EC.element_to_be_clickable(
            (AppiumBy.ID, "com.instagram.android:id/primary_button")
        ))
        final_logout_button.click()
        print("✅ Final 'Log Out' clicked!")
        time.sleep(2)
    except:
        print("ℹ️ Final logout not required or already handled.")

    open_settings_and_wait_for_remove(driver, username, DEVICE_ID)