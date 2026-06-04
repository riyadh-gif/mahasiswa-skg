# Line-based TCP link. Works on CPython (Alice) and MicroPython (Bob).
import socket


class Link:
    def __init__(self, conn):
        self.conn = conn
        self.buf = b""

    def sendline(self, s):
        if isinstance(s, str):
            s = s.encode()
        self.conn.sendall(s + b"\n")

    def recvline(self):
        while b"\n" not in self.buf:
            chunk = self.conn.recv(1024)
            if not chunk:
                if self.buf:
                    line, self.buf = self.buf, b""
                    return line.decode()
                return None
            self.buf += chunk
        line, _, self.buf = self.buf.partition(b"\n")
        return line.decode()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def serve(port):
    """Alice: listen, accept one client, return Link."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(1)
    print("Menunggu Bob connect di port %d..." % port)
    conn, addr = s.accept()
    print("Bob terhubung dari", addr[0])
    s.close()
    return Link(conn)


def connect(ip, port, retries=60, delay=0.5):
    """Bob: connect to Alice with retry, return Link."""
    import time
    for _ in range(retries):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, port))
            return Link(s)
        except OSError:
            s.close()
            time.sleep(delay)
    raise RuntimeError("Gagal connect ke %s:%d" % (ip, port))
