import os, sys
import vars, state
from log import log, err, LOGFILE
from helpers import close_on_exec


LOGCMD = None
if vars.LOGFD[1]:
    LOGCMD = os.fdopen(vars.LOGFD[1], "w")


def _encode(stamp, line):
    return "\0%s\0%s" % (stamp, line.replace("\0", "\0z\0"))

class Logger:
    def __init__(self, logfd, stdoutfd):
        self.stdoutfd = stdoutfd
        self.logfd    = logfd
        self.fd_std_in, self.fd_std_out = os.pipe()
        self.fd_err_in, self.fd_err_out = os.pipe()
        self.fd_log_in, self.fd_log_out = os.pipe()
        self.fd_cmd_in, self.fd_cmd_out = os.pipe()

    def fork(self):
        pid = os.fork()
        if pid == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_cmd_out)
            os.close(self.fd_err_in)
            os.close(self.fd_log_in)
            os.close(self.fd_cmd_in)
            self._main(os.fdopen(self.fd_std_in), "std", sys.stdout, self.stdoutfd, dbg=self.fd_std_out)
            os._exit(0)
        pid2 = os.fork()
        if pid2 == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_cmd_out)
            os.close(self.fd_std_in)
            os.close(self.fd_log_in)
            os.close(self.fd_cmd_in)
            os.close(self.stdoutfd)
            self._main(os.fdopen(self.fd_err_in), "err", sys.stderr, dbg=self.fd_err_out)
            os._exit(0)
        pid3 = os.fork()
        if pid3 == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_cmd_out)
            os.close(self.fd_std_in)
            os.close(self.fd_err_in)
            os.close(self.fd_cmd_in)
            os.close(self.stdoutfd)
            self._main(os.fdopen(self.fd_log_in), "log", LOGFILE, dbg=self.fd_log_out)
            os._exit(0)
        pid4 = os.fork()
        if pid4 == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_log_out)
            os.close(self.fd_cmd_out)
            os.close(self.fd_std_in)
            os.close(self.fd_err_in)
            os.close(self.fd_log_in)
            os.close(self.stdoutfd)
            self._main_cmd(os.fdopen(self.fd_cmd_in))
            os._exit(0)
        os.dup2(self.fd_std_out, 1)
        os.dup2(self.fd_err_out, 2)
        os.dup2(self.fd_log_out, 3)
        os.close(self.fd_std_out)
        os.close(self.fd_err_out)
        os.close(self.fd_std_in)
        os.close(self.fd_err_in)
        os.close(self.fd_log_in)
        os.close(self.fd_cmd_in)
        close_on_exec(self.fd_log_out, False)
        close_on_exec(self.fd_cmd_out, False)
        close_on_exec(1, False)
        close_on_exec(2, False)
        os.environ["REDO_LOGFD"] = "%d,%d" % (self.fd_log_out, self.fd_cmd_out)
        os.close(self.logfd)

    def _main(self, f, stamp, sysout=None, stdoutfd=None, dbg=""):
        l = f.readline(1024)
        while len(l):
            os.write(self.logfd, _encode(stamp, l))
            os.fsync(self.logfd)
            if vars.OUTPUT and sysout:
                os.write(sysout.fileno(), l)
                try: os.fsync(sysout.fileno())
                except: pass
            if stdoutfd:
                os.write(stdoutfd, l)
                os.fsync(stdoutfd)
            l = f.readline(1024)

    def _main_cmd(self, f):
        c = f.read(1)
        buf = ""
        z = 0
        while len(c):
            if c == "\0": z += 1
            if z >= 3:
                z = 0
                os.write(self.logfd, buf)
                os.fsync(self.logfd)
                buf = c
            else:
                buf += c
            c = f.read(1)
        os.write(self.logfd, buf)
        os.fsync(self.logfd)

def _flush_redo(t, buf):
    olddepth = vars.DEPTH
    vars.DEPTH = vars.DEPTH + '  '
    try:
        main([os.path.join(t.dirname(), buf)])
    finally:
        vars.DEPTH = olddepth

def _flush_std(t, buf):
    sys.stdout.write(buf)
    sys.stdout.flush()

def _flush_err(t, buf):
    sys.stderr.write(buf)
    sys.stderr.flush()


def _flush_log(t, buf):
    LOGFILE.write(buf)
    LOGFILE.flush()

def _flush_none(f, buf):
    pass

def print_log(t, recursive=False):
    fname  = t.tmpfilename('log')
    flush  = _flush_none
    cmdbuf = ""
    argbuf = ""
    command = False
    with open(fname, "r") as f:
        for line in f:
            for c in line:
                if command:
                    command = (c != "\0")
                    if command:
                        cmdbuf += c
                    elif cmdbuf == "std":
                        flush(t, argbuf)
                        flush, argbuf = _flush_std, ""
                    elif cmdbuf == "err":
                        flush(t, argbuf)
                        flush, argbuf = _flush_err, ""
                    elif cmdbuf == "log" and not recursive:
                        flush(t, argbuf)
                        flush, argbuf = _flush_log, ""
                    elif cmdbuf == "z":
                        argbuf += "\0"
                    elif cmdbuf == "redo" and recursive:
                        flush(t, argbuf)
                        flush, argbuf = _flush_redo, ""
                    else:
                        flush(t, argbuf)
                        flush, argbuf = _flush_none, ""
                else:
                    if c == "\0":
                        cmdbuf = ""
                        command = True
                    else:
                        argbuf += c
    flush(t, argbuf)


def log_cmd(cmd, arg):
    if LOGCMD:
        LOGCMD.write(_encode(cmd, arg))
        LOGCMD.flush()


def main(targets):
    for t in targets:
        f = state.File(name=t)
        l = f.tmpfilename('log')
        if not os.path.exists(l):
            err('%s: no log\n', f.printable_name())
        else:
            log('%s\n', f.printable_name())
            print_log(f, recursive=True)
        if f.exitcode == 0:
            log('%s (done)\n', f.printable_name())
        elif f.exitcode != None:
            err('%s: exit code %d\n', f.printable_name(), f.exitcode)
