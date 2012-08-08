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

import os
import json
import time
import flask
import atexit
import shutil

import tiberium

import proxy
import execution

CURRENT = {}
""" The base of the map that will hold the various state
related configuration for the execution of the tiberium
soul runtime processes """

PORTS = [port for port in range(5001, 5100)]
""" The list containing the tcp ports that are currently
available for the working of the soul instance """

CURRENT_DIRECTORY = os.path.dirname(__file__)
CURRENT_DIRECTORY_ABS = os.path.abspath(CURRENT_DIRECTORY)
GLOBAL_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "global")
SUNS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "suns")
REPOS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "repos")
HOOKS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "hooks")
APPS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "apps")

app = flask.Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 ** 3

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
    name = flask.request.form["name"]
    file = flask.request.files["file"]
    contents = file.read()
    file_path = os.path.join(SUNS_FOLDER, "%s.sun" % name)
    file = open(file_path, "wb")
    try: file.write(contents)
    finally: file.close()
    current_time = time.time()
    execute_sun = _get_execute_sun(name, file_path)
    execution_thread.insert_work(current_time, execute_sun)
    return "success"

@app.route("/apps", methods = ("GET",))
def list_app():
    apps = get_apps()

    return flask.render_template(
        "apps_list.html.tpl",
        link = "apps",
        apps = apps
    )

@app.route("/apps/<id>", methods = ("GET",))
def show_app(id):
    app = get_app(id)
    return flask.render_template(
        "apps_show.html.tpl",
        link = "apps",
        sub_link = "info",
        app = app
    )

@app.route("/apps/<id>/help", methods = ("GET",))
def help_app(id):
    app = get_app(id)
    return flask.render_template(
        "apps_help.html.tpl",
        link = "apps",
        sub_link = "help",
        app = app
    )

@app.route("/apps/new", methods = ("GET",))
def new_app():
    return flask.render_template(
        "app_new.html.tpl",
        link = "new_app"
    )

@app.route("/apps", methods = ("POST",))
def create_app():
    name = flask.request.form.get("name", None)
    description = flask.request.form.get("description", None)

    config = get_config()
    hostname = config.get("hostname", "repo.tiberium")
    domain_suffix = config.get("domain_suffix", "tibapp")
    user = config.get("user", "git")
    group = config.get("group", "git")

    app = {
        "id" : name,
        "name" : name,
        "description" : description,
        "domain" : "%s.%s" % (name, domain_suffix),
        "schema" : "http",
        "git" : "git@%s:%s.git" % (hostname, name)
    }

    app_path = os.path.join(APPS_FOLDER, "%s.json" % name)
    app_file = open(app_path, "wb")
    try: json.dump(app, app_file)
    finally: app_file.close()

    repo_path = os.path.join(REPOS_FOLDER, "%s.git" % name)
    tiberium.create_repo(repo_path)

    hooks_path = os.path.join(repo_path, ".git", "hooks")

    names = os.listdir(HOOKS_FOLDER)
    for _name in names:
        file_path = os.path.join(HOOKS_FOLDER, _name)
        target_path = os.path.join(hooks_path, _name)
        shutil.copy(file_path, target_path)
        os.chmod(target_path, 0755)

    chown_r(repo_path, user, group)

    return flask.redirect(
        flask.url_for("show_app", id = name)
    )

@app.errorhandler(404)
def handler_404(error):
    return str(error)

@app.errorhandler(413)
def handler_413(error):
    return str(error)

@app.errorhandler(BaseException)
def handler_exception(error):
    import traceback
    import sys
    print "Exception in user code:"
    print '-' * 60
    traceback.print_exc(file=sys.stdout)
    print '-' * 60
    return str(error)

def get_config():
    # retrieves the path to the (target) config (configuration) file and
    # check if it exists then opens it and loads the json configuration
    # contained in it to config it in the template
    config_path = os.path.join(GLOBAL_FOLDER, "config.json")
    if not os.path.exists(config_path): raise RuntimeError("Config file does not exist")
    config_file = open(config_path, "rb")
    try: config = json.load(config_file)
    finally: config_file.close()

    return config

def get_apps():
    apps_directory = os.path.join(APPS_FOLDER)
    if not os.path.exists(apps_directory): raise RuntimeError("Apps directory does not exist")
    entries = os.listdir(apps_directory)
    entries.sort()

    apps = []

    for entry in entries:
        base, extension = os.path.splitext(entry)
        if not extension == ".json": continue

        app = get_app(base)
        apps.append(app)

    return apps

