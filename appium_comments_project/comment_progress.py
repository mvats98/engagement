import json

COMMENT_PROGRESS_FILE = "comment_progress.json"

def load_comment_progress():
    """Loads progress for comments from comment_progress.json."""
    try:
        with open(COMMENT_PROGRESS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "last_index": 0,
            "last_used_account": 0,
            "processed_comments": {}  # ✅ Tracks specific comments per post & account
        }

def save_comment_progress(index=None, account_index=None, processed_comments=None):
    """Saves progress for comments to comment_progress.json."""
    progress = load_comment_progress()

    if index is not None:
        progress["last_index"] = index
    if account_index is not None:
        progress["last_used_account"] = account_index
    if processed_comments is not None:
        progress["processed_comments"] = processed_comments  # ✅ Saves specific comments

    with open(COMMENT_PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

