import os

COMMENT_DATA_FILE = "comment_data.txt"

def load_comment_data():
    """Loads post URLs and their respective comments from comment_data.txt (new format)."""
    if not os.path.exists(COMMENT_DATA_FILE):
        print("⚠️ comment_data.txt file does not exist. Creating an empty file...")
        open(COMMENT_DATA_FILE, "w").close()
        return {}

    comment_dict = {}
    current_url = None

    with open(COMMENT_DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("https://www.instagram.com/"):
            current_url = line
            comment_dict[current_url] = []
        elif current_url:
            comment_dict[current_url].append(line)

    if not comment_dict:
        print("⚠️ No valid comments found in comment_data.txt")

    return comment_dict

def remove_comment_url(url):
    """Removes a post and its comments from comment_data.txt after processing."""
    if not os.path.exists(COMMENT_DATA_FILE):
        return

    with open(COMMENT_DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    skip = False

    for line in lines:
        if line.strip() == url:
            skip = True
        elif skip and line.strip() == "":
            skip = False
        else:
            if not skip:
                new_lines.append(line)

    with open(COMMENT_DATA_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"🗑 Removed all comments for: {url}")

def save_comment_data(comment_dict):
    """Overwrites comment_data.txt with updated comment data."""
    with open(COMMENT_DATA_FILE, "w", encoding="utf-8") as f:
        for url, comments in comment_dict.items():
            f.write(f"{url}\n")
            for comment in comments:
                f.write(f"{comment}\n")
            f.write("\n")  # blank line to separate posts
            
            
def safe_save_comment_data(current_dict):
    """Safely merge in any newly added URLs/comments from the file before saving."""
    if os.path.exists(COMMENT_DATA_FILE):
        latest = load_comment_data()
        for url, new_comments in latest.items():
            if url not in current_dict:
                current_dict[url] = new_comments
           

    save_comment_data(current_dict)
            
