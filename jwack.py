#
# beware the jobberwack
#
import sys, os, errno, select, fcntl, signal
from helpers import atoi, close_on_exec

_toplevel = 0
_mytokens = 1
_fds = None
_waitfds = {}


def _debug(s):
    if 0:
        sys.stderr.write('jwack#%d: %s' % (os.getpid(),s))
    

def _release(n):
    global _mytokens
    _debug('release(%d)\n' % n)
    _mytokens += n
    if _mytokens > 1:
        os.write(_fds[1], 't' * (_mytokens-1))
        _mytokens = 1


def release_mine():
    global _mytokens
    assert(_mytokens >= 1)
    os.write(_fds[1], 't')
    _mytokens -= 1


def _timeout(sig, frame):
    pass


def _make_pipe(startfd):
    (a,b) = os.pipe()
    fds = (fcntl.fcntl(a, fcntl.F_DUPFD, startfd),
            fcntl.fcntl(b, fcntl.F_DUPFD, startfd+1))
    os.close(a)
    os.close(b)
    return fds


def _try_read(fd, n):
    # using djb's suggested way of doing non-blocking reads from a blocking
    # socket: http://cr.yp.to/unix/nonblock.html
    # We can't just make the socket non-blocking, because we want to be
    # compatible with GNU Make, and they can't handle it.
    r,w,x = select.select([fd], [], [], 0)
    if not r:
        return ''  # try again
    # ok, the socket is readable - but some other process might get there
    # first.  We have to set an alarm() in case our read() gets stuck.
    oldh = signal.signal(signal.SIGALRM, _timeout)
    try:
        signal.alarm(1)  # emergency fallback
        try:
            b = os.read(_fds[0], 1)
        except OSError, e:
            if e.errno in (errno.EAGAIN, errno.EINTR):
                # interrupted or it was nonblocking
                return ''  # try again
            else:
                raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, oldh)
    return b and b or None  # None means EOF


def _find_fds():
    flags = ' ' + os.getenv('MAKEFLAGS', '') + ' '
    FIND = ' --jobserver-fds='
    ofs = flags.find(FIND)
    if ofs >= 0:
        s = flags[ofs+len(FIND):]
        (arg,junk) = s.split(' ', 1)
        (a,b) = arg.split(',', 1)
        a = atoi(a)
        b = atoi(b)
        if a <= 0 or b <= 0:
            raise ValueError('invalid --jobserver-fds: %r' % arg)
        try:
            fcntl.fcntl(a, fcntl.F_GETFL)
            fcntl.fcntl(b, fcntl.F_GETFL)
        except IOError, e:
            if e.errno == errno.EBADF:
                raise ValueError('broken --jobserver-fds from make; prefix your Makefile rule with a "+"')
            else:
                raise
        return (a,b)
    else:
        return None


def cleanup_makeflags(flags):
    i = flags.find("--jobserver-fds=")
    if i >= 0:
        prefix = flags[0:i] if i > 0 else ""
        j = i
        while j < len(flags):
            if flags[j].isspace(): break
            j += 1
        if (flags[j+1:] + " ").startswith("-j "):
            j += 2
        return prefix + flags[j+1:]
    else:
        return flags


def cleanup_on_exec():
    "Close file descriptors"
    fds = _find_fds()
    if fds:
        a, b = fds
        close_on_exec(a, True)
        close_on_exec(b, True)
    for waitfd in os.environ.get('REDO_JWACK', '').split(','):
        waitfd = atoi(waitfd, None)
        if waitfd != None: close_on_exec(waitfd, True)
    del os.environ['REDO_JWACK']
    os.environ['MAKEFLAGS'] = cleanup_makeflags(os.getenv('MAKEFLAGS'))


def setup(maxjobs):
    "Start the job server"
    global _fds, _toplevel
    if _fds:
        return  # already set up
    _debug('setup(%d)\n' % maxjobs)
    _fds = _find_fds()
    if maxjobs and not _fds:
        # need to start a new server
        _toplevel = maxjobs
        _fds = _make_pipe(100)
        _release(maxjobs-1)
        os.environ['MAKEFLAGS'] = '%s --jobserver-fds=%d,%d -j' % (
            os.getenv('MAKEFLAGS'), _fds[0], _fds[1])


