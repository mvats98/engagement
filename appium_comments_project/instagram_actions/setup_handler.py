import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def handle_setup_popups(driver):
    """Handles one-time setup screens after login."""
    wait = WebDriverWait(driver, 10)

    try:
    # "Not Now" 
        wait
        not_now_button = wait.until(EC.presence_of_element_located(
        (AppiumBy.XPATH, "//android.view.View[@text='Not now']")
    ))
        not_now_button.click()
        print("⚠️ Clicked 'Not Now' button first!")
        time.sleep(2)
    except:
        print("✅ No 'Not Now' button found.")
  

    try:
        # Sync Contacts popup
        sync_contacts_button = wait.until(EC.presence_of_element_located(
        (AppiumBy.XPATH, "//android.view.View[@text='Skip']")
    ))
        sync_contacts_button.click()
        print("⚠️ Skipped 'Sync Contacts' popup!")
        time.sleep(2)
    except:
        print("✅ No 'Sync Contacts' popup found.")

    try:
        # Continue Button
        continue_button = wait.until(EC.presence_of_element_located(
        (AppiumBy.XPATH, "//android.view.View[@text='Continue']")))
        continue_button.click()
        print("⚠️ Clicked 'Continue' button!")
        time.sleep(2)
    except:
         print("✅ No 'Continue' button found.")

    try:
        wait = WebDriverWait(driver, 10)
        deny_button = wait.until(EC.element_to_be_clickable(
            (AppiumBy.ID, "com.android.packageinstaller:id/permission_deny_button")
        ))
        deny_button.click()
        print("✅ Clicked 'DENY' button!")
    except:
        print("⚠️ 'DENY' button not found or already handled.")    


    try:
        # Cancel Button
         cancel_button = wait.until(EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/primary_button")))
         cancel_button.click()
         print("⚠️ Clicked 'Cancel' button!")
         time.sleep(2)
    except:
         print("✅ No 'Cancel' button found.")
     
    try:
        # Save Login Info popup
        save_login_info_button = wait.until(EC.presence_of_element_located(
            (AppiumBy.XPATH, "//android.widget.Button[contains(@text, 'Not Now')]")
        ))
        save_login_info_button.click()
        print("⚠️ Skipped 'Save Login Info' popup!")
        time.sleep(2)
    except:
        print("✅ No 'Save Login Info' popup found.")

    print("✅ One-time setup completed!")
