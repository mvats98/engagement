import subprocess
import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _is_liked(button):
    description = (button.get_attribute("content-desc") or "").strip().lower()
    return (str(button.get_attribute("selected")).lower() == "true"
            or str(button.get_attribute("checked")).lower() == "true"
            or description in {"liked", "unlike"})


def like_current_post(driver, package_name="com.instagram.android"):
    """Like the open post once and leave it open for commenting.

    Return True only when the UI reports a liked state. Never retry a click
    when its outcome is uncertain, since that could remove the like.
    """
    locator = (AppiumBy.ID, f"{package_name}:id/row_feed_button_like")
    try:
        wait = WebDriverWait(driver, 5)
        button = wait.until(EC.element_to_be_clickable(locator))
        if _is_liked(button):
            print("Post already liked; keeping the existing like.")
            return True
        button.click()
        wait.until(lambda current: _is_liked(current.find_element(*locator)))
        print("Post like confirmed in the UI.")
        return True
    except Exception as exc:
        print(f"Could not confirm post like: {exc}")
        return False


def like_post(driver, url, device_id, package_name="com.instagram.android"):
    """Open and like a post, then return to the previous screen."""
    subprocess.run([
        "adb", "-s", device_id, "shell", "am", "start", "-n",
        f"{package_name}/com.instagram.mainactivity.LauncherActivity",
        "-a", "android.intent.action.VIEW", "-d", url,
    ], check=True)
    time.sleep(5)
    try:
        return like_current_post(driver, package_name)
    finally:
        driver.press_keycode(4)
        time.sleep(2)
