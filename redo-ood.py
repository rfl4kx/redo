#!/usr/bin/env python
import sys, os

import build_context
bc = build_context.init(os.environ, sys.argv[0])

import state
from log import err

if len(sys.argv) != 1:
    err('%s: no arguments expected.\n' % sys.argv[0])
    sys.exit(1)


def make_cache():
    _ = {}
    def is_checked(f):
        return _.get(f.id, 0)
    def set_checked(f):
        _[f.id] = 1
    cache = locals().copy()
    del cache['_']
    return cache


for f in state.files():
    if f.is_generated and f.stamp_not_missing():
        if f.is_dirty(max_changed=bc.RUNID, **make_cache()):
            print f.nicename()
