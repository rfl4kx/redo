from log import *
import vars, main
import socket, sys, os, signal, errno

def socketfile():
  return os.path.join(os.environ['REDO_DIR'], "socket")

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
      debug3("Run %s %s\n", exe, arg)
      pid = os.fork()
      if pid == 0: # child
        for e in env:
          try:
            if env[e] == None: del os.environ[e]
            else:              os.environ[e] = env[e]
          except: pass
        res = main.run_main(exe, arg)
        client.send("EXIT=%s=%d" % (val, res))
        sys.exit(res)
      else:
        server.add_child_pid(pid)
        #if len(server.child_pids) > jobs:
        #  try:
        #    pid, exit = os.waitpid(pid, 0)
        #    server._register_child_status(pid, exit)
        #  except OSError as e:
        #    if e.errno != errno.ECHILD: raise
        
    elif var == "X":
      exe = val
    elif var == "ARG":
      arg = val
    elif var == "ENV":
      var, eq, val = val.partition("=")
      if eq: env[var] = val
      else:  env[var] = None

def run_server(server, child_pid, jobs):
  with server.listen() as srv:
    if child_pid: srv.add_child_pid(child_pid)
    debug3("Server accept connections\n")
    for client in srv.accept():
      with client as c:
        #pid = os.fork()
        #if pid == 0: # child
        #  debug3("Server child process\n")
        #  run_server_instance(c)
        #  debug3("Server child process exit\n")
        #  sys.exit(0)
        #else: # parent
        #  srv.add_child_pid(pid)
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
      if env in os.environ:
        conn.send("ENV=%s=%s" % (env, os.environ[env]))
      else:
        conn.send("ENV=%s" % env)
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
    self.child_pids = []
    self.child_status = {}
    self.exit_status = 0
  
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
    
  def _receive_sigchld(self, x, y):
    try:
      pid, exit = os.waitpid(0, os.WNOHANG)
      debug3("Received SIGCHLD for %d (exit status: %d)\n", pid, exit)
    except OSError as e:
      if e.errno != errno.ECHILD: raise
  
  def _register_child_status(self, pid, exit):
    debug3("Received SIGCHLD for %d (exit status: %d)\n", pid, exit)
    self.child_status[pid] = exit
    if pid in self.child_pids:
      self.child_pids.remove(pid)
      if exit and not vars.KEEP_GOING: self.exit_status = 1
  
  def accept(self):
    signal.signal(signal.SIGCHLD, self._receive_sigchld)
    signal.siginterrupt(signal.SIGCHLD, True)
    while True:
      try:
        # Be careful, there might be a race to accept() in Python runtime
        # - the python accept function is executed
        # - this locks signal handlers until the end of the C function
        # - before the accept() syscall is executed, a child dies
        # - the SIGCHLD handler is blocked by the Python lock with no chance
        #   of recovering
        conn, addr = self.sock.accept()
        yield Peer(sockfile=self.sockfile, sock=conn)
      except IOError as e:
        if e.errno != errno.EINTR: raise
        if len(self.child_pids) == 0: break
        if self.exit_status: break
  
  def send(self, payload):
    debug3("send %s\n", payload)
    self.sock.send("%08x%s" % (len(payload), payload))
  
  def _recv(self, len):
    while True:
      try:
        return self.sock.recv(len)
      except IOError as e:
        if e.errno != errno.EINTR: raise      
  
  def recv(self):
    length = self._recv(8)
    if length == "":
      return None
    length = int(length, base=16)
    payload = self._recv(length)
    debug3("receive %s\n", payload)
    return payload
  
  def recvloop(self):
    while True:
      payload = self.recv()
      if payload: yield payload
      else:       break
  
  def add_child_pid(self, pid):
    if pid not in self.child_status:
      self.child_pids.append(pid)
    elif self.child_status[pid] and not vars.KEEP_GOING:
      self.exit_status = 1


