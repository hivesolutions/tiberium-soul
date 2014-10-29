#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Tiberium System
# Copyright (C) 2008-2014 Hive Solutions Lda.
#
# This file is part of Hive Tiberium System.
#
# Hive Tiberium System is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hive Tiberium System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hive Tiberium System. If not, see <http://www.gnu.org/licenses/>.

__author__ = "João Magalhães <joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2014 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import os
import ssl
import sys
import socket
import select
import threading

import quorum

BUFFER_SIZE = 4096
""" The size of the buffer to be used in the various
read and writes requests to be performed """

AGENT = "Tiberium Proxy/" + __version__
""" The agent string value to be used
while serving the proxy requests """

HTTP_VERSION = "HTTP/1.1"
""" The version of the http protocol to be used
while serving the proxy requests """

SELECT_TIMEOUT = 1.0
""" The timeout to be used in the server select timeout
this value must be low so that a signal is handled in
a sufficient short time (rapid response) """

DEFAULT_HOST = "admin"
""" The default host value to be used for situations
where there's no host header available """

class ConnectionHandler(threading.Thread):
    """
    The thread based class meant to be used
    in a per connection basis, each connection
    has its own thread for handling.
    """

    def __init__(self, connection, address, timeout, current):
        threading.Thread.__init__(self)

        self.client = connection
        self.client_buffer = ""
        self.target = None
        self.timeout = timeout
        self.current = current

    def run(self):
        try:
            # iterates continuously to handle the various request provided
            # from the current client connection
            while True:
                self.method, self.path, self.protocol = self.get_base_header()
                self._client_buffer = self.client_buffer
                self.headers = self.get_headers()

                if self.method == "CONNECT":
                    self.method_CONNECT()
                elif self.method in ("OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE"):
                    self.method_others()
        except BaseException, exception:
            try: self.client.send("Problem in routing - %s" % str(exception))
            except BaseException, exception: print >> sys.stderr, " [error] - %s" % str(exception)
        else:
            if self.target: self.target.close()
        finally:
            if self.client: self.client.close()

    def get_base_header(self):
        while True:
            end = self.client_buffer.find("\r\n")
            if not end == -1: break
            data = self.client.recv(BUFFER_SIZE)
            if not data: raise RuntimeError("Problem in connection (dropped)")
            self.client_buffer += data

        data = (self.client_buffer[:end]).split()
        self.client_buffer = self.client_buffer[end + 2:]
        return data

    def get_headers(self):
        while True:
            end = self.client_buffer.find("\r\n\r\n")
            if not end == -1: break
            data = self.client.recv(BUFFER_SIZE)
            if not data: raise RuntimeError("Problem in connection (dropped)")
            self.client_buffer += data

        lines = self.client_buffer[:end].split("\r\n")

        headers = {}

        for line in lines:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            headers[key] = value

        return headers

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTP_VERSION + " 200 Connection established\n" + "Proxy-agent: %s\r\n\r\n" % AGENT)
        self.client_buffer = ""
        self._read_write()

    def method_others(self):
        target, path = self._resolve_target()
        self._connect_target(target)

        self.target.send("%s %s %s\r\n" % (self.method, path, self.protocol) + self._client_buffer)
        self.client_buffer = ""
        self._read_write()

    def _resolve_target(self):
        # retrieves the reference to the storage engine
        # consisting of a redis data source
        storage = quorum.get_redis()

        # sets the path to the target connection as the
        # "just" set path or the root value in case no
        # value is set
        path = self.path or "/"

        # retrieves the host header value from the map
        # or headers and tries to resolve it as an alias
        # defaulting to the value itself then retrieves
        # the first part of the resolved value as the name
        # of the app to be used in connection
        host = self.headers.get("Host", DEFAULT_HOST)
        host = storage and storage.get("alias:" + host) or host
        host_s = host.split(".", 1)
        name = host_s[0]

        # tries to retrieves the process information from the
        # current (in memory) data structure, in case no process
        # type is found raises an exception (no routing possible)
        process_t = self.current.get(name, None)
        if not process_t: raise RuntimeError("No process available for request (%s)" % name)

        # unpacks the process tuple into the process temporary path
        # and port information then uses it to construct the final
        # target value for connection
        _process, _temp_path, port = process_t
        target = "localhost:" + str(port)
        return target, path

    def _connect_target(self, host):
        # in case there's current an existing target connection
        # it must be closed before "advancing" to a new one
        if self.target: self.target.close()

        # tries to find the port character separator in case it's
        # found retrieves the port value from it, otherwise used
        # the default port
        index = host.find(":")
        if not index == -1:
            port = int(host[index + 1:])
            host = host[:index]
        else:
            port = 80

        # creates the socket for the target host and connects to
        # it, creating a valid and ready socket
        self.target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.target.connect((host, port))

    def _read_write(self):
        time_out_max = self.timeout / 3
        socs = [self.client, self.target]
        count = 0
        while True:
            count += 1
            recv, _, error = select.select(socs, [], socs, 3)

            if error: break

            if recv:
                for in_ in recv:
                    data = in_.recv(BUFFER_SIZE)
                    if in_ is self.client: out = self.target
                    else: out = self.client

                    if not data: continue

                    out.send(data)
                    count = 0

            if count == time_out_max: break

