#!/usr/bin/env python
import sys, os
import build_context
from builder import ALWAYS, STAMP_MISSING
from log import err


bc = build_context.init(os.environ, sys.argv[0])


try:
    f = bc.target_file()
    f.add_dep('m', ALWAYS)
    always = bc.file_from_name(ALWAYS)
    always.stamp = STAMP_MISSING
    always.set_changed()
    always.save()
    bc.commit()
except KeyboardInterrupt:
    sys.exit(200)
