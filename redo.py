#!/usr/bin/env python
import os, sys, shutil, signal

BINARIES = ["redo", "redo-ifchange", "redo-ifcreate"]

if not os.environ.get('REDO_STARTDIR'):
    os.environ['REDO_STARTDIR'] = os.getcwd()
    os.environ['REDO_RUNID_FILE'] = 'runid.redo'
    import runid
    runid.change('runid.redo')

if not os.environ.get('REDO_DIR'):
    from tempfile import mkdtemp
    tmpdir = mkdtemp()
    bindir = os.path.join(tmpdir, "bin")
    os.mkdir(bindir)
    redo = os.path.abspath(__file__)
    os.environ['REDO'] = redo
    os.environ['REDO_DIR'] = tmpdir
    os.environ['PATH'] = bindir + ":" + os.environ['PATH']
    for x in BINARIES:
        os.symlink(redo, os.path.join(bindir, x))

import options
from helpers import atoi

optspec = """
redo [targets...]
--
j,jobs=    maximum number of jobs to build at once
d,debug    print dependency checks as they happen
v,verbose  print commands as they are read from .do files (variables intact)
x,xtrace   print commands as they are executed (variables expanded)
k,keep-going  keep going as long as possible even if some targets fail
shuffle    randomize the build order to find dependency bugs
debug-locks  print messages about file locking (useful for debugging)
debug-pids   print process ids as part of log messages (useful for debugging)
version    print the current version and exit
old-args   use old-style definitions of $1,$2,$3 (deprecated)
overwrite  overwrite targets even if they were not built by redo
"""
o = options.Options(optspec)
(opt, flags, targets) = o.parse(sys.argv[1:])

if opt.version:
    import version
    print version.TAG
    sys.exit(0)
if opt.debug:
    os.environ['REDO_DEBUG'] = str(opt.debug or 0)
if opt.verbose:
    os.environ['REDO_VERBOSE'] = '1'
if opt.xtrace:
    os.environ['REDO_XTRACE'] = '1'
if opt.keep_going:
    os.environ['REDO_KEEP_GOING'] = '1'
if opt.shuffle:
    os.environ['REDO_SHUFFLE'] = '1'
if opt.debug_locks:
    os.environ['REDO_DEBUG_LOCKS'] = '1'
if opt.debug_pids:
    os.environ['REDO_DEBUG_PIDS'] = '1'
if opt.old_args:
    os.environ['REDO_OLD_ARGS'] = '1'
if opt.overwrite:
    os.environ['REDO_OVERWRITE'] = '1'

from log import *
import server

try:
    j = atoi(opt.jobs or 1)
    if j < 1 or j > 1000:
        err('invalid --jobs value: %r\n', opt.jobs)

    if server.has_server():
        sys.exit(server.run_client())
    else:
        srv = server.Peer()
        srv.bind().listen()
        pid = os.fork()
        if pid == 0:  # child
            server.run_server(srv, pid, j)
            shutil.rmtree(os.getenv('REDO_DIR'))
            sys.exit(srv.exit_status or srv.child_status[pid])
        else: # parent
            srv.close()
            res = server.run_client(targets)
            os.kill(pid, signal.SIGTERM)
            sys.exit(res)

except KeyboardInterrupt:
    sys.exit(200)

sys.exit(42)




import sys, os
import options
from helpers import atoi

optspec = """
redo [targets...]
--
j,jobs=    maximum number of jobs to build at once
d,debug    print dependency checks as they happen
v,verbose  print commands as they are read from .do files (variables intact)
x,xtrace   print commands as they are executed (variables expanded)
k,keep-going  keep going as long as possible even if some targets fail
shuffle    randomize the build order to find dependency bugs
debug-locks  print messages about file locking (useful for debugging)
debug-pids   print process ids as part of log messages (useful for debugging)
version    print the current version and exit
old-args   use old-style definitions of $1,$2,$3 (deprecated)
"""
o = options.Options(optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

targets = extra

if opt.version:
    import version
    print version.TAG
    sys.exit(0)
if opt.debug:
    os.environ['REDO_DEBUG'] = str(opt.debug or 0)
if opt.verbose:
    os.environ['REDO_VERBOSE'] = '1'
if opt.xtrace:
    os.environ['REDO_XTRACE'] = '1'
if opt.keep_going:
    os.environ['REDO_KEEP_GOING'] = '1'
if opt.shuffle:
    os.environ['REDO_SHUFFLE'] = '1'
if opt.debug_locks:
    os.environ['REDO_DEBUG_LOCKS'] = '1'
if opt.debug_pids:
    os.environ['REDO_DEBUG_PIDS'] = '1'
if opt.old_args:
    os.environ['REDO_OLD_ARGS'] = '1'

import vars_init
vars_init.init(targets)

import vars, state, builder
from log import warn, err

any_errors = 0
try:
    j = atoi(opt.jobs or 1)
    if j < 1 or j > 1000:
        err('invalid --jobs value: %r\n', opt.jobs)

    targets = state.fix_chdir(targets)
    for t in targets:
        f = state.File(t)
        if os.path.exists(t) and not f.is_generated:
            warn('%s: exists and not marked as generated; not redoing.\n'
                 % f.name)
        retcode = builder.build(t)
        any_errors += retcode
        if retcode and not vars.KEEP_GOING:
            sys.exit(retcode)
except KeyboardInterrupt:
    sys.exit(200)
if any_errors:
    sys.exit(1)
