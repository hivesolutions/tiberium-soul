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
import sys

from tiberium_soul import util
from tiberium_soul.main import app
from tiberium_soul.main import flask
from tiberium_soul.main import quorum

@app.route("/", methods = ("GET",))
@app.route("/index", methods = ("GET",))
def index():
    return flask.render_template(
        "index.html.tpl",
        link = "home"
    )

@app.route("/about", methods = ("GET",))
def about():
    return flask.render_template(
        "about.html.tpl",
        link = "about"
    )

@app.route("/deploy", methods = ("POST",))
def deploy():
    # retrieves the name of the sun file to be deployed
    # and the contents of the file to be deployed
    name = quorum.get_field("name")
    file = quorum.get_field("file")

    # retrieves the directory to be used as the
    # based for the sun files
    suns_folder = util.get_suns_folder()

    # reads the complete file contents from the request and
    # then retrieves the associated sun file to update it
    contents = file.read()
    file_path = os.path.join(suns_folder, "%s.sun" % name)
    file = open(file_path, "wb")
    try: file.write(contents)
    finally: file.close()

    # retrieves the "clojure method" to be used in the
    # execution (deployment) of the sun file and uses it
    # to execute the deployment of the application
    execute_sun = util.get_execute_sun(name, file_path)
    quorum.run_back(execute_sun)
    return "success"

@app.errorhandler(404)
def handler_404(error):
    return str(error)

@app.errorhandler(413)
def handler_413(error):
    return str(error)

@app.errorhandler(BaseException)
def handler_exception(error):
    import traceback
    print("Exception in user code:")
    print("-" * 60)
    traceback.print_exc(file = sys.stdout)
    print("-" * 60)
    return str(error)
