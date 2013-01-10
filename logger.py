import os, sys
import vars, state
from log import log, err

class Logger:
    def __init__(self, logfd, stdoutfd):
        self.stdoutfd = stdoutfd
        self.logfd    = logfd
        self.fd_std_in, self.fd_std_out = os.pipe()
        self.fd_err_in, self.fd_err_out = os.pipe()

    def fork(self):
        pid = os.fork()
        if pid == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_err_in)
            self._std_main(os.fdopen(self.fd_std_in))
            os._exit(0)
        pid2 = os.fork()
        if pid2 == 0:
            os.close(self.fd_std_out)
            os.close(self.fd_err_out)
            os.close(self.fd_std_in)
            os.close(self.stdoutfd)
            self._err_main(os.fdopen(self.fd_err_in))
            os._exit(0)
        os.dup2(self.fd_std_out, 1)
        os.dup2(self.fd_err_out, 2)
        os.close(self.fd_std_in)
        os.close(self.fd_err_in)
        os.close(self.fd_std_out)
        os.close(self.fd_err_out)
        os.close(self.logfd)
        
    def _encode(self, stamp, line):
        return "\0%s\0%s" % (stamp, line.replace("\0", "\0z\0"))

    def _std_main(self, f):
        l = f.readline(1024)
        while len(l):
            os.write(self.logfd, self._encode("std", l))
            os.write(self.stdoutfd, l)
            if vars.OUTPUT: 
                sys.stdout.write(l)
            l = f.readline(1024)
        sys.stdout.flush()
        os.fsync(self.logfd)
        os.fsync(self.stdoutfd)

    def _err_main(self, f):
        l = f.readline(1024)
        while len(l):
            os.write(self.logfd, self._encode("err", l))
            if vars.OUTPUT: 
                sys.stderr.write(l)
            l = f.readline(1024)
        sys.stderr.flush()
        os.fsync(self.logfd)

def print_log(fname):
    f = sys.stdout
    cmdbuf = ""
    command = False
    with open(fname, "r") as f:
        for line in f:
            for c in line:
                if command:
                    command = (c != "\0")
                    if command:
                        cmdbuf += c
                    elif cmdbuf == "std":
                        f = sys.stdout
                    elif cmdbuf == "err":
                        f = sys.stderr
                    elif cmdbuf == "z":
                        f.write("\0")
                else:
                    if c == "\0":
                        cmdbuf = ""
                        command = True
                    else:
                        f.write(c)

def main(targets):
    for t in targets:
        f = state.File(name=t)
        l = f.tmpfilename('log')
        if not os.path.exists(l):
            err('%s: no log\n', f.printable_name())
        else:
            log('%s\n', f.printable_name())
            print_log(l)
        if f.exitcode == 0:
            log('%s (done)\n', f.printable_name())
        elif f.exitcode != None:
            err('%s: exit code %d\n', f.printable_name(), f.exitcode)
