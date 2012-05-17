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
from atoi import atoi


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
    return BuildContext(env, state.File, state.commit, state.files)


class BuildContext(object):

    def __init__(self, env, file_class, commit, files):
        self.env = env
        self.file_class = file_class
        self.commit = commit
        self.files = files
        # RUNID is initialized in state.init().
        self.RUNID = atoi(self.env.get('REDO_RUNID')) or None
        assert self.RUNID, repr(self.RUNID)

    def target_full_path(self):
        STARTDIR = self.env['REDO_STARTDIR']
        PWD = self.env['REDO_PWD']
        TARGET = self.env['REDO_TARGET']
        return join(STARTDIR, PWD, TARGET)

    def target_name(self):
        return self.env['REDO_TARGET']

    def target_file(self):
        return self.file_from_name(self.target_full_path())

    def set_unlocked(self):
        self.env['REDO_UNLOCKED'] = '1'

    def unlocked(self):
        return bool(self.env.get('REDO_UNLOCKED'))

    def file_from_name(self, name):
        return self.file_class(name=name)


if __name__ == '__main__':
    import sys
    from pprint import pprint as P
    d = {}
    init(d, sys.argv[0], 'all')
    P(d)
    print
