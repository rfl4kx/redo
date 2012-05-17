#!/usr/bin/env python
import sys, os
import build_context

bc = build_context.init(os.environ, *sys.argv)

from log import err


try:
    f = bc.target_file()
    for t in sys.argv[1:]:
        if os.path.exists(t):
            err('redo-ifcreate: error: %r already exists\n' % t)
            sys.exit(1)
        else:
            f.add_dep('c', t)
    bc.commit()
except KeyboardInterrupt:
    sys.exit(200)
