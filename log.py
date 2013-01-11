import sys, os
import vars

# By default, no output colouring.
RED    = ""
GREEN  = ""
YELLOW = ""
BOLD   = ""
PLAIN  = ""

if vars.COLOR:
    # ...use ANSI formatting codes.
    RED    = "\x1b[31m"
    GREEN  = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BOLD   = "\x1b[1m"
    PLAIN  = "\x1b[m"


LOGFILE = os.fdopen(vars.LOGFD, "a") if vars.LOGFD else sys.stderr


def _cmd_encode(stamp, line):
    return "\0%s\0%s" % (stamp, line.replace("\0", "\0z\0"))


def log_cmd(cmd, arg):
    from logger import LOGCMD, LOCKCMD
    if LOGCMD:
        with LOCKCMD.write():
            os.write(LOGCMD, _cmd_encode(cmd, arg))
            os.fsync(LOGCMD)


def _fmt(s, *args):
    if args:
        return s % args
    else:
        return s
    

def _log(f, s, *args):
    ss = _fmt(s, *args)
    sys.stdout.flush()
    sys.stderr.flush()
    f.flush()
    if vars.DEBUG_PIDS:
        f.write('%d %s' % (os.getpid(), ss))
    else:
        f.write(ss)
    f.flush()

def log_e(s, *args):
    _log(sys.stderr, s, *args)

def log_l(s, *args):
    _log(LOGFILE, s, *args)

def _color(s, color):
    if s.endswith("\n"):
        return ''.join([color, "redo  ", vars.DEPTH, BOLD, s[:-1], PLAIN, s[-1]])
    else:
        return ''.join([color, "redo  ", vars.DEPTH, BOLD, s, PLAIN])

def log(s, *args):
    log_l(_color(s, GREEN), *args)


def err(s, *args):
    log_l(_color(s, RED), *args)
    log_cmd("redo_err", _fmt(s, *args))


def warn(s, *args):
    log_l(_color(s, YELLOW), *args)
    log_cmd("redo_warn", _fmt(s, *args))


def debug(s, *args):
    if vars.DEBUG >= 1:
        log_l('redo: %s%s' % (vars.DEPTH, s), *args)


def debug2(s, *args):
    if vars.DEBUG >= 2:
        log_l('redo: %s%s' % (vars.DEPTH, s), *args)


def debug3(s, *args):
    if vars.DEBUG >= 3:
        log_l('redo: %s%s' % (vars.DEPTH, s), *args)
