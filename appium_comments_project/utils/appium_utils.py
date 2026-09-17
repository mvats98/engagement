from appium import webdriver
from appium.options.android import UiAutomator2Options
from config import APPIUM_SERVER, DEVICE_ID, APP_PACKAGE, APP_ACTIVITY,SYSTEM_PORT


def start_appium_session():
    if not DEVICE_ID:
        raise ValueError('Set INSTAGRAM_DEVICE_ID, or use multi_device.py with devices.json')
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = DEVICE_ID 
    options.udid = DEVICE_ID
    options.automation_name = "UiAutomator2"
    options.no_reset = True
    #options.set_capability("uiautomator2ServerLaunchTimeout", 60000)
    options.auto_grant_permissions = True  # Ensures required permissions
    options.new_command_timeout = 12000
    options.set_capability("skipServerInstallation", False)
    

    options.set_capability("systemPort", SYSTEM_PORT)
    
   
    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    return driver
