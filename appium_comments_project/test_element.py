import time
import os
import json
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.appium_utils import start_appium_session
from utils.adb_utils import force_stop_instagram, start_instagram


# Only open a session when running this helper directly.
if __name__ == '__main__':
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

def click_save_button(driver):
    """Clicks the visible 'Save' button using accessibility ID."""
    try:
        save_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Save"))
        )
        save_button.click()
        print("✅ Clicked the 'Save' button.")
    except Exception as e:
        print("❌ Failed to click the 'Save' button:", e)
        

def click_allow_button(driver):
    """Clicks the 'Allow' button on Instagram popup."""
    try:
        allow_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "//android.view.View[@text='Allow']"))
        )
        allow_button.click()
        print("✅ Clicked the 'Allow' button.")
    except Exception as e:
        print("❌ Failed to click 'Allow' button:", e)

def click_skip_button(driver):
    """Clicks the 'Skip' button using its accessibility ID."""
    try:
        skip_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Skip"))
        )
        skip_button.click()
        print("✅ Clicked the 'Skip' button.")
    except Exception as e:
        print("❌ Failed to click the 'Skip' button:", e)
                           
