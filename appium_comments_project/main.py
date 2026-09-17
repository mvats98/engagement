import time
import subprocess
import os
import sys
import random
import json
from instagram_actions.login import reset_login_status, confirm_login, switch_account
from instagram_actions.logout import logout
from instagram_actions.process_comments import process_comments
from utils.adb_utils import force_stop_instagram, start_instagram
from utils.appium_utils import start_appium_session
from accounts import ACCOUNTS
from comment_data import load_comment_data
from comment_progress import load_comment_progress, save_comment_progress
from config import DEVICE_ID, APP_PACKAGE

# --------- Configuration ---------
POLL_INTERVAL_SECONDS = 30       # how often to re-check comment_data when empty
MAX_WAIT_MINUTES = None         # None = wait indefinitely. Or set e.g. 60 for 1 hour.
# ---------------------------------

def restart_script(delay_seconds: int = 5):
    """
    Replace current process with a fresh Python process for the same script.
    Preferred over spawning to avoid accumulating parent processes.
    """
    print(f"⚠️ Restarting script in {delay_seconds} seconds...")
    time.sleep(delay_seconds)
    python = sys.executable
    try:
        os.execv(python, [python] + sys.argv)
    except Exception as e:
        print(f"⚠️ execv failed ({e}), falling back to subprocess.Popen")
        try:
            subprocess.Popen([python] + sys.argv)
        except Exception as ex:
            print(f"❌ Failed to spawn new process: {ex}")
    sys.exit(0)

def account_has_pending_comments(username):
    comment_data = load_comment_data()
    progress = load_comment_progress()
    processed = progress.get("processed_comments", {})

    for url, comments in comment_data.items():
        if url not in processed or username not in processed[url]:
            return True
    return False

def wait_for_comment_data(poll_interval=POLL_INTERVAL_SECONDS, max_wait_minutes=MAX_WAIT_MINUTES):
    """
    Poll load_comment_data() until it returns non-empty.
    - poll_interval: seconds between checks
    - max_wait_minutes: total minutes to wait before giving up (None = wait forever)
    Returns True if data available, False if timed out.
    """
    start = time.time()
    max_wait_seconds = None if max_wait_minutes is None else max_wait_minutes * 60

    print(f"🔎 Waiting for comment_data to appear (poll every {poll_interval}s)"
          + (f", timeout {max_wait_minutes} minutes." if max_wait_minutes else ", waiting indefinitely."))

    while True:
        try:
            data = load_comment_data()
            if data and len(data.keys()) > 0:
                print("✅ comment_data found.")
                return True
        except Exception as e:
            # If loading the file itself throws, log and keep waiting
            print(f"⚠️ Failed to load comment_data: {e}")

        if max_wait_seconds is not None and (time.time() - start) > max_wait_seconds:
            print("⏳ wait_for_comment_data timed out.")
            return False

        time.sleep(poll_interval)

