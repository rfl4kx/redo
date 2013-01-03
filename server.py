from log import *
import vars, main
import socket, sys, os, signal, errno

def socketfile():
  return os.path.join(os.getenv('REDO_DIR'), "socket")

def has_server():
  return os.path.exists(socketfile())

def run_server_instance(server, client, jobs):
  exe = "redo"
  arg = None
  env = {}
  csum_in = None
  keep_going = vars.KEEP_GOING
  for buf in client.recvloop():
    var, eq, val = buf.partition("=")
    if buf == "END":
      return
    elif var == "RUN":
      pid = os.fork()
      if pid == 0: # child
        for k in env:
          try:
            if env[k] == None: del os.environ[k]
            else:              os.environ[k] = env[k]
          except: pass
        reload(vars)
        debug3("Run %s %s\n", exe, arg)
        res = main.run_main(exe, arg, csum_in)
        client.send("EXIT=%s=%d" % (val, res))
        sys.exit(res)
      else:
        pid2, status = os.waitpid(pid, 0)
        if pid2 == pid and status != 0 and not keep_going:
          client.send("END")
          return
    elif var == "X":
      exe = val
    elif var == "ARG":
      arg = val
    elif var == "ENV":
      var, eq, val = val.partition("=")
      if not eq: env[var] = None
      else:
        env[var] = val
        if var == "REDO_KEEP_GOING":
          keep_going = int(val)
    elif var == "CSUMIN":
      csum_in = val

def run_server(server, child_pid, jobs):
  with server as srv:
    if child_pid: srv.add_child_pid(child_pid)
    debug3("Server accept connections\n")
    for client in srv.accept():
      with client as c:
        pid = os.fork()
        if pid == 0:
          run_server_instance(server, c, jobs)

def run_client(targets = sys.argv[1:]):
    debug3("Client\n")
    exe = os.path.basename(sys.argv[0])
    return_values = []

    if exe == "redo-stamp":
        if len(targets) > 1:
            err('%s: no arguments expected.\n', exe)
            return 1

        if os.isatty(0):
            err('%s: you must provide the data to stamp on stdin\n', exe)
            return 1

        try:
            import hashlib
        except ImportError:
            import sha
            sh = sha.sha()
        else:
            sh = hashlib.sha1()

    if vars.SHUFFLE:
        import random
        random.shuffle(targets)

    with Peer().client() as conn:
        conn.send("X=%s" % exe)
        conn.send("KEEP_GOING=%d" % vars.KEEP_GOING)

        for env in vars.ENVIRONMENT:
            if os.getenv(env) == None:
                conn.send("ENV=%s" % env)
            else:
                conn.send("ENV=%s=%s" % (env, os.getenv(env)))

        if exe == "redo-stamp":
            while True:
                b = os.read(0, 4096)
                sh.update(b)
                if not b: break
            conn.send("CSUMIN=%s" % sh.hexdigest())
            conn.send("RUN=1")
            conn.send("END")
        else:
            i = 1
            for arg in targets:
                conn.send("ARG=%s" % os.path.abspath(arg))
                conn.send("RUN=%d" % i)
                i = i + 1
            conn.send("END")

        for buf in conn.recvloop():
            var, eq, val = buf.partition("=")
            if var == "EXIT":
                var, eq, val = val.partition("=")
                val = int(val)
                return_values.append(val)

    if len(return_values) == 1:
        res = return_values[0]
    elif len([i for i in return_values if i != 0]) > 0:
        res = 1
    else:
        res = 0

    debug3("Client exit %d\n", res)
    return res

class Peer:
  def __init__(self, sockfile=None, sock=None):
    if sockfile:
      self.sockfile = sockfile
    else:
      self.sockfile = socketfile()
    if sock:
      self.sock = sock
    else:
      self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  
  def bind(self, listen_queue=1):
    self.sock.bind(self.sockfile)
    return self

  def listen(self, listen_queue=1):
    self.sock.listen(listen_queue)
    return self

  def client(self):
    self.sock.connect(self.sockfile)
    return self
  
  def __enter__(self):
    return self
  
  def __exit__(self, type, value, traceback):
    self.close()
  
  def close(self):
    self.sock.close()
    
  def accept(self):
    signal.siginterrupt(signal.SIGTERM, True)
    while True:
      try:
        conn, addr = self.sock.accept()
        yield Peer(sockfile=self.sockfile, sock=conn)
      except IOError as e:
        if e.errno != errno.EINTR: raise
        else:                      break
  
  def send(self, payload):
    debug3("send %s\n", payload)
    self.sock.send("%08x%s" % (len(payload), payload))

  def recv(self):
    try:
        length = self.sock.recv(8)
        if length == "": return None
        length = int(length, base=16)
        payload = self.sock.recv(length)
        debug3("receive %s\n", payload)
        return payload
    except:
        return None
  
  def recvloop(self):
    while True:
      payload = self.recv()
      if payload: yield payload
      else:       break

