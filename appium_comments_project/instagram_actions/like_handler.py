import time
from accounts import ACCOUNTS
from config import DEVICE_ID
from post_urls import load_post_urls, remove_url
from progress import load_progress, save_progress
from instagram_actions.like_post import like_post
from instagram_actions.logout import logout

 # Exit function to move to the next account


def process_likes(driver):
    """Handles the liking process while tracking progress."""
    progress = load_progress()
    liked_urls = progress["liked_urls"]
    last_used_account = progress["last_used_account"]
    last_url_index = progress["last_url_index"]

    if last_url_index >= len(load_post_urls()):
        print("✅ No more URLs left. Logging out...")
        return 
    
    post_urls = load_post_urls()
    start_index = last_url_index
    
    for url in post_urls[start_index:]:
        current_account = ACCOUNTS[last_used_account]
        username = current_account["username"]

        # Skip if this account already liked the URL
        if url in liked_urls and username in liked_urls[url]:
            continue

        print(f"📌 {username} liking {url}")
        like_post(driver, url,DEVICE_ID)

        # Update progress
        if url not in liked_urls:
            liked_urls[url] = []
        liked_urls[url].append(username)


        last_url_index += 1
        save_progress(last_url_index, last_used_account, liked_urls)

        # Check if all accounts have liked it → Remove URL
        if set(liked_urls[url]) == {acc["username"] for acc in ACCOUNTS}:
            remove_url(url)
            del liked_urls[url]  # Remove from progress tracking
            save_progress(last_url_index, last_used_account, liked_urls)

        time.sleep(2)  # Small delay