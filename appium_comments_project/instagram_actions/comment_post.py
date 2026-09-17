import os
import time
import subprocess
from selenium.common.exceptions import TimeoutException
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from comment_progress import load_comment_progress, save_comment_progress
from instagram_actions.like_post import like_current_post
from utils.adb_utils import force_stop_instagram, start_instagram
from utils.ui_recovery_handler import (
    handle_ui_based_failure,
    UI_RECOVERY_MAP,
    confirm_its_you,
    incorrect_password,
    incorrect_username,
    removed_comment,
    confirm_you_own, 
    capture_error
)


def open_post_with_retry(driver, url, device_id, package_name, max_attempts=3):
    """Retry only navigation, before any like or comment is attempted."""
    wait = WebDriverWait(driver, 5)
    locator = (AppiumBy.ID, f'{package_name}:id/row_feed_button_comment')
    for attempt in range(1, max_attempts + 1):
        print(f'Opening post (attempt {attempt}/{max_attempts}): {url}', flush=True)
        try:
            subprocess.run([
                'adb', '-s', device_id, 'shell', 'am', 'start', '-n',
                f'{package_name}/com.instagram.mainactivity.LauncherActivity',
                '-a', 'android.intent.action.VIEW', '-d', url,
            ], check=True, timeout=20)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f'Post launch failed: {exc}', flush=True)
            continue
        time.sleep(5)
        scrolled = False
        for swipe in range(6):
            try:
                button = wait.until(EC.element_to_be_clickable(locator))
                return button, scrolled
            except TimeoutException:
                if swipe == 5:
                    break
                size = driver.get_window_size()
                driver.swipe(int(size['width']*.8), int(size['height']*.55),
                             int(size['width']*.8), int(size['height']*.25))
                scrolled = True
                time.sleep(2)
        print('Post controls did not load; reopening the URL.' if attempt < max_attempts
              else 'Post controls did not load after all attempts.', flush=True)
    return None, False


def comment_post(driver, url, device_id, username, comment_text,package_name, track_progress=True):
    """Posts a comment on a given Instagram post using Appium and tracks progress."""
    wait = WebDriverWait(driver, 30)
    progress = load_comment_progress()
    processed_comments = progress["processed_comments"]

    print(f"💬 {username} opening post: {url}")

    # ✅ Skip if user already commented
    if track_progress and url in processed_comments and username in processed_comments[url]:
        print(f"⚠️ {username} already commented on this post. Skipping...")
        return False

    scrolled = False  # Track whether scrolling was used

    try:
        comment_button, scrolled = open_post_with_retry(
            driver, url, device_id, package_name)

        if not comment_button:
            print(f"❌ {username} could not load post after 3 attempts.")
            handle_ui_based_failure(driver,username)
            force_stop_instagram(device_id, package_name)
            return False

        # Like this post before opening comments, without blocking submission
        # if the like fails or cannot be confirmed.
        if not like_current_post(driver, package_name):
            print(f"{username}: like failed or uncertain; continuing with comment.")

        # ✅ Re-locate freshly to avoid stale reference
        comment_button = wait.until(EC.presence_of_element_located(
            (AppiumBy.ID, f"{package_name}:id/row_feed_button_comment")
        ))
        comment_button.click()
        print(f"💬 {username} opened comment section!")

        # ✅ Type the comment
        def find_comment_field(d):
            # Newer Instagram versions use the multiline composer.
            for suffix in ('layout_comment_thread_edittext_multiline',
                           'layout_comment_thread_edittext'):
                for field in d.find_elements(AppiumBy.ID, f"{package_name}:id/{suffix}"):
                    if field.is_displayed() and field.is_enabled():
                        return field
            return False

        comment_field = wait.until(find_comment_field)
        comment_field.click()
        comment_field.clear()
        comment_field.send_keys(comment_text)

        def comment_text_entered(d):
            field = find_comment_field(d)
            return field and field.text == comment_text

        wait.until(comment_text_entered)

        # ✅ Post the comment
        post_button = wait.until(EC.element_to_be_clickable(
            (AppiumBy.ID, f"{package_name}:id/layout_comment_thread_post_button_icon"))
        )
        post_button.click()
        print(f"✅ {username} commented: {comment_text}")

        # ✅ Save to progress
        if url not in processed_comments:
            processed_comments[url] = {}
        processed_comments[url][username] = comment_text
        if track_progress:
            save_comment_progress(processed_comments=processed_comments)

    except Exception as e:
        print(f"⚠️ {username} could not comment. Error: {e}")
        return False

    # ✅ Exit back to Instagram
    back_times = 1 if scrolled else 3
    try:
        for _ in range(back_times):
            driver.press_keycode(4)
            time.sleep(1)
    except Exception as e:
        print(f"Navigation after submission failed: {e}")

    print("🔙 Exited post and returned to Instagram.")
    return True
