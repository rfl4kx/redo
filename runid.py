import os


def read(filename):
    "read filename mtime (create file if it doesn't exists)"
    with open(filename, 'a') as f:
        return int(os.fstat(f.fileno()).st_mtime)


def change(filename):
    """Increment mtime from filename, using the current time if possible,
    creating the file if it doesn't exists"""
    try: os.makedirs(os.path.dirname(filename))
    except: pass
    try:
        mtime1 = int(os.stat(filename).st_mtime)
    except OSError:
        mtime1 = 0
    with open(filename, 'a') as f:
        os.utime(filename, None)
        mtime2 = int(os.fstat(f.fileno()).st_mtime)
        if mtime2 <= mtime1:
            mtime2 = mtime1 + 1
            os.utime(filename, (mtime2, mtime2))
        return mtime2