# ---- main loop ----
while True:
    try:
        progress = load_comment_progress()

        # If no comment data, WAIT (don't restart). Use watcher/polling.
        comment_data = load_comment_data()
        if not comment_data or len(comment_data.keys()) == 0:
            # Wait until data appears (poll), or exit/restart if watcher times out.
            ok = wait_for_comment_data()
            if not ok:
                # If watcher timed out and you still want to restart, do so; otherwise loop again.
                # Here we choose to restart to recover; change to `continue` if you prefer to just loop.
                print("⚠️ No data after waiting — restarting script.")
                restart_script(delay_seconds=10)
            # reload after wait
            comment_data = load_comment_data()

        if not comment_data or len(comment_data.keys()) == 0:
            # As a safety net: if still empty after wait, restart
            print("🛑 comment_data still empty after wait; restarting.")
            restart_script(delay_seconds=10)

        current_account_index = progress.get("last_used_account", 0)
        processed_comments = progress.get("processed_comments", {})

        while current_account_index < len(ACCOUNTS):
            account = ACCOUNTS[current_account_index]
            username = account["username"]
            package_name = APP_PACKAGE

            if not account_has_pending_comments(username):
                print(f"✅ {username} has already commented on all posts. Skipping.")
                current_account_index += 1
                save_comment_progress(index=0, account_index=current_account_index)
                continue

            print(f"🔄 Logging in with: {username}")
            driver = start_appium_session()
            start_instagram(DEVICE_ID, package_name)
            time.sleep(10)

            MAX_ATTEMPTS = 10
            attempts = 0

            while True:
                if confirm_login(driver, username):
                    print(f"✅ Logged in as @{username}")
                    break
                else:
                    print(f"🔄 Not logged in as @{username}. Trying to switch account...")
                    try:
                        # The shared ADB switch raises on failure; the next
                        # confirm_login call verifies the active account.
                        switch_account(driver, username)
                    except Exception as e:
                        print(f"⚠️ switch_account threw: {e}")
                    attempts += 1

                if attempts >= MAX_ATTEMPTS:
                    print("❌ Too many failed attempts. Restarting Instagram...")
                    try:
                        force_stop_instagram(DEVICE_ID, package_name)
                    except Exception as e:
                        print(f"⚠️ force_stop_instagram failed: {e}")
                    try:
                        start_instagram(DEVICE_ID, package_name)
                    except Exception as e:
                        print(f"⚠️ start_instagram failed: {e}")
                    attempts = 0  # Reset attempts after restart

            # process comments for current account
            try:
                process_comments(driver, account, package_name)
            except Exception as e:
                print(f"⚠️ process_comments raised: {e}")
                # optional: more recovery logic here

            # tidy up and move to next account
            try:
                driver.quit()
            except:
                pass

            reset_login_status()
            current_account_index += 1
            # reload updated processed_comments and save progress
            progress_data = load_comment_progress()
            save_comment_progress(index=0, account_index=current_account_index)

        print("✅ Completed processing all accounts!")

        # Export comment progress to txt
        final_progress = load_comment_progress()
        with open("comment_progress.txt", "w", encoding="utf-8") as f:
            for url, user_comments in final_progress.get("processed_comments", {}).items():
                f.write(url + "\n")
                for user, comment in user_comments.items():
                    f.write(f"{user}: {comment}\n")
                f.write("\n")

        # Reset progress file while preserving processed_comments
        with open("comment_progress.json", "w", encoding="utf-8") as f:
            json.dump({
                "last_used_account": 0,
                "last_index": 0,
                "processed_comments": final_progress.get("processed_comments", {})
            }, f, indent=2)

        print("🧹 comment_progress.txt saved and progress reset.")
        # 🔀 Shuffle accounts once per session
        random.shuffle(ACCOUNTS)

        # All done for this run — restart the script to pick up new data or continue looping
        print("🔁 Restarting script to begin new session.")
        restart_script(delay_seconds=5)

    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt received — exiting without restart.")
        try:
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
        finally:
            reset_login_status()
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error encountered: {e}")

        try:
            print("⚠️ Attempting to recover session...")
            if 'driver' in locals():
                try:
                    # best-effort cleanup
                    try:
                        logout(driver)
                    except Exception as ex:
                        print(f"⚠️ logout failed: {ex}")
                    try:
                        driver.quit()
                    except:
                        pass
                    reset_login_status()
                except Exception as ex2:
                    print(f"⚠️ Cleanup while driver present failed: {ex2}")

            # ensure Instagram is restarted for the last known package_name
            try:
                if 'package_name' in locals():
                    force_stop_instagram(DEVICE_ID, package_name)
                    start_instagram(DEVICE_ID, package_name)
            except Exception as ex:
                print(f"⚠️ Recovery start/stop failed: {ex}")

        except Exception as ex:
            print(f"⚠️ Recovery failed: {ex}")

        # reset login state and restart the script
        reset_login_status()
        restart_script(delay_seconds=8)
