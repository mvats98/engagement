"""Run isolated Android workers against one transactional comment queue."""
import argparse
import json
import multiprocessing
import os
import time
from pathlib import Path
from shared_queue import CommentQueue

ROOT = Path(__file__).resolve().parent
PAUSE_FILE = ROOT / 'comments.paused'
STOP_FILE = ROOT / 'comments.stop'


def wait_until_resumed(stop):
    announced = False
    while PAUSE_FILE.exists():
        if not announced:
            print('Comments paused. Use RESUME-COMMENTS.bat to continue.', flush=True)
            announced = True
        if stop.wait(1):
            return False
    if announced:
        print('Comments resumed.', flush=True)
    return not stop.is_set()


def load_devices(path):
    devices = json.loads(Path(path).read_text(encoding='utf-8-sig'))['devices']
    enabled = [d for d in devices if d.get('enabled', True)]
    if not enabled:
        raise ValueError('Enable at least one device in devices.json')
    for key in ('name', 'udid', 'system_port'):
        values = [d[key] for d in enabled]
        if len(values) != len(set(values)):
            raise ValueError(f'Duplicate {key} in enabled devices')
    usernames = set()
    for d in enabled:
        if not d['name'] or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in d['name']):
            raise ValueError('Device names may contain only letters, digits, underscores and hyphens')
        if not isinstance(d['system_port'], int) or not 1024 <= d['system_port'] <= 65535:
            raise ValueError('system_port must be an integer from 1024 to 65535')
        if not d.get('accounts'):
            raise ValueError(f"Assign accounts to {d['name']} before enabling it")
        if not d.get('appium_server', '').startswith(('http://', 'https://')):
            raise ValueError('appium_server must be an HTTP URL')
        for account in d['accounts']:
            username = account['username']
            if not username:
                raise ValueError('Each account requires username')
            if username in usernames:
                raise ValueError(f'Account assigned more than once: {username}')
            usernames.add(username)
    return enabled


def worker(device, db_path, stop):
    # Set environment before importing modules with module-level device constants.
    os.environ['INSTAGRAM_DEVICE_ID'] = device['udid']
    os.environ['INSTAGRAM_APPIUM_SERVER'] = device['appium_server']
    os.environ['INSTAGRAM_SYSTEM_PORT'] = str(device['system_port'])
    state = ROOT / 'device_state' / device['name']
    state.mkdir(parents=True, exist_ok=True)
    os.chdir(state)
    from config import APP_PACKAGE
    from instagram_actions.login import confirm_login, switch_account, reset_login_status
    from instagram_actions.comment_post import comment_post
    from utils.appium_utils import start_appium_session
    from utils.adb_utils import start_instagram, force_stop_instagram
    queue = CommentQueue(db_path)
    while not stop.is_set():
        for account in device['accounts']:
            if not wait_until_resumed(stop):
                break
            username, package = account['username'], APP_PACKAGE
            if not queue.has_work(username):
                continue
            driver = None
            try:
                reset_login_status()
                driver = start_appium_session()
                start_instagram(device['udid'], package)
                if stop.wait(10):
                    break
                logged_in = False
                for _ in range(10):
                    if stop.is_set():
                        break
                    if confirm_login(driver, username):
                        logged_in = True
                        break
                    switch_account(driver, username)
                if not logged_in:
                    print(f"[{device['name']}] Cannot confirm {username}; leaving queue untouched", flush=True)
                    continue
                while not stop.is_set():
                    # Finish any claimed comment before honoring a pause.
                    # Cleanup below closes the session while paused.
                    if PAUSE_FILE.exists():
                        break
                    job = queue.claim(username, device['udid'])
                    if job is None:
                        break
                    try:
                        submitted = comment_post(driver, job['url'], device['udid'], username,
                                                 job['comment'], package, track_progress=False)
                        queue.finish(job['id'], bool(submitted), None if submitted else 'Submission failed or uncertain')
                    except Exception as exc:
                        queue.finish(job['id'], False, str(exc))
                        raise
            except Exception as exc:
                print(f"[{device['name']}] {username}: {exc}", flush=True)
            finally:
                if driver is not None:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                reset_login_status()
                force_stop_instagram(device['udid'], package)
        stop.wait(30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'enqueue', 'status', 'export', 'check'])
    parser.add_argument('--devices', type=Path, default=ROOT / 'devices.json')
    parser.add_argument('--db', type=Path, default=ROOT / 'comment_queue.sqlite3')
    parser.add_argument('--source', type=Path, default=ROOT / 'comment_data.txt')
    parser.add_argument('--output', type=Path, default=ROOT / 'multi_device_progress.txt')
    args = parser.parse_args()
    if args.command == 'check':
        devices = load_devices(args.devices)
        print(f"Configuration valid: {len(devices)} enabled device(s)")
        return
    queue = CommentQueue(args.db)
    if args.command == 'enqueue':
        queue.seed_progress(ROOT / 'comment_progress.json')
        print(f'Enqueued {queue.enqueue(args.source)} comments')
    elif args.command == 'status':
        print(json.dumps(queue.counts(), indent=2))
    elif args.command == 'export':
        queue.export(args.output)
        print(args.output)
    else:
        devices = load_devices(args.devices)
        # A bound local socket prevents a second launcher for these workers.
        import socket
        guard = socket.socket()
        try:
            guard.bind(('127.0.0.1', 47999))
        except OSError:
            guard.close()
            raise SystemExit('Another launcher is running, or local port 47999 is occupied')
        stop = multiprocessing.Event()
        processes = []
        try:
            # A new launcher starts a fresh run after acquiring the single-run guard.
            STOP_FILE.unlink(missing_ok=True)
            PAUSE_FILE.unlink(missing_ok=True)
            for device in devices:
                process = multiprocessing.Process(target=worker, args=(device, str(args.db.resolve()), stop), name=device['name'])
                process.start()
                processes.append(process)
            while all(p.is_alive() for p in processes):
                if STOP_FILE.exists():
                    print('Stop requested. Waiting for current comments and cleanup to finish...', flush=True)
                    stop.set()
                    # Do not terminate a worker partway through submitting a comment.
                    for process in processes:
                        process.join()
                    print('Comment workers stopped.', flush=True)
                    break
                time.sleep(1)
            else:
                raise RuntimeError('A device worker exited; stopping the remaining workers')
        except KeyboardInterrupt:
            print('Stopping device workers...')
        finally:
            stop.set()
            deadline = time.monotonic() + 10
            for process in processes:
                process.join(max(0, deadline - time.monotonic()))
                if process.is_alive():
                    process.terminate()
                    process.join()
            queue.export(args.output)
            guard.close()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
