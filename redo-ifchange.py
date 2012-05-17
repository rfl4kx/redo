#!/usr/bin/env python
import sys, os

import build_context
bc = build_context.init(os.environ, *sys.argv)

import vars, state, builder, jwack
from helpers import unlink
from log import debug, debug2, err

def should_build(t):
    f = state.File(name=t)
    if f.is_failed():
        raise builder.ImmediateReturn(32)
    dirty = f.is_dirty(max_changed=bc.RUNID)
    return dirty==[f] and state.DIRTY or dirty

targets = sys.argv[1:]

rv = 202
try:
    if vars.TARGET and not bc.unlocked():
        f = state.File(name=bc.target_name())
        for t in targets:
            f.add_dep('m', t)
        f.save()
        debug2('TARGET: %r %r %r\n' % (vars.STARTDIR, vars.PWD, vars.TARGET))
    else:
        debug2('redo-ifchange: not adding depends.\n')
    try:
        rv = builder.main(targets, should_build)
    finally:
        jwack.force_return_tokens()
except KeyboardInterrupt:
    sys.exit(200)
state.commit()
sys.exit(rv)
