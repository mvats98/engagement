from config import DEVICE_ID
import os
from comment_data import load_comment_data, remove_comment_url, save_comment_data, safe_save_comment_data
from comment_progress import load_comment_progress, save_comment_progress
from instagram_actions.comment_post import comment_post
from utils.adb_utils import force_stop_instagram, start_instagram

LOGIN_STATUS_FILE = "login_status.json"

def process_comments(driver, account, package_name):
    if not os.path.exists(LOGIN_STATUS_FILE):
        print("ℹ️ login_status.json does not exist. Skipping logout.")
        return

    progress = load_comment_progress()
    processed_comments = progress["processed_comments"]

    comment_data = load_comment_data()
    if not comment_data:
        print("⚠️ No comment data found! Cannot proceed with commenting.")
        return

    post_urls = list(comment_data.keys())
    if not post_urls:
        print("✅ No more URLs left for commenting. Logging out...")
        return

    username = account["username"]
    print(f"🔁 Starting comments for account: {username}")

    for url in post_urls:
        if url in processed_comments and username in processed_comments[url]:
            continue

        comments = comment_data.get(url, [])
        if not comments:
            print(f"⚠️ No comments available for {url}. Removing URL...")
            comment_data.pop(url, None)
            remove_comment_url(url)
            safe_save_comment_data(comment_data)
            continue

        try:
            comment_text = comments.pop(0)
            safe_save_comment_data(comment_data)
        except IndexError:
            print(f"❌ Tried to pop comment from empty list for {url}. Removing URL...")
            comment_data.pop(url, None)
            remove_comment_url(url)
            safe_save_comment_data(comment_data)
            continue

        print(f"💬 {username} commenting on {url} with: {comment_text}")
        comment_post(driver, url, DEVICE_ID, username, comment_text, package_name)
        

        # Track progress
        if url not in processed_comments:
            processed_comments[url] = {}
        processed_comments[url][username] = comment_text
        progress["processed_comments"] = processed_comments

        # Update comment data
        if comments:
            comment_data[url] = comments
        else:
            comment_data.pop(url, None)
            remove_comment_url(url)

        safe_save_comment_data(comment_data)
        save_comment_progress(processed_comments=processed_comments)

    print(f"✅ Finished all URLs for {username}\n")
   