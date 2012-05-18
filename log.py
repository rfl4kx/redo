import sys, os
from helpers import atoi


# By default, no output colouring.
RED    = ""
GREEN  = ""
YELLOW = ""
BOLD   = ""
PLAIN  = ""


if sys.stderr.isatty() and (os.environ.get('TERM') or 'dumb') != 'dumb':
    # ...use ANSI formatting codes.
    RED    = "\x1b[31m"
    GREEN  = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BOLD   = "\x1b[1m"
    PLAIN  = "\x1b[m"


DEBUG = atoi(os.environ.get('REDO_DEBUG', ''))
DEPTH = os.environ.get('REDO_DEPTH', '')
DEBUG_PIDS = os.environ.get('REDO_DEBUG_PIDS', '')


def log_(s):
    sys.stdout.flush()
    if DEBUG_PIDS:
        sys.stderr.write('%d %s' % (os.getpid(), s))
    else:
        sys.stderr.write(s)
    sys.stderr.flush()


def log(s):
    log_(''.join([GREEN,  "redo  ", DEPTH, BOLD, s, PLAIN]))

def err(s):
    log_(''.join([RED,    "redo  ", DEPTH, BOLD, s, PLAIN]))

def warn(s):
    log_(''.join([YELLOW, "redo  ", DEPTH, BOLD, s, PLAIN]))


def debug(s):
    if DEBUG >= 1:
        log_('redo: %s%s' % (DEPTH, s))
def debug2(s):
    if DEBUG >= 2:
        log_('redo: %s%s' % (DEPTH, s))
def debug3(s):
    if DEBUG >= 3:
        log_('redo: %s%s' % (DEPTH, s))


