#!/usr/bin/env python
import sys, os

import build_context
bc = build_context.init(os.environ, sys.argv[0])

from log import err

if len(sys.argv) != 1:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)

for f in bc.files():
    if not (f.special() or f.is_generated) and f.stamp_not_missing():
        print f.nicename()
