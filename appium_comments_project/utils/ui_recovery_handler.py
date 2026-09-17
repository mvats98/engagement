from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.action_chains import ActionChains
from utils.adb_utils import force_stop_instagram, start_instagram



import time
import os
from xml.etree import ElementTree as ET

# Define your handler functions
def incorrect_password(driver):
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

def incorrect_username(driver):
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

def confirm_you_own(driver):
    force_stop_instagram()
    start_instagram()

def removed_comment(driver):
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
    try:
        menu_button = driver.find_element(AppiumBy.XPATH, '//android.widget.Button[@content-desc="Menu"]')
        menu_button.click()
        print("✅ Clicked the Menu button.")
    except Exception as e:
        print("❌ Could not click Menu button:", e)
        capture_error(driver, "confirm_menu_button")
        return

    try:
        logout_text = wait.until(EC.presence_of_element_located((
            AppiumBy.XPATH, '//android.view.View[starts-with(@text, "Log out")]')))
        print("✅ Found 'Log out <username>' element.")
    except Exception as e:
        print("❌ Could not find logout text element:", e)
        capture_error(driver, "logout_text_detected")

    try:
        print("👉 Tapping logout via coordinates using W3C actions...")
        finger = PointerInput("touch", "finger")
        actions = ActionChains(driver)
        actions.w3c_actions = ActionBuilder(driver, mouse=finger)
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
        ok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.ID, "com.instagram.android:id/primary_button")))
        if ok_button.text.strip().lower() == "ok":
            ok_button.click()
            print("✅ Clicked on 'OK' button.")
        else:
            print(f"⚠️ Found primary_button but text was: {ok_button.text}")
    except Exception as e:
        print("❌ Failed to click 'OK' button:", e)
        capture_error(driver, "ok_button_click")

    force_stop_instagram()
    start_instagram()

# Error capture
def capture_error(driver, step_name):
    timestamp = int(time.time())
    os.makedirs("errors", exist_ok=True)
    driver.save_screenshot(f"errors/{step_name}_{timestamp}.png")

# Phrase mapping
UI_RECOVERY_MAP = {
    "help us confirm that it's you": "confirm_its_you",
    "help us confirm that you own this account": "confirm_you_own",
    "record a video of yourself": "confirm_its_you",
    "we removed your comment": "removed_comment",
    "we removed some content or messages": "removed_comment",
    "we noticed suspicious activity": "handle_suspicious_login",
    "incorrect password": "incorrect_password",
    "incorrect username": "incorrect_username",
}

# Dominant error text
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
                force_stop_instagram()
                start_instagram()    
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
                

        force_stop_instagram()
        start_instagram()
        return True

    except Exception as e:
        print("❌ Error while analyzing UI:", e)
        return False
    
    
    

__all__ = [
    "handle_ui_based_failure",
    "UI_RECOVERY_MAP",
    "confirm_its_you",
    "incorrect_password",
    "incorrect_username",
    "removed_comment",
    "confirm_you_own"
]
