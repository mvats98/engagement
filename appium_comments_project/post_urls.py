import os

def load_post_urls():
    """Dynamically loads post URLs from a file and ensures the file exists."""
    if not os.path.exists("post_urls.txt"):
        print("⚠️ post_urls.txt file does not exist. Creating an empty file...")
        open("post_urls.txt", "w").close()  # ✅ Create an empty file if missing
        return []  # ✅ Return an empty list

    with open("post_urls.txt", "r") as f:
        urls = f.read().splitlines()
    
    urls = [url.strip() for url in urls if url.strip()]  # ✅ Remove empty lines
    
    if not urls:
        print("⚠️ No valid URLs found in post_urls.txt")
    
    return urls  # ✅ Always returns a list (even if empty)

def remove_url(url):
    """Removes a specific URL from post_urls.txt after processing it."""
    urls = load_post_urls()  # ✅ Always loads dynamically
    
    if url in urls:
        print(f"🗑 Removing URL: {url}")
        urls.remove(url)  # ✅ Remove the processed URL

        # ✅ Update file dynamically
        with open("post_urls.txt", "w") as f:
            if urls:  
                f.write("\n".join(urls) + "\n")  # ✅ Save remaining URLs
            else:
                print("⚠️ All URLs have been processed. post_urls.txt is now empty.")
                f.write("")  # ✅ Clear file if no URLs are left
    else:
        print(f"⚠️ URL not found in post_urls.txt: {url}")

