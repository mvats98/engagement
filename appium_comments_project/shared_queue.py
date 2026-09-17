"""Transactional shared queue. Only Python's standard library is required."""
from contextlib import contextmanager
import hashlib
import sqlite3
from pathlib import Path


class CommentQueue:
    def __init__(self, path):
        self.path = str(Path(path).resolve())
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS batches (digest TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS pending (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, comment TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY, url TEXT NOT NULL, comment TEXT NOT NULL,
                    username TEXT NOT NULL, device TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'claimed', error TEXT,
                    claimed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url, username));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, source):
        content = Path(source).read_text(encoding='utf-8-sig')
        digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
        rows, url = [], None
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('https://www.instagram.com/'):
                url = line
            elif url:
                rows.append((url, line))
            else:
                raise ValueError('Comment appears before its Instagram URL')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM batches WHERE digest=?', (digest,)).fetchone():
                return 0
            db.executemany('INSERT INTO pending(url, comment) VALUES (?,?)', rows)
            db.execute('INSERT INTO batches VALUES (?)', (digest,))
        return len(rows)

    def has_work(self, username):
        with self.connect() as db:
            return db.execute('''SELECT 1 FROM pending p WHERE NOT EXISTS
                (SELECT 1 FROM claims c WHERE c.url=p.url AND c.username=?) LIMIT 1''',
                (username,)).fetchone() is not None

    def claim(self, username, device):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('''SELECT * FROM pending p WHERE NOT EXISTS
                (SELECT 1 FROM claims c WHERE c.url=p.url AND c.username=?)
                ORDER BY id LIMIT 1''', (username,)).fetchone()
            if row is None:
                return None
            db.execute('INSERT INTO claims(id,url,comment,username,device) VALUES (?,?,?,?,?)',
                       (row['id'], row['url'], row['comment'], username, device))
            db.execute('DELETE FROM pending WHERE id=?', (row['id'],))
            return dict(row)

    def finish(self, claim_id, submitted, error=None):
        with self.connect() as db:
            db.execute('UPDATE claims SET status=?, error=? WHERE id=?',
                       ('submitted' if submitted else 'failed', error, claim_id))

    def seed_progress(self, path):
        import json
        if not Path(path).exists():
            return
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # Negative IDs reserve history imported from the original runner.
            next_id = min(0, db.execute('SELECT COALESCE(MIN(id),0) FROM claims').fetchone()[0]) - 1
            for url, comments in data.get('processed_comments', {}).items():
                for username, comment in comments.items():
                    db.execute('''INSERT OR IGNORE INTO claims
                        (id,url,comment,username,device,status) VALUES (?,?,?,?,?,?)''',
                        (next_id, url, comment, username, 'legacy', 'submitted'))
                    next_id -= 1

    def export(self, path):
        with self.connect() as db:
            rows = db.execute('SELECT * FROM claims ORDER BY url,id').fetchall()
        with Path(path).open('w', encoding='utf-8') as out:
            last_url = None
            for row in rows:
                if row['url'] != last_url:
                    out.write('\n' + row['url'] + '\n')
                    last_url = row['url']
                out.write(f"{row['username']} [{row['device']}; {row['status']}]: {row['comment']}\n")

    def counts(self):
        with self.connect() as db:
            result = {'pending': db.execute('SELECT COUNT(*) FROM pending').fetchone()[0]}
            result.update(dict(db.execute('SELECT status,COUNT(*) FROM claims GROUP BY status')))
            return result

