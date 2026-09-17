import json
import os

PROGRESS_FILE = "progress.json"

def load_progress():
    """Loads progress from progress.json or initializes it if empty."""
    if not os.path.exists(PROGRESS_FILE) or os.stat(PROGRESS_FILE).st_size == 0:
        return {"last_used_account": 0, "last_url_index": 0, "liked_urls": {}}

    with open(PROGRESS_FILE, "r") as f:
        return json.load(f)

def save_progress(last_url_index, last_used_account, liked_urls):
    """Saves progress of accounts & liked URLs."""
    data = {
        "last_used_account": last_used_account,
        "last_url_index": last_url_index,
        "liked_urls": liked_urls
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=4)