def get_app(id):
    # retrieves the path to the (target) app (configuration) file and
    # check if it exists then opens it and loads the json configuration
    # contained in it to app it in the template
    app_path = os.path.join(APPS_FOLDER, "%s.json" % id)
    if not os.path.exists(app_path): raise RuntimeError("app file does not exist")
    app_file = open(app_path, "rb")
    try: app = json.load(app_file)
    finally: app_file.close()

    return app

def redeploy():
    names = os.listdir(SUNS_FOLDER)

    for name in names:
        _base, extension = os.path.splitext(name)
        if not extension == ".sun": continue

        _name = name.strip(".sun")
        file_path = os.path.join(SUNS_FOLDER, "%s.sun" % _name)
        current_time = time.time()
        execute_sun = _get_execute_sun(_name, file_path)
        execution_thread.insert_work(current_time, execute_sun)

def chown_r(path, user, group):
    # in case the current operative system is
    # windows base cannot set the owner, and
    # must return immediately
    if os.name == "nt": return

    for base, dirs, files in os.walk(path):
        for name in dirs:
            chown(os.path.join(base, name), user, group)
        for name in files:
            chown(os.path.join(base, name), user, group)

    chown(path, user, group)

def chown(file_path, user, group):
    # in case the current operative system is
    # windows base cannot set the owner, and
    # must return immediately
    if os.name == "nt": return

    import pwd
    import grp
    pw_name = pwd.getpwnam(user)
    group_info = grp.getgrnam(group)
    uid = pw_name.pw_uid
    gid = group_info.gr_gid
    os.chown(file_path, uid, gid) #@UndefinedVariable

def _get_execute_sun(name, file_path):
    def execute_sun():
        if name in CURRENT:
            process, temp_path, port = CURRENT[name]
            try:
                process.kill()
                process.wait()
                shutil.rmtree(temp_path)
                PORTS.append(port)
            except: pass

        # retrieves the next available port from the list
        # of currently available ports
        port = PORTS.pop()

        # creates the map of (extra) environment variables
        # to be used for the execution of the sun file
        env = {
            "PORT" : str(port)
        }

        # executes the sun file and retrieves the tuple
        # object describing the "just" created process
        # for the sun file execution, this value will be
        # saved in the current map for future process actions
        process, temp_path = tiberium.execute_sun(file_path, env = env, sync = False)
        CURRENT[name] = (process, temp_path, port)

    return execute_sun

def run():
    # sets the debug control in the application
    # then checks the current environment variable
    # for the target port for execution (external)
    # and then start running it (continuous loop)
    debug = os.environ.get("DEBUG", False) and True or False
    reloader = os.environ.get("RELOADER", False) and True or False
    port = int(os.environ.get("PORT", 5000))
    CURRENT["admin"] = (None, None, port)
    app.debug = debug
    app.run(
        use_debugger = debug,
        debug = debug,
        use_reloader = reloader,
        host = "0.0.0.0",
        port = port
    )

    # runs the cleanup environment state, to be able to
    # release all the currently allocated resources for
    # the current tiberium soul instance
    cleanup_environment()

@atexit.register
def cleanup_environment():
    # iterates over all the names pending in execution
    # and kill the executing processes, removing the
    # associated files at the same time
    for name in CURRENT:
        process, temp_path, port = CURRENT[name]
        try:
            process.kill()
            process.wait()
            shutil.rmtree(temp_path)
            PORTS.append(port)
        except: pass

    # stop the execution thread so that it's possible to
    # the process to return the calling
    execution_thread.stop()

    # stops the proxy server from executing, this should
    # take a while to take any effect (timeout value)
    proxy_server.stop()

# creates the proxy server with the reference to
# the current state map to be used for the proxy
# routing rules
proxy_server = proxy.ProxyServer(CURRENT)
proxy_server.start()

# creates the thread that it's going to be used to
# execute the various background tasks and starts
# it, providing the mechanism for execution
execution_thread = execution.ExecutionThread()
execution_thread.start()

# redeploys the currently installed sun file so that
# the system is restores to the actual state
redeploy()

if __name__ == "__main__":
    run()
