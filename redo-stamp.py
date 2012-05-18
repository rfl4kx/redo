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

if len(sys.argv) > 1:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)

if os.isatty(0):
    err('%s: you must provide the data to stamp on stdin\n' % sys.argv[0])
    sys.exit(1)

import build_context
bc = build_context.init(os.environ, sys.argv[0])
from log import err, debug2

sh = sha()
while 1:
    b = os.read(0, 4096)
    sh.update(b)
    if not b:
        break
csum = sh.hexdigest()

if not bc.target_name():
    sys.exit(0)

f = bc.target_file()
changed = (csum != f.csum)
debug2('%s: old = %s\n' % (f.name, f.csum))
debug2('%s: sum = %s (%s)\n' % (f.name, csum,
                                changed and 'changed' or 'unchanged'))
f.is_generated = True
f.is_override = False
f.failed_runid = None
if changed:
    f.set_changed()  # update_stamp might not do this if the mtime is identical
    f.csum = csum
else:
    # unchanged
    f.set_checked()
f.save()
bc.commit()
