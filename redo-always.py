#!/usr/bin/env python
import sys, os
import vars, builder
from log import err


try:
    me = os.path.join(vars.STARTDIR, 
                      os.path.join(vars.PWD, vars.TARGET))
    f = builder.File(name=me)
    f.add_dep('m', builder.ALWAYS)
    always = builder.File(name=builder.ALWAYS)
    always.stamp = builder.STAMP_MISSING
    always.set_changed()
    always.save()
    builder.commit()
except KeyboardInterrupt:
    sys.exit(200)
