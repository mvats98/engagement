"""Post one comment in the currently open Instagram comment section.

Keep Appium running and stop comment workers before using this live test.
Example: python test_comment_live.py --device phone1 --text "Nice post!"
"""
import argparse
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET


def visible_comment(source, text):
    for node in ET.fromstring(source).iter():
        if 'edittext' in node.get('resource-id', ''):
            continue
        for value in (node.get('text', ''), node.get('content-desc', '')):
            if value == text or value.endswith(' said ' + text):
                return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', default='phone1')
    parser.add_argument('--text', default='Nice post!')
    args = parser.parse_args()
    if not args.text.strip():
        parser.error('Comment must not be empty')
    root = Path(__file__).resolve().parent
    devices = json.loads((root / 'devices.json').read_text(encoding='utf-8-sig'))['devices']
    device = next((d for d in devices if args.device in (d['name'], d['udid'])), None)
    if device is None:
        parser.error('Device not found in devices.json')
    os.environ['INSTAGRAM_DEVICE_ID'] = device['udid']
    os.environ['INSTAGRAM_APPIUM_SERVER'] = device['appium_server']
    os.environ['INSTAGRAM_SYSTEM_PORT'] = str(device['system_port'])

    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from utils.appium_utils import start_appium_session

    ids = ['com.instagram.android:id/layout_comment_thread_edittext_multiline',
           'com.instagram.android:id/layout_comment_thread_edittext']
    driver = start_appium_session()
    output = root / 'live_comment_results' / device['name']
    output.mkdir(parents=True, exist_ok=True)
    try:
        wait = WebDriverWait(driver, 15)

        def find_field(d):
            for resource_id in ids:
                for element in d.find_elements(AppiumBy.ID, resource_id):
                    if element.is_displayed() and element.is_enabled():
                        return element
            return False

        field = wait.until(find_field)
        print('Input element:', field.get_attribute('resource-id'), flush=True)
        field.click()
        field.clear()
        field.send_keys(args.text)
        wait.until(lambda d: find_field(d).text == args.text)
        print('Verified input:', args.text, flush=True)
        before = driver.page_source
        (output / 'before.xml').write_text(before, encoding='utf-8')
        button = wait.until(EC.element_to_be_clickable((
            AppiumBy.ID, 'com.instagram.android:id/layout_comment_thread_post_button_icon')))
        button.click()  # Submit once only; never retry an uncertain submission.
        print('Post clicked once.', flush=True)

        def posted(d):
            current = find_field(d)
            return current and current.text != args.text and visible_comment(d.page_source, args.text)

        wait.until(posted)
        if visible_comment(before, args.text):
            print('Submission sent; identical text was already visible, so a new comment cannot be confirmed.')
            return 1
        print('PASS: input cleared and the posted comment is visible.', flush=True)
        return 0
    finally:
        try:
            (output / 'after.xml').write_text(driver.page_source, encoding='utf-8')
            driver.save_screenshot(str(output / 'after.png'))
        finally:
            driver.quit()


if __name__ == '__main__':
    raise SystemExit(main())
