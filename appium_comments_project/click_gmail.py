import time
import os
import json
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.appium_utils import start_appium_session
from utils.adb_utils import force_stop_instagram, start_instagram


# Start Appium session
driver = start_appium_session()


import re
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.interaction import Interaction

import re
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.interaction import Interaction
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

def click_gmail_share_option_w3c(driver):
    try:
        # Step 1: Locate Gmail TextView
        gmail_textview = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.TextView[@text="Gmail"]'))
        )
        print("✅ Gmail text found.")

        # Step 2: Locate its parent
        gmail_parent = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Gmail"]/..')

        # Step 3: Get bounds of parent
        bounds = gmail_parent.get_attribute("bounds")  # Example: "[406,888][468,973]"
        match = re.findall(r'\[(\d+),(\d+)\]', bounds)
        if not match:
            print("❌ Could not parse bounds.")
            return

        x1, y1 = map(int, match[0])
        x2, y2 = map(int, match[1])
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        print(f"👉 Tapping at ({center_x}, {center_y})")

        # Step 4: Perform W3C-compliant tap using ActionChains
        try:
            print("👉 Tapping Gmail via coordinates using W3C actions...")
            finger = PointerInput("touch", "finger")
            actions = ActionChains(driver)
            actions.w3c_actions = ActionBuilder(driver, mouse=finger)  # attach pointer device
            actions.w3c_actions.pointer_action.move_to_location(center_x, center_y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.pointer_up()
            actions.perform()
            print("✅ Tapped on 'Gmail' via coordinates.")
        except Exception as e:
            print("❌ Failed to tap using W3C coordinates:", e)

    except Exception as e:
        print(f"❌ Error during Gmail share tap: {e}")

click_gmail_share_option_w3c(driver)