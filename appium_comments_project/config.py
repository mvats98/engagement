import os

DEVICE_ID = os.environ.get("INSTAGRAM_DEVICE_ID", "")
APPIUM_SERVER = os.environ.get("INSTAGRAM_APPIUM_SERVER", "http://127.0.0.1:4725")
APP_PACKAGE = "com.instagram.android"
APP_ACTIVITY = "com.instagram.mainactivity.InstagramMainActivity"
SYSTEM_PORT = int(os.environ.get("INSTAGRAM_SYSTEM_PORT", "9205"))
