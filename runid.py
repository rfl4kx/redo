import os


def read(filename):
    try:
        return int(os.stat(filename).st_mtime)
    except OSError:
        open(filename, 'a')
        os.utime(filename, (1,1))
        return 1


def change(filename):
    try: os.makedirs(os.path.dirname(filename))
    except: pass
    orig_runid = read(filename)
    runid = orig_runid + 1
    os.utime(filename, (runid, runid))
    return runid