class ProxyServer(threading.Thread):
    """
    The thread bases class that serves as the main
    entry point for the proxy server used in the
    tiberium.

    Its main responsibilities are: handling of new
    connections and forwarding of data.
    """

    current = None
    """ The global state related values to be passed across
    the various handling operations in the proxy server, this
    map should contain various options including the various
    instances to be used in the proxy """

    cert_path = None
    """ The default path to the certificate file to be used
    for ssl based connections """

    key_path = None
    """ The default path to the (private) key file to be used
    for ssl based connections """

    executing = True
    """ The flag that controls the continuous execution
    of the proxy server, if unset the proxy handling stops """

    def __init__(self, current, cert_path = None, key_path = None):
        threading.Thread.__init__(self)

        self.current = current
        self.cert_path = cert_path
        self.key_path = key_path

    def run(self):
        self.start_server(
            cert_path = self.cert_path,
            key_path = self.key_path
        )

    def stop(self):
        self.stop_server()

    def start_server(
        self,
        host = "0.0.0.0",
        port = 80,
        port_ssl = 443,
        use_ssl = True,
        cert_path = None,
        key_path = None,
        timeout = 60,
        handler = ConnectionHandler
    ):
        # creates the list that will hold the various sockets
        # to be used in the server
        sockets = []

        # creates the various certificate and key file paths for
        # the usage on the ssl based connections
        base_path = os.path.dirname(__file__)
        cert_path = cert_path or os.path.join(base_path, "cert", "dummy.crt")
        key_path = key_path or os.path.join(base_path, "cert", "dummy.key")

        # creates the (internet) socket for the service and binds
        # it to the required host and port
        _socket = socket.socket(socket.AF_INET)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _socket.bind((host, port))
        sockets.append(_socket)

        # in case the current connection should also use ssl a new socket
        # should be created for such connections
        if use_ssl:
            _socket_ssl = socket.socket(socket.AF_INET)
            _socket_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            _socket_ssl.bind((host, port_ssl))
            sockets.append(_socket_ssl)

        # creates the hostname string value taking into account if the
        # provided port is the default one for the connection, then
        # prints the information on the hostname binding
        hostname = not port == 80 and host + ":" + str(port) or host
        hostname_ssl = not port_ssl == 443 and host + ":" + str(port_ssl) or host
        print >> sys.stderr, " * Running proxy on http://%s/" % hostname
        if use_ssl: print >> sys.stderr, " * Running proxy on https://%s/" % hostname_ssl

        # starts listening in the socket for the various connections to
        # be received in the current proxy
        _socket.listen(0)
        use_ssl and _socket_ssl.listen(0)

        # iterates continuously, while the executing flag is set, supposed
        # to be iterating then accepts the various incoming connections
        # and handles it by creating a new thread handler
        while self.executing:
            read, _write, _error = select.select(sockets, [], [], SELECT_TIMEOUT)
            if not read: continue
            for read_socket in read:
                try:
                    connection, address = read_socket.accept()
                    if read_socket == _socket_ssl: connection = ssl.wrap_socket(
                        connection,
                        server_side = True,
                        certfile = cert_path,
                        keyfile = key_path
                    )
                    _handler = handler(connection, address, timeout, self.current)
                    _handler.start()
                except BaseException, exception:
                    print >> sys.stderr, " [error] - %s" % str(exception)

        # closes the service sockets as no more work is meant to be processed
        # (end of the proxy task) note that the ssl socket is only closed in
        # case the use ssl flag is currently active
        _socket.close()
        use_ssl and _socket_ssl.close()

    def stop_server(self):
        self.executing = False
