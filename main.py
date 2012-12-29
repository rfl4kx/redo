import vars, builder, state, deps
from log import *

def _chdir():
    os.chdir(os.path.join(vars.STARTDIR, vars.PWD))

def _should_build(t):
    f = state.File(t)
    if f.stamp_mtime >= vars.RUNID and f.exitcode:
        raise Exception('earlier build of %r failed with code %d'
                        % (f.name, f.exitcode))
    if f.stamp_mtime == 0:
        expect_stamp = None
    else:
        expect_stamp = f.csum or f.stamp
    dirty = deps.isdirty(f, depth='', expect_stamp=expect_stamp,
                         max_runid=vars.RUNID)
    return dirty==[f] and deps.DIRTY or dirty


def build_ifchanged(sf):
    dirty = _should_build(sf.name)
    while dirty and dirty != deps.DIRTY:
        # FIXME: bring back the old (targetname) notation in the output
        #  when we need to do this.  And add comments.
        for t2 in dirty:
            rv = build_ifchanged(t2)
            if rv:
                return rv
        dirty = _should_build(sf.name)
        #assert(dirty in (deps.DIRTY, deps.CLEAN))
    if dirty:
        rv = builder.build(sf.name)
        if rv:
            return rv
    return 0

def redo(f):
    "f: absolute target pathname"
    _chdir()
    sf = state.File(f)
    if os.path.exists(f) and not sf.is_generated and not vars.OVERWRITE:
        warn('%s: exists and not marked as generated; not redoing.\n'
             % sf.name)
    return builder.build(f)

def redo_ifchange(f):
    "f: absolute target pathname"
    _chdir()
    
    # Add dependency
    if vars.TARGET:
        st = state.File(name=vars.TARGET)
        debug2('TARGET: %r %r %r\n', vars.STARTDIR, vars.PWD, vars.TARGET)
    else:
        st = None
        debug2('redo-ifchange: no target - not adding depends.\n')

    sf = state.File(name=f)
    retcode = build_ifchanged(sf)
    if st:
        sf.refresh()
        st.add_dep(sf)
    return retcode

def redo_ifcreate(f):
    "f: absolute target pathname"

    st = state.File(vars.TARGET)
    if os.path.exists(f):
        err('redo-ifcreate: error: %r already exists\n', f)
        # It would be nice to call redo-ifchange then
        return 1
    else:
        st.add_dep(state.File(name=f))
        return 0

def run_main(exe, arg):
    if exe == "redo-ifchange":
        return redo_ifchange(arg)
    if exe == "redo-ifcreate":
        return redo_ifcreate(arg)
    else:
        return redo(arg)

