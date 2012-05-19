import sys, os, errno, glob, stat, fcntl, sqlite3
from helpers import (
    close_on_exec,
    join,
    possible_do_files,
    relpath,
    try_stat,
    unlink,
    )
from log import log, warn, err, debug, debug2, debug3

SCHEMA_VER = 1
TIMEOUT = 60
ALWAYS = '//ALWAYS'   # an invalid filename that is always marked as dirty


def _connect(dbfile):
    _db = sqlite3.connect(dbfile, timeout=TIMEOUT)
    _db.execute("pragma synchronous = off")
    _db.execute("pragma journal_mode = PERSIST")
    _db.text_factory = str
    return _db


_db = None
def db(bc):
    global _db
    if _db:
        return _db

    dbdir = '%s/.redo' % bc.BASE
    dbfile = '%s/db.sqlite3' % dbdir
    try:
        os.mkdir(dbdir)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass  # if it exists, that's okay
        else:
            raise

    must_create = not os.path.exists(dbfile)

    if not must_create:
        _db = _connect(dbfile)
        try:
            row = _db.cursor().execute("select version from Schema").fetchone()
        except sqlite3.OperationalError:
            row = None
        ver = row and row[0] or None
        if ver != SCHEMA_VER:
            err("state database: discarding v%s (wanted v%s)\n"
                % (ver, SCHEMA_VER))
            must_create = True
            _db = None

    if must_create:
        unlink(dbfile)
        _db = _connect(dbfile)
        _db.execute("create table Schema "
                    "    (version int)")
        _db.execute("create table Runid "
                    "    (id integer primary key autoincrement)")
        _db.execute("create table Files "
                    "    (name not null primary key, "
                    "     is_generated int, "
                    "     is_override int, "
                    "     checked_runid int, "
                    "     changed_runid int, "
                    "     failed_runid int, "
                    "     stamp, "
                    "     csum)")
        _db.execute("create table Deps "
                    "    (target int, "
                    "     source int, "
                    "     mode not null, "
                    "     delete_me int, "
                    "     primary key (target,source))")
        _db.execute("insert into Schema (version) values (?)", [SCHEMA_VER])
        # eat the '0' runid and File id
        _db.execute("insert into Runid values "
                    "     ((select max(id)+1 from Runid))")
        _db.execute("insert into Files (name) values (?)", [ALWAYS])

    if not bc.RUNID:
        _db.execute("insert into Runid values "
                    "     ((select max(id)+1 from Runid))")
        bc.RUNID = _db.execute("select last_insert_rowid()").fetchone()[0]
        os.environ['REDO_RUNID'] = str(bc.RUNID)
    
    _db.commit()
    return _db
    

_wrote = 0
def _write(bc, q, l):
    if _insane:
        return
    global _wrote
    _wrote += 1
    db(bc).execute(q, l)


def commit(bc):
    if _insane:
        return
    global _wrote
    if _wrote:
        db(bc).commit()
        _wrote = 0


_insane = None
def check_sane(BASE):
    global _insane, _writable
    if not _insane:
        _insane = not os.path.exists('%s/.redo' % (BASE,))
    return not _insane


_file_cols = ['rowid', 'name', 'is_generated', 'is_override',
              'checked_runid', 'changed_runid', 'failed_runid',
              'stamp', 'csum']
class FileDBMixin(object):
    # use this mostly to avoid accidentally assigning to typos
    __slots__ = ['id', 't'] + _file_cols[1:]

    def __init__(self, id=None, name=None, cols=None):
        if cols:
            self._init_from_cols(cols)
        else:
            self._init_from_idname(id, name)
            self.t = name or self.name

    def _init_from_idname(self, id, name):
        q = ('select %s from Files ' % join(', ', _file_cols))
        if id != None:
            q += 'where rowid=?'
            l = [id]
        elif name != None:
            global _bc
            name = (name==ALWAYS) and ALWAYS or relpath(name, self.bc.BASE)
            q += 'where name=?'
            l = [name]
        else:
            raise Exception('name or id must be set')
        d = db(self.bc)
        row = d.execute(q, l).fetchone()
        if not row:
            if not name:
                raise Exception('File with id=%r not found and '
                                'name not given' % id)
            try:
                _write(self.bc, 'insert into Files (name) values (?)', [name])
            except sqlite3.IntegrityError:
                # some parallel redo probably added it at the same time; no
                # big deal.
                pass
            row = d.execute(q, l).fetchone()
            assert row
        return self._init_from_cols(row)

    def _init_from_cols(self, cols):
        (self.id, self.name, self.is_generated, self.is_override,
         self.checked_runid, self.changed_runid, self.failed_runid,
         self.stamp, self.csum) = cols
        if self.name == ALWAYS and self.changed_runid < self.bc.RUNID:
            self.changed_runid = self.bc.RUNID
    
    def save(self):
        cols = join(', ', ['%s=?'%i for i in _file_cols[2:]])
        _write(self.bc, 'update Files set '
               '    %s '
               '    where rowid=?' % cols,
               [self.is_generated, self.is_override,
                self.checked_runid, self.changed_runid, self.failed_runid,
                self.stamp, self.csum,
                self.id])

    def add_dep(self, mode, dep):
        src = self.__class__(self.bc, name=dep)
        debug3('add-dep: "%s" < %s "%s"\n' % (self.name, mode, src.name))
        assert self.id != src.id
        _write(self.bc, "insert or replace into Deps "
               "    (target, mode, source, delete_me) values (?,?,?,?)",
               [self.id, mode, src.id, False])

    def _deps(self):
        q = ('select Deps.mode, Deps.source, %s '
             '  from Files '
             '    join Deps on Files.rowid = Deps.source '
             '  where target=?' % join(', ', _file_cols[1:]))
        for row in db(self.bc).execute(q, [self.id]).fetchall():
            mode = row[0]
            cols = row[1:]
            assert mode in ('c', 'm')
            yield mode, self.__class__(self.bc, cols=cols)

    def _zap_deps1(self):
        debug2('zap-deps1: %r\n' % self.name)
        _write(self.bc, 'update Deps set delete_me=? where target=?', [True, self.id])

    def _zap_deps2(self):
        debug2('zap-deps2: %r\n' % self.name)
        _write(self.bc, 'delete from Deps where target=? and delete_me=1', [self.id])

    @classmethod
    def files(class_):
        q = ('select %s from Files order by name' % join(', ', _file_cols))
        for cols in db(self.bc).execute(q).fetchall():
            yield class_(cols=cols)
