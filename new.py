import sqlite3
def do_GET(self):
    if self.path.lower().startswith("/robophotos"):
        self.photo_url('http://localhost:5001/snapshots/XpeqTcyLcCjuQHCSrWEhf2.png')
    else:
        self.do_photo_url



