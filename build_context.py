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
import db
from builder import File
from log import warn
from helpers import atoi


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

    return BuildContext(env)


class BuildContext(object):

    file_class = File
    files = File.files

    def __init__(self, env):
        self.env = env
        self.RUNID = atoi(self.env.get('REDO_RUNID')) or None
        self.BASE = self.env['REDO_BASE']
        db.db(self) # RUNID & REDO_RUNID are set in this call if they
                    # were previously None/undefined.
        assert self.RUNID, repr(self.RUNID)
        self.relpath = db.relpath
        self.DEPTH = self.env.get('REDO_DEPTH', '')
        self.DEBUG = atoi(self.env.get('REDO_DEBUG', ''))
        self.DEBUG_LOCKS = self.env.get('REDO_DEBUG_LOCKS', '') and 1 or 0
        self.DEBUG_PIDS = self.env.get('REDO_DEBUG_PIDS', '') and 1 or 0
        self.OLD_ARGS = self.env.get('REDO_OLD_ARGS', '') and 1 or 0
        self.VERBOSE = self.env.get('REDO_VERBOSE', '') and 1 or 0
        self.XTRACE = self.env.get('REDO_XTRACE', '') and 1 or 0
        self.KEEP_GOING = self.env.get('REDO_KEEP_GOING', '') and 1 or 0
        self.SHUFFLE = self.env.get('REDO_SHUFFLE', '') and 1 or 0
        self.STARTDIR = self.env.get('REDO_STARTDIR', '')
        self.UNLOCKED = self.env.get('REDO_UNLOCKED', '') and 1 or 0
        self.env['REDO_UNLOCKED'] = ''  # not inheritable by subprocesses
        self.NO_OOB = self.env.get('REDO_NO_OOB', '') and 1 or 0
        self.env['REDO_NO_OOB'] = ''    # not inheritable by subprocesses

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
        return self.UNLOCKED

    def file_from_name(self, name):
        return self.file_class(self, name=name)

    def file_from_id(self, id_):
        return self.file_class(self, id=id_)

    def check_sane(self):
        return db.check_sane(self.BASE)

    def commit(self):
        db.commit(self)

    def warn_about_existing_ungenerated(self, targets):
        for t in targets:
            if exists(t):
                f = self.file_from_name(t)
                if not f.is_generated:
                    warn('%s: exists and not marked as generated; not redoing.\n'
                         % f.nicename())



if __name__ == '__main__':
    import sys
    from pprint import pprint as P
    d = {}
    init(d, sys.argv[0], 'all')
    P(d)
    print
