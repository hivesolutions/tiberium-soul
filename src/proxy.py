#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Tiberium System
# Copyright (C) 2008-2012 Hive Solutions Lda.
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

__copyright__ = "Copyright (c) 2008-2012 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import sys
import socket
import select
import threading

__version__ = "0.1.0 Draft 1"

BUFLEN = 4096

VERSION = "Python Proxy/" + __version__

HTTPVER = "HTTP/1.1"

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
        self.timeout = timeout
        self.current = current

    def run(self):
        try:
            self.method, self.path, self.protocol = self.get_base_header()
            self._client_buffer = self.client_buffer
            self.headers = self.get_headers()

            if self.method == "CONNECT":
                self.method_CONNECT()
            elif self.method in ("OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE"):
                self.method_others()
        except BaseException, exception:
            self.client.send("Problem in routing - %s" % str(exception))
        else:
            self.target.close()
        finally:
            self.client.close()

    def get_base_header(self):
        while 1:
            end = self.client_buffer.find("\r\n")
            if not end == -1: break
            self.client_buffer += self.client.recv(BUFLEN)

        data = (self.client_buffer[:end]).split()
        self.client_buffer = self.client_buffer[end + 2:]
        return data

    def get_headers(self):
        while 1:
            end = self.client_buffer.find("\r\n\r\n")
            if not end == -1: break
            self.client_buffer += self.client.recv(BUFLEN)

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
        self.client.send(HTTPVER + " 200 Connection established\n" + "Proxy-agent: %s\r\n\r\n" % VERSION)
        self.client_buffer = ""
        self._read_write()

    def method_others(self):
        path = self.path or "/"

        host = self.headers.get("Host", DEFAULT_HOST)
        host_s = host.split(".", 1)
        name = host_s[0]

        process_t = self.current.get(name, None)
        if not process_t: raise RuntimeError("No process available for request (%s)" % name)

        _process, _temp_path, port = process_t

        self._connect_target("localhost:" + str(port))
        self.target.send("%s %s %s\r\n" % (self.method, path, self.protocol) + self._client_buffer)
        self.client_buffer = ""
        self._read_write()

    def _connect_target(self, host):
        i = host.find(":")
        if not i == -1:
            port = int(host[i + 1:])
            host = host[:i]
        else:
            port = 80
        self.target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.target.connect((host, port))

    def _read_write(self):
        time_out_max = self.timeout / 3
        socs = [self.client, self.target]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)

            if error: break

            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
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
    the various handling operation in the proxy server, this
    map should contain various options including the various
    instances to be used in the proxy """

    executing = True
    """ The flag that controls the continuous execution
    of the proxy server, if unset the proxy handling stops """

    def __init__(self, current):
        threading.Thread.__init__(self)

        self.current = current

    def run(self):
        self.start_server()

    def stop(self):
        self.stop_server()

    def start_server(self, host = "0.0.0.0", port = 8080, timeout = 60, handler = ConnectionHandler):
        # creates the (internet) socket for the service and binds
        # it to the required host and port
        socket_type = socket.AF_INET
        _socket = socket.socket(socket_type)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _socket.bind((host, port))

        # creates the hostname string value taking into account if the
        # provided port is the default one for the connection, then
        # prints the information on the hostname binding
        hostname = not port == 80 and host + ":" + str(port) or host
        print >> sys.stderr, " * Running proxy on http://%s/" % hostname

        # starts listening in the socket for the various connections to
        # be received in the current proxy
        _socket.listen(0)

        # iterates continuously, while the executing flag is set, supposed
        # to be iterating
        while self.executing:
            read, _write, _error = select.select([_socket], [], [], SELECT_TIMEOUT)
            if not read: continue
            connection, address = _socket.accept()
            _handler = handler(connection, address, timeout, self.current)
            _handler.start()

        # closes the service socket as no more work is meant to be processed
        # (end of the proxy task)
        _socket.close()

    def stop_server(self):
        self.executing = False
