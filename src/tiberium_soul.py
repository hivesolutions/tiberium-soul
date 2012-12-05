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
import quorum
import execution

CURRENT = {
}
""" The base of the map that will hold the various state
related configuration for the execution of the tiberium
soul runtime processes """

PORTS = [port for port in range(5001, 5100)]
""" The list containing the tcp ports that are currently
available for the working of the soul instance """

MONGO_DATABASE = "tiberium_soul"
""" The default database to be used for the connection with
the mongo database """

CLEANUP = False
""" The flag that controls if the cleanup operation has
been already processed """

CURRENT_DIRECTORY = os.path.dirname(__file__)
CURRENT_DIRECTORY_ABS = os.path.abspath(CURRENT_DIRECTORY)
GLOBAL_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "global")
TEMP_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "tmp")
SUNS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "suns")
REPOS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "repos")
HOOKS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "hooks")
APPS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "apps")

app = flask.Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 ** 3

quorum.load(
    app,
    redis_session = True,
    mongo_database = MONGO_DATABASE
)

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
    name = flask.request.form["name"]
    file = flask.request.files["file"]

    # reads the complete file contents from the request and
    # then retrieves the associated sun file to update it
    contents = file.read()
    file_path = os.path.join(SUNS_FOLDER, "%s.sun" % name)
    file = open(file_path, "wb")
    try: file.write(contents)
    finally: file.close()

    # retrieves the current time (to insert the job immediately)
    # and then retrieves the "clojure method" to be used in the
    # execution (deployment) of the sun file
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

@app.route("/apps/<id>/env", methods = ("GET",))
def env_app(id):
    app = get_app(id)
    return flask.render_template(
        "apps_env.html.tpl",
        link = "apps",
        sub_link = "env",
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

@app.route("/apps/<id>/restart", methods = ("GET",))
def restart_app(id):
    # @todo: implement this method
    pass

@app.route("/apps/new", methods = ("GET",))
def new_app():
    return flask.render_template(
        "app_new.html.tpl",
        link = "new_app"
    )

@app.route("/apps", methods = ("POST",))
def create_app():
    # retrieves the name and the description attributes of
    # the app to be used in the creation
    name = flask.request.form.get("name", None)
    description = flask.request.form.get("description", None)

    # retrieves the current configuration structure to be able
    # to retrieve a series of configuration attributes
    config = get_config()
    hostname = config.get("hostname", "repo.tiberium")
    domain_suffix = config.get("domain_suffix", "tibapp")
    user = config.get("user", "git")
    group = config.get("group", "git")

    # creates the map containing the complete description of the
    # app from the provided parameters and configuration
    app = {
        "id" : name,
        "name" : name,
        "description" : description,
        "domain" : "%s.%s" % (name, domain_suffix),
        "schema" : "http",
        "git" : "git@%s:%s.git" % (hostname, name),
        "env" : {}
    }

    # retrieves the database and then saves the app in the
    # correct collection
    db = quorum.get_mongo_db()
    db.apps.save(app)

    # retrieves the (complete) repository path for the current app
    # and creates the repository in it (uses tiberium)
    repo_path = os.path.join(REPOS_FOLDER, "%s.git" % name)
    tiberium.create_repo(repo_path)

    # retrieves the "proper" path to the hooks in the application
    # to copy and change their permissions
    hooks_path = os.path.join(repo_path, ".git", "hooks")

    # lists the names of the various hook files and then copies
    # each of them to the hooks folder of the application
    names = os.listdir(HOOKS_FOLDER)
    for _name in names:
        file_path = os.path.join(HOOKS_FOLDER, _name)
        target_path = os.path.join(hooks_path, _name)
        shutil.copy(file_path, target_path)
        os.chmod(target_path, 0755)

    # changes the owner and group of the repository path (all the
    # applications require the same user)
    chown_r(repo_path, user, group)

    return flask.redirect(
        flask.url_for("show_app", id = name)
    )

@app.route("/apps/<id>/env", methods = ("POST",))
def set_env_app(id):
    # retrieves the app from the provided identifier
    # value (this map will be updated)
    app = get_app(id)

    # retrieves the key and value values from the
    # request to be used to set the new environment
    # variable for the app
    key = flask.request.form["key"]
    value = flask.request.form["value"]
    app["env"][key] = value

    # saves the app back in the database to reflect
    # the changes that were made
    db = quorum.get_mongo_db()
    db.apps.save(app)

    return flask.redirect(
        flask.url_for("show_app", id = id)
    )

@app.route("/alias", methods = ("POST",))
def create_alias():
    alias = flask.request.form.get("alias", None)
    host = flask.request.form.get("host", None)

    storage = quorum.get_redis()
    storage.set("alias:%s" % alias, host)

    return flask.redirect(
        flask.url_for("index")
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
    print "-" * 60
    traceback.print_exc(file = sys.stdout)
    print "-" * 60
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
    # retrieves the app from the provided identifier
    # value (this map will be updated)
    db = quorum.get_mongo_db()
    apps = db.apps.find()
    return apps

def get_app(id):
    # retrieves the app from the provided identifier
    # value (this map will be updated)
    db = quorum.get_mongo_db()
    app = db.apps.find_one({"id" : id})
    return app

def redeploy():
    names = os.listdir(SUNS_FOLDER)

    for name in names:
        _base, extension = os.path.splitext(name)
        if not extension == ".sun": continue

        _name = name[:-4]
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
        # in case the name is already present in the map
        # of currently executing processes the process
        # file for it must be "killed"
        if name in CURRENT:
            process, temp_path, port = CURRENT[name]
            try:
                process.kill()
                process.wait()
                shutil.rmtree(temp_path)
                PORTS.insert(0, port)
            except: pass

        # creates the full path to the "target" temporary
        # path to be used in the execution
        temp_path = os.path.join(TEMP_FOLDER, name)

        # retrieves the app for the provided name and retrieves
        # the set of environment variable to be used
        app = get_app(name)
        env = app.get("env", {})

        # retrieves the next available port from the list
        # of currently available ports
        port = PORTS.pop()

        # updates the map of (extra) environment variables
        # to be used for the execution of the sun file
        env["PORT"] = str(port)

        # executes the sun file and retrieves the tuple
        # object describing the "just" created process
        # for the sun file execution, this value will be
        # saved in the current map for future process actions
        process, temp_path = tiberium.execute_sun(
            file_path, temp_path = temp_path, env = env, sync = False
        )
        CURRENT[name] = (process, temp_path, port)

    return execute_sun

def run():
    # runs the loading of the quorum structures, this should
    # delegate a series of setup operations to quorum
    quorum.load(app, redis_session = True)

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
    # references the cleanup variable as a global variable
    # avoids problems with forward references
    global CLEANUP

    # in case the cleanup operation has been already processed
    # no need for duplicated operations (returns immediately)
    if CLEANUP: return

    # stop the execution thread so that it's possible to
    # the process to return the calling
    execution_thread.stop()
    execution_thread.join()

    # stops the proxy server from executing, this should
    # take a while to take any effect (timeout value)
    proxy_server.stop()
    proxy_server.join()

    # iterates over all the names pending in execution
    # and kill the executing processes, removing the
    # associated files at the same time
    for name in CURRENT:
        process, temp_path, port = CURRENT[name]
        try:
            process.kill()
            process.wait()
            shutil.rmtree(temp_path)
            PORTS.insert(0, port)
        except: pass

    # sets the cleanup flag as true so that duplicated
    # operations are immediately avoided
    CLEANUP = True

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
