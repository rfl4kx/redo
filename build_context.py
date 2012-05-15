from os import getcwd
from os.path import (
    abspath,
    realpath,
    dirname,
    commonprefix,
    exists,
    join,
    split,
    )


def toplevel(env):
    '''Return True is this is a toplevel call to redo'''
    return 'REDO' not in env


def get_paths(exename):
    '''Return a list of possible paths for PATH from an executable.'''
    abs_dir = dirname(abspath(exename))
    real_dir = dirname(realpath(exename))
    paths = _make_paths_from(abs_dir)
    if real_dir != abs_dir:
        paths.extend(_make_paths_from(real_dir))
    return paths


def _make_paths_from(path):
    return [abspath(join(path, '../lib/redo')),
            join(path, 'redo-sh'),
            path]


def add_dirs_to_PATH(dirs, env):
    PATH = env.get('PATH')
    if PATH:
        dirs.append(PATH)
    env['PATH'] = ':'.join(dirs)


def common_base(cwd, targets):
    bases = [abspath(dirname(t)) for t in targets]
    bases.append(cwd)
    return commonprefix(bases)


def find_redo_root(base):
    '''
    Given a directory path look for a .redo dir in that directory and
    its ancestors. Return the directory path containing the .redo dir or
    the original base path if the .redo dir is absent.
    '''
    newbase = base
    while True:
        if exists(join(newbase, '.redo')):
            return newbase
        newbase, head = split(newbase)
        if not head:
            return base


def init(env, exename, *targets):
    if toplevel(env):

        add_dirs_to_PATH(get_paths(exename), env)

        env['REDO'] = abspath(exename)
        env['REDO_STARTDIR'] = cwd = getcwd()
        env['REDO_BASE'] = find_redo_root(common_base(cwd, targets))

        import state
        state.init()



if __name__ == '__main__':
    import sys
    from pprint import pprint as P
    d = {}
    init(d, sys.argv[0], 'all')
    P(d)
    print
