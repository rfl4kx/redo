#!/usr/bin/env python
import sys, os
# hashlib is only available in python 2.5 or higher, but the 'sha' module
# produces a DeprecationWarning in python 2.6 or higher.  We want to support
# python 2.4 and above without any stupid warnings, so let's try using hashlib
# first, and downgrade if it fails.
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha
from log import err

if len(sys.argv) > 1:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)

if os.isatty(0):
    err('%s: you must provide the data to stamp on stdin\n' % sys.argv[0])
    sys.exit(1)

import build_context
bc = build_context.init(os.environ, sys.argv[0])

sh = sha()
while 1:
    b = os.read(0, 4096)
    sh.update(b)
    if not b:
        break

if not bc.target_name():
    sys.exit(0)

f = bc.target_file()
f.set_csum(sh.hexdigest())
f.save()
bc.commit()
