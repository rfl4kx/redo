import vars, state, builder, deps
from log import debug, debug2, err


def should_build(f):
    if f.stamp_mtime == 0:
        expect_stamp = state.Stamp()
    else:
        expect_stamp = f.stamp
    dirty = deps.isdirty(f, depth='', expect_stamp=expect_stamp)
    return dirty==[f] and deps.DIRTY or dirty

