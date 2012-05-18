#!/usr/bin/env python
import sys, os
from log import err
import build_context


if len(sys.argv) != 1:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)


for f in build_context.init(os.environ, sys.argv[0]).files():
    if f.is_generated and f.stamp_not_missing():
        print f.nicename()
