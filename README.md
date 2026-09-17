# Appium comments project

Python runners for Android devices using Appium, with a shared SQLite comment queue.
See [queue behavior and commands](appium_comments_project/README.md).

## Setup on another computer

1. Install Python 3.10+ (add Python to PATH), Node.js, a JDK, and Android SDK platform-tools.
   Follow the [Appium setup guide](https://appium.io/docs/en/3.4/quickstart/) and
   [UiAutomator2 requirements](https://github.com/appium/appium-uiautomator2-driver#requirements).
   Set `JAVA_HOME` and `ANDROID_HOME` for that computer. Put `adb` on PATH.
2. Install Appium and its Android driver:

   ```text
   npm install -g appium
   appium driver install uiautomator2
   appium driver doctor uiautomator2
   ```

3. Extract or clone the project. On Windows double-click `SETUP.bat`, or run
   `python setup.py` from this folder. Setup creates `.venv-local`, installs the
   pinned Python dependencies, and copies examples only when local files are absent.
4. Enable USB debugging, connect the phones, authorize the computer, and run
   `adb devices`. Fill in `appium_comments_project/devices.json` with the serials
   and usernames already logged in on each phone. Each device needs a unique
   name and system port; each username must belong to one device only.
5. On Windows run:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\appium_comments_project\run-local.ps1 check
   ```

6. Put your own new work in `appium_comments_project/comment_data.txt`: a post URL
   followed by one comment per line. Double-click `IMPORT-COMMENTS.bat`, then
   `START-COMMENTS.bat`. Pause, resume, stop and log-viewing buttons are included.

The Windows one-click launcher starts Appium at `http://127.0.0.1:4725`.
For another server address, configure each device and start the runner directly.
`check` validates configuration structure; it does not verify connected hardware.

## macOS / Linux command line

The Python runner can be launched without the Windows buttons. This path has not
been verified against physical devices on macOS or Linux.

```sh
python3 setup.py
cd appium_comments_project
source .venv-local/bin/activate
python multi_device.py check
appium --address 127.0.0.1 --port 4725
# In another terminal with the environment activated:
python multi_device.py enqueue --source comment_data.txt
python multi_device.py run
```

## Moving an existing installation

Copy source files, then run setup on the destination computer. Do not copy virtual
environments: their interpreter paths belong to the computer that created them.
Preserve the folder layout; paths are resolved relative to the launcher/project.
Run the legacy `main.py` from the inner folder and set `INSTAGRAM_DEVICE_ID` first;
it also supports `INSTAGRAM_APPIUM_SERVER` and `INSTAGRAM_SYSTEM_PORT`.

Personal accounts, device configuration, comments, queue databases, screenshots,
logs and progress are excluded from the source package and GitHub. To resume work
on another computer, stop workers first and transfer the private configuration,
queue database (including any SQLite sidecar files), and required progress files
separately. Starting with a fresh database does not preserve past claims.

## Offline verification

From the inner folder, using the installed Python environment:

```text
python -m unittest test_shared_queue test_like_post test_post_loading -v
```

These tests use mocks and temporary databases. Files ending in `_live.py` require
real phones and may perform actions; they are not part of this offline command.
