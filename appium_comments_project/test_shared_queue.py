import multiprocessing
import tempfile
import unittest
from pathlib import Path
from shared_queue import CommentQueue
from multi_device import load_devices
import json


def claim_all(path, worker_id, results):
    queue = CommentQueue(path)
    jobs = []
    for i in range(30):
        job = queue.claim(f'user-{worker_id}-{i}', str(worker_id))
        if job:
            jobs.append(job['id'])
    results.put(jobs)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.queue = CommentQueue(self.root / 'queue.sqlite3')
        self.source = self.root / 'comments.txt'

    def enqueue(self, count=1):
        self.source.write_text('https://www.instagram.com/p/test/\n' + '\n'.join(f'comment {i}' for i in range(count)), encoding='utf-8')
        return self.queue.enqueue(self.source)

    def test_parallel_devices_never_claim_same_comment(self):
        self.enqueue(80)
        results = multiprocessing.Queue()
        workers = [multiprocessing.Process(target=claim_all, args=(self.queue.path, i, results)) for i in range(4)]
        for w in workers:
            w.start()
        ids = []
        for _ in workers:
            ids.extend(results.get(timeout=30))
        for w in workers:
            w.join(30)
            self.assertEqual(w.exitcode, 0)
        results.close()
        results.join_thread()
        self.assertEqual(len(ids), 80)
        self.assertEqual(len(set(ids)), 80)
        self.assertEqual(self.queue.counts()['pending'], 0)

    def test_claim_survives_worker_failure_and_blocks_same_account(self):
        self.enqueue(2)
        job = self.queue.claim('alice', 'phone1')
        reopened = CommentQueue(self.queue.path)
        self.assertIsNone(reopened.claim('alice', 'phone2'))
        self.assertEqual(reopened.counts()['pending'], 1)
        reopened.finish(job['id'], False, 'failure')
        self.assertEqual(reopened.counts()['failed'], 1)
        self.assertEqual(reopened.counts()['pending'], 1)

    def test_reimport_identical_batch_does_not_restore_consumed_comments(self):
        self.enqueue()
        self.queue.claim('alice', 'phone1')
        self.assertEqual(self.queue.enqueue(self.source), 0)
        self.assertEqual(self.queue.counts()['pending'], 0)

    def test_legacy_progress_prevents_repeat_account_post(self):
        self.enqueue()
        path = self.root / 'legacy.json'
        path.write_text(json.dumps({'processed_comments': {'https://www.instagram.com/p/test/': {'alice': 'old'}}}))
        self.queue.seed_progress(path)
        self.queue.seed_progress(path)
        self.assertFalse(self.queue.has_work('alice'))
        self.assertTrue(self.queue.has_work('bob'))
        self.assertEqual(self.queue.counts()['submitted'], 1)

    def test_export_keeps_status_and_device(self):
        self.enqueue()
        job = self.queue.claim('alice', 'phone1')
        self.queue.finish(job['id'], True)
        out = self.root / 'report.txt'
        self.queue.export(out)
        self.assertIn('alice [phone1; submitted]: comment 0', out.read_text())

    def test_duplicate_device_ports_rejected(self):
        devices = [{'name': 'one', 'udid': 'one', 'system_port': 9205}, {'name': 'two', 'udid': 'two', 'system_port': 9205}]
        path = self.root / 'devices.json'
        path.write_text(json.dumps({'devices': devices}))
        with self.assertRaisesRegex(ValueError, 'system_port'):
            load_devices(path)


if __name__ == '__main__':
    unittest.main()
