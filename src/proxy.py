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
import thread
import select
import threading

__version__ = "0.1.0 Draft 1"

BUFLEN = 4096

VERSION = "Python Proxy/" + __version__

HTTPVER = "HTTP/1.1"

class ConnectionHandler:
    def __init__(self, connection, address, timeout, current):
        self.client = connection
        self.client_buffer = ""
        self.timeout = timeout
        self.current = current
        self.method, self.path, self.protocol = self.get_base_header()
        self.headers = self.get_headers()

        if self.method == "CONNECT":
            self.method_CONNECT()
        elif self.method in ("OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE"):
            self.method_others()
        self.client.close()
        self.target.close()

    def get_base_header(self):
        while 1:
            end = self.client_buffer.find("\r\n")
            if not end == -1: break
            self.client_buffer += self.client.recv(BUFLEN)

        print "'%s'" % self.client_buffer[:end]

        data = (self.client_buffer[:end]).split()
        self.client_buffer = self.client_buffer[end + 2:]
        print data
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
        self.client.send(HTTPVER + " 200 Connection established\n" + "Proxy-agent: %s\n\n" % VERSION)
        self.client_buffer = ""
        self._read_write()

    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find("/")
        path = self.path[i:]
        path = path or "/"

        host = self.headers["Host"]
        host_s = host.split(".", 1)
        name = host_s[0]

        process_t = self.current.get(name, None)
        if not process_t: raise RuntimeError("Problem handling the request, no process available")

        _process, _temp_path, port = process_t

        self._connect_target("localhost:" + str(port))
        self.target.send("%s %s %s\n" % (self.method, path, self.protocol) + self.client_buffer)
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
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
                    if in_ is self.client:
                        out = self.target
                    else:
                        out = self.client
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break

class ProxyServer(threading.Thread):

    current = None

    def __init__(self, current):
        threading.Thread.__init__(self)
        self.current = current

    def run(self):
        self.start_server()

    def start_server(self, host = "0.0.0.0", port = 80, timeout = 60, handler = ConnectionHandler):
        soc_type = socket.AF_INET
        soc = socket.socket(soc_type)
        soc.bind((host, port))

        hostname = not port == 80 and host + ":" + str(port) or host

        print >> sys.stderr, " * Running proxy on http://%s/" % hostname
        soc.listen(0)

        while 1:
            arguments = soc.accept() + (timeout, self.current)
            thread.start_new_thread(handler, arguments)
