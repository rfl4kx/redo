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
        debug3("Run %s %s\n", exe, arg)
        res = main.run_main(exe, arg)
        client.send("EXIT=%s=%d" % (val, res))
        sys.exit(res)
    elif var == "X":
      exe = val
    elif var == "ARG":
      arg = val
    elif var == "ENV":
      var, eq, val = val.partition("=")
      if eq: env[var] = val
      else:  env[var] = None

def run_server(server, child_pid, jobs):
  with server as srv:
    if child_pid: srv.add_child_pid(child_pid)
    debug3("Server accept connections\n")
    for client in srv.accept():
      with client as c:
        run_server_instance(server, c, jobs)

def run_client(targets = sys.argv[1:]):
  debug3("Client\n")
  if len(sys.argv[1:]) == 0: return
  if len(targets) == 0:
    targets.append('all')
  if vars.SHUFFLE:
    import random
    random.shuffle(targets)
  with Peer().client() as conn:
    conn.send("X=%s" % os.path.basename(sys.argv[0]))
    i = 1
    for env in vars.ENVIRONMENT:
      if os.getenv(env) == None:
        conn.send("ENV=%s" % env)
      else:
        conn.send("ENV=%s=%s" % (env, os.getenv(env)))
    for arg in targets:
      conn.send("ARG=%s" % os.path.abspath(arg))
      conn.send("RUN=%d" % i)
      i = i + 1
    conn.send("END")
    res = 0
    for buf in conn.recvloop():
      var, eq, val = buf.partition("=")
      if var == "EXIT":
        var, eq, val = val.partition("=")
        val = int(val)
        if val != 0:
          if i == 2: res = val
          else:      res = 1  
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
    length = self.sock.recv(8)
    if length == "":
      return None
    length = int(length, base=16)
    payload = self.sock.recv(length)
    debug3("receive %s\n", payload)
    return payload
  
  def recvloop(self):
    while True:
      payload = self.recv()
      if payload: yield payload
      else:       break