def wait(want_token):
    rfds = _waitfds.keys()
    if _fds and want_token:
        rfds.append(_fds[0])
    assert(rfds)
    r,w,x = select.select(rfds, [], [])
    _debug('_fds=%r; wfds=%r; readable: %r\n' % (_fds, _waitfds, r))
    for fd in r:
        if _fds and fd == _fds[0]:
            pass
        else:
            pd = _waitfds[fd]
            _debug("done: %r\n" % pd.name)
            _release(1)
            os.close(fd)
            del _waitfds[fd]
            rv = os.waitpid(pd.pid, 0)
            assert(rv[0] == pd.pid)
            _debug("done1: rv=%r\n" % (rv,))
            rv = rv[1]
            if os.WIFEXITED(rv):
                pd.rv = os.WEXITSTATUS(rv)
            else:
                pd.rv = -os.WTERMSIG(rv)
            _debug("done2: rv=%d\n" % pd.rv)
            pd.donefunc(pd.name, pd.rv)


def has_token():
    "Return True if we have one or more tokens available"
    if _mytokens >= 1:
        return True


def get_token(reason):
    "Ensure we have one token available."
    global _mytokens
    assert(_mytokens <= 1)
    setup(1)
    while 1:
        if _mytokens >= 1:
            _debug("_mytokens is %d\n" % _mytokens)
            assert(_mytokens == 1)
            _debug('(%r) used my own token...\n' % reason)
            break
        assert(_mytokens < 1)
        _debug('(%r) waiting for tokens...\n' % reason)
        wait(want_token=1)
        if _mytokens >= 1:
            break
        assert(_mytokens < 1)
        if _fds:
            b = _try_read(_fds[0], 1)
            if b == None:
                raise Exception('unexpected EOF on token read')
            if b:
                _mytokens += 1
                _debug('(%r) got a token (%r).\n' % (reason, b))
                break
    assert(_mytokens <= 1)


def running():
    "Tell if jobs are running"
    return len(_waitfds)


def wait_all():
    "Wait for all jobs to be finished"
    _debug("wait_all\n")
    while running():
        while _mytokens >= 1:
            release_mine()
        _debug("wait_all: wait()\n")
        wait(want_token=0)
    _debug("wait_all: empty list\n")
    get_token('self')  # get my token back
    if _toplevel:
        bb = ''
        while 1:
            b = _try_read(_fds[0], 8192)
            bb += b
            if not b: break
        if len(bb) != _toplevel-1:
            raise Exception('on exit: expected %d tokens; found only %r' 
                            % (_toplevel-1, len(bb)))
        os.write(_fds[1], bb)


def force_return_tokens():
    n = len(_waitfds)
    if n:
        _debug('%d tokens left in force_return_tokens\n' % n)
    _debug('returning %d tokens\n' % n)
    for k in _waitfds.keys():
        del _waitfds[k]
    if _fds:
        _release(n)


def _pre_job(r, w, pfn):
    os.close(r)
    if pfn:
        pfn()


class Job:
    def __init__(self, name, pid, donefunc):
        self.name = name
        self.pid = pid
        self.rv = None
        self.donefunc = donefunc
        
    def __repr__(self):
        return 'Job(%s,%d)' % (self.name, self.pid)

            
def start_job(reason, jobfunc, donefunc):
    """
    Start a job
    jobfunc:  executed in the child process
    doncfunc: executed in the parent process during a wait or wait_all call
    """
    global _mytokens
    assert(_mytokens <= 1)
    get_token(reason)
    assert(_mytokens >= 1)
    assert(_mytokens == 1)
    _mytokens -= 1
    r,w = _make_pipe(50)
    pid = os.fork()
    if pid == 0:
        # child
        os.close(r)
        os.environ['REDO_JWACK'] = "%s,%d" % (os.environ.get('REDO_JWACK'), w)
        rv = 201
        try:
            try:
                rv = jobfunc() or 0
                _debug('jobfunc completed (%r, %r)\n' % (jobfunc,rv))
            except Exception:
                import traceback
                traceback.print_exc()
        finally:
            _debug('exit: %d\n' % rv)
            os._exit(rv)
    close_on_exec(r, True)
    os.close(w)
    pd = Job(reason, pid, donefunc)
    _waitfds[r] = pd
