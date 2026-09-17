import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def upload_photo(driver, image_path):
    try:
        add_post_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.ImageView[contains(@content-desc, 'New Post')]"))
        )
        add_post_button.click()

        time.sleep(2)

        # Select from gallery
        gallery_photo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.ImageView"))
        )
        gallery_photo.click()

        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "//android.widget.Button[@text='Next']"))
        )
        next_button.click()

        caption_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.EditText"))
        )
        caption_box.send_keys("📸 Uploaded using Appium!")

        share_button = driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@text='Share']")
        share_button.click()

        print("📸 Photo uploaded successfully!")
    except:
        print("⚠️ Failed to upload photo.")
