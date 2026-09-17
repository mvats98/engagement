import time
import os
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def follow_user(driver, profile_url, device_id):
    os.system(f"adb -s {device_id} shell am start -a android.intent.action.VIEW -d \"{profile_url}\"")
    time.sleep(5)

    try:
        follow_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.Button[contains(@text, 'Follow')]"))
        )
        follow_button.click()
        print("✅ Followed user successfully!")
    except:
        print("⚠️ Follow button not found.")
