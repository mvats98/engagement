# Multiple Android devices with a shared comment queue

The original `main.py` remains the single-device runner. Use `multi_device.py` for
multiple devices connected to this computer. Do not run both runners together.

## Configuration

Run `python setup.py` from the parent folder, then edit `devices.json`.
Replace the example UDID with its `adb devices` serial and assign accounts
already logged in on that phone. Add another device entry for each phone.
Every enabled device needs a unique name, UDID and system_port. Each account must
be assigned to exactly one device. Accounts only need a `username`; all devices
use `com.instagram.android` from `config.py`. No VPN is used.
The launcher uses accounts from this JSON, not accounts.py.

Start your existing Appium server with UiAutomator2 installed (the example uses
http://127.0.0.1:4725). One server can serve the independent device sessions.
The explicit UDID and unique systemPort follow the Appium driver guidance:
https://github.com/appium/appium-uiautomator2-driver#parallel-tests

Run commands from this project folder:

```powershell
python -m pip install -r requirements.txt
python multi_device.py check
python multi_device.py enqueue --source comment_data.txt
python multi_device.py status
python multi_device.py run
```

`check` validates configuration without connecting to devices. Ctrl+C stops the
workers. Login status, UI dumps and local progress are isolated under
`device_state/<name>/`. Worker errors include the device name.

## Queue behavior

Both runners attempt to like each post before opening its comment section.
Already-liked posts are left liked. A missing button or unconfirmed like is
logged and commenting continues. Queue status still describes the comment
submission only. Previously completed comments are not replayed to add likes.

SQLite (`comment_queue.sqlite3`) is the live shared queue. The text file is an
import source; it is not the live queue and is not rewritten by workers.
Each URL line is followed by its comments, with optional blank lines between URLs.

An account claims the first eligible comment only after login is confirmed.
In one database transaction, the comment is removed from `pending` and added to
claim history. Other devices cannot claim it. Once its last comment is claimed,
a URL no longer appears in the pending queue. Each account can claim at most one
comment per URL, preserving the previous runner's behavior.

A failed or interrupted claim is never returned automatically. This provides
at-most-once claiming, including when a phone disconnects. `claimed` means an
attempt has not reported an outcome (possibly a crash); `submitted` means the UI
post button was clicked successfully, not server-side verification that Instagram
published the comment. `failed` means failure or uncertainty was reported.

Enqueue new work while workers run with:

```powershell
python multi_device.py enqueue --source new_comments.txt
python multi_device.py status
python multi_device.py export
```

Each new import should contain only new work. Reimporting the exact same file
content is ignored, even after consumption. Editing a previously imported file
creates a new batch and will import all its comments, including any old lines.
Duplicate comment text within a batch is allowed as separate queue items.
Existing comment_progress.json history is imported on enqueue to prevent those
accounts commenting again on the same URLs. Original data/progress files remain
unchanged. Enqueue is explicit; workers do not watch edits to comment_data.txt.

The combined report is `multi_device_progress.txt`; export it on demand, or it
is exported when the launcher shuts down. The original comment_progress.txt is
preserved. Keep the SQLite database on this computer's local disk.

## Verification

```powershell
python -m unittest test_shared_queue -v
```

Tests use temporary databases and simulated worker processes; they never contact
Instagram. Real device operation requires Appium, ADB and installed Python
packages. The launcher reserves local port 47999 to prevent duplicate launchers.
