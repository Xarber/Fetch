# SPDX-License-Identifier: AGPL-3.0-only
"""DNS-pinned egress proxy: validate every HTTP target and CONNECT tunnel."""
import hashlib
import http.client
import ipaddress
import re
import select
import socket
import socketserver
import threading
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit
from .config import SOURCE_HOSTS, STORE_MODE, TEST_ORIGIN

class UnsafeURL(ValueError):
    pass

def validate_url(url, source=True):
    if len(url) > 8192 or any(ord(c) < 32 for c in url) or '\\' in url:
        raise UnsafeURL('Invalid URL')
    try:
        p = urlsplit(url)
        host = p.hostname
        port = p.port or (443 if p.scheme == 'https' else 80)
    except ValueError as e:
        raise UnsafeURL('Invalid URL') from e
    if p.scheme not in ('http','https') or not host or p.username or p.password:
        raise UnsafeURL('Use an HTTP(S) URL without embedded credentials')
    if source and ((SOURCE_HOSTS and host.lower() not in SOURCE_HOSTS) or (STORE_MODE and host.lower() not in SOURCE_HOSTS)):
        raise UnsafeURL('Source is not authorized by this server')
    resolve(host, port)
    return url

def resolve(host, port):
    if TEST_ORIGIN and f'{host}:{port}' == TEST_ORIGIN:
        return [('127.0.0.1', socket.AF_INET)]
    if port not in (80,443):
        raise UnsafeURL('Only public HTTP ports 80 and 443 are permitted')
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as e:
        raise UnsafeURL('Hostname could not be resolved') from e
    result = []
    for family, _, _, _, address in addresses:
        ip = ipaddress.ip_address(address[0])
        if not ip.is_global or ip.is_multicast or (ip.version == 6 and ip.ipv4_mapped and not ip.ipv4_mapped.is_global):
            raise UnsafeURL('Private, reserved and internal network destinations are blocked')
        result.append((str(ip), family))
    if not result:
        raise UnsafeURL('No public address')
    return result

def pinned_socket(host, port):
    # Never resolve the hostname a second time between validation and connection.
    for ip, family in resolve(host, port):
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(20)
        try:
            sock.connect((ip, port))
            return sock
        except OSError:
            sock.close()
    raise UnsafeURL('Destination unavailable')

class ProxyHandler(BaseHTTPRequestHandler):
    timeout = 30
    def log_message(self, *args): pass
    def do_CONNECT(self):
        try:
            p = urlsplit('https://' + self.path)
            if p.username or p.password or not p.hostname:
                raise UnsafeURL('Invalid tunnel')
            upstream = pinned_socket(p.hostname, p.port or 443)
        except (ValueError,OSError):
            self.send_error(403, 'Destination blocked'); return
        self.send_response(200); self.end_headers()
        self.close_connection = True
        with upstream:
            sockets = [self.connection, upstream]
            while True:
                readable, _, _ = select.select(sockets, [], [], 30)
                if not readable: return
                for src in readable:
                    data = src.recv(65536)
                    if not data: return
                    (upstream if src is self.connection else self.connection).sendall(data)
    def do_GET(self): self.forward()
    def do_HEAD(self): self.forward()
    def do_POST(self): self.forward()
    def forward(self):
        try:
            validate_url(self.path, source=False)
            p = urlsplit(self.path)
            upstream = pinned_socket(p.hostname, p.port or 80)
            if p.scheme != 'http':
                upstream.close(); raise UnsafeURL('Use CONNECT for TLS')
        except (ValueError,OSError):
            self.send_error(403, 'Destination blocked'); return
        self.close_connection = True
        with upstream:
            path = p.path or '/'
            if p.query: path += '?' + p.query
            headers = {k:v for k,v in self.headers.items() if k.lower() not in ('connection','proxy-connection','proxy-authorization','transfer-encoding','host')}
            headers['Host'] = p.netloc
            headers['Connection'] = 'close'
            length = int(headers.get('Content-Length','0'))
            if length > 1024*1024: self.send_error(413); return
            request = f'{self.command} {path} HTTP/1.1\r\n' + ''.join(f'{k}: {v}\r\n' for k,v in headers.items()) + '\r\n'
            upstream.sendall(request.encode('latin1'))
            if length: upstream.sendall(self.rfile.read(length))
            while data := upstream.recv(65536): self.connection.sendall(data)

class Proxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

def start_proxy():
    server = Proxy(('127.0.0.1',0), ProxyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f'http://127.0.0.1:{server.server_address[1]}'

def digest(secret): return hashlib.sha256(secret.encode()).hexdigest()

def safe_name(name):
    name = re.sub(r'[^\w .()-]', '_', name, flags=re.UNICODE).strip(' .')[:100]
    return name or 'media'
