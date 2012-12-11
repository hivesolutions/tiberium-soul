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
import sys
import json
import time
import flask
import signal
import atexit
import shutil
import getopt

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

CONFIG_PATHS = (
    "/etc/tiberium/config.json",
)
""" The various config paths to be searched before using
the default config file """

CURRENT_DIRECTORY = os.path.dirname(__file__)
CURRENT_DIRECTORY_ABS = os.path.abspath(CURRENT_DIRECTORY)
GLOBAL_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "global")
TEMP_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "tmp")
SUNS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "suns")
REPOS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "repos")
HOOKS_FOLDER = os.path.join(CURRENT_DIRECTORY_ABS, "hooks")

app = flask.Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 ** 3

execution_thread = None
proxy_server = None
daemon = None

quorum.load(
    app,
    redis_session = True,
    mongo_database = MONGO_DATABASE,
    name = "tiberium_soul.debug"
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

    # retrieves the directory to be used as the
    # based for the sun files
    suns_folder = get_suns_folder()

    # reads the complete file contents from the request and
    # then retrieves the associated sun file to update it
    contents = file.read()
    file_path = os.path.join(suns_folder, "%s.sun" % name)
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
        "app_list.html.tpl",
        link = "apps",
        apps = apps
    )

@app.route("/apps/<id>", methods = ("GET",))
def show_app(id):
    app = get_app(id)
    return flask.render_template(
        "app_show.html.tpl",
        link = "apps",
        sub_link = "info",
        app = app
    )

@app.route("/apps/<id>/edit", methods = ("GET",))
def edit_app(id):
    app = get_app(id)
    return flask.render_template(
        "app_edit.html.tpl",
        link = "apps",
        sub_link = "edit",
        app = app,
        errors = {}
    )

@app.route("/apps/<id>/delete_c", methods = ("GET",))
def delete_app_c(id):
    app = get_app(id)
    return flask.render_template(
        "app_delete.html.tpl",
        link = "apps",
        sub_link = "delete",
        app = app,
        errors = {}
    )

@app.route("/apps/<id>/delete", methods = ("GET",))
def delete_app(id):
    # retrieves both the directory to used as the
    # base for the sun files and the directory used
    # to store the repositories
    suns_folder = get_suns_folder()
    repos_folder = get_repos_folder()

    # retrieves the current mongo database and removes the
    # app entry contained in it
    db = quorum.get_mongo_db()
    db.apps.remove({"id" : id})

    # retrieves the (complete) repository path for the current app
    # and removes the repository directory
    repo_path = os.path.join(repos_folder, "%s.git" % id)
    shutil.rmtree(repo_path)

    # retrieves the (complete) sun path for the current app and
    # removes the sun file from the file system
    sun_path = os.path.join(suns_folder, "%s.sun" % id)
    if os.path.exists(sun_path): os.remove(sun_path)

    return flask.redirect(
        flask.url_for("list_app")
    )

@app.route("/apps/<id>/help", methods = ("GET",))
def help_app(id):
    app = get_app(id)
    return flask.render_template(
        "app_help.html.tpl",
        link = "apps",
        sub_link = "help",
        app = app
    )

@app.route("/apps/<id>/restart", methods = ("GET",))
def restart_app(id):
    # retrieves the directory to be used as the
    # based for the sun files
    suns_folder = get_suns_folder()

    # creates the "full" path to the sun file associated
    # with the app with the provided id
    file_path = os.path.join(suns_folder, "%s.sun" % id)

    # retrieves the current time (to insert the job immediately)
    # and then retrieves the "clojure method" to be used in the
    # execution (deployment) of the sun file
    current_time = time.time()
    execute_sun = _get_execute_sun(id, file_path)
    execution_thread.insert_work(current_time, execute_sun)

    return flask.redirect(
        flask.url_for("show_app", id = id)
    )

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

    # retrieves the directory used to store the repository
    # for the various applications
    repos_folder = get_repos_folder()

    # creates the map containing the complete description of the
    # app from the provided parameters and configuration
    app = {
        "id" : name,
        "name" : name,
        "description" : description,
        "domain" : "%s.%s" % (name, domain_suffix),
        "schema" : "http",
        "git" : "git@%s:%s.git" % (hostname, name),
        "env" : {},
        "domains" : []
    }

    # retrieves the database and then saves the app in the
    # correct collection
    db = quorum.get_mongo_db()
    db.apps.save(app)

    # retrieves the (complete) repository path for the current app
    # and creates the repository in it (uses tiberium)
    repo_path = os.path.join(repos_folder, "%s.git" % name)
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
        flask.url_for("edit_app", id = id)
    )

@app.route("/apps/<id>/alias", methods = ("POST",))
def set_alias_app(id):
    # retrieves the application from the provided identifier
    # and then retrieves its (main) domain value
    app = get_app(id)
    host = app.get("domain", None)

    # retrieves the alias sent by the post value
    # adds it as an alias in the app
    alias = flask.request.form.get("alias", None)
    app["domains"].append(alias)

    # saves the app back in the database to reflect
    # the changes that were made
    db = quorum.get_mongo_db()
    db.apps.save(app)

    # retrieves the current storage infra-structure
    # and sets the alias in it
    storage = quorum.get_redis()
    storage.set("alias:%s" % alias, host)

    return flask.redirect(
        flask.url_for("edit_app", id = id)
    )

@app.route("/apps/<id>/alias/<alias>/unset", methods = ("GET",))
def unset_alias_app(id, alias):
    # retrieves the application from the provided identifier
    # and then retrieves its (main) domain value
    app = get_app(id)

    # removes the alias from the app
    if alias in app["domains"]: app["domains"].remove(alias)

    # saves the app back in the database to reflect
    # the changes that were made
    db = quorum.get_mongo_db()
    db.apps.save(app)

    # retrieves the current storage infra-structure
    # and sets the alias in it
    storage = quorum.get_redis()
    storage.delete("alias:%s" % alias)

    return flask.redirect(
        flask.url_for("edit_app", id = id)
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
    print "Exception in user code:"
    print "-" * 60
    traceback.print_exc(file = sys.stdout)
    print "-" * 60
    return str(error)

def get_config():
    # sets the initial config path as unset then iterates
    # over the various config file to try to find one that
    # is valid in the current file system
    config_path = None
    for _config_path in CONFIG_PATHS:
        if not os.path.exists(_config_path): continue
        config_path = _config_path

    # retrieves the path to the (target) config (configuration) file and
    # check if it exists then opens it and loads the json configuration
    # contained in it to config it in the template
    config_path = config_path or os.path.join(GLOBAL_FOLDER, "config.json")
    if not os.path.exists(config_path): raise RuntimeError("Config file does not exist")
    config_file = open(config_path, "rb")
    try: config = json.load(config_file)
    finally: config_file.close()

    return config

def get_suns_folder():
    config = get_config()
    suns_folder = config.get("suns_dir", SUNS_FOLDER)
    return suns_folder

def get_repos_folder():
    config = get_config()
    suns_folder = config.get("repos_dir", REPOS_FOLDER)
    return suns_folder

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
    suns_folder = get_suns_folder()
    names = os.listdir(suns_folder)

    for name in names:
        _base, extension = os.path.splitext(name)
        if not extension == ".sun": continue

        _name = name[:-4]
        file_path = os.path.join(suns_folder, "%s.sun" % _name)
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

    # starts the logging system for the current process, the
    # logging file is chosen according to the operative system
    quorum.start_log(app, "tiberium_soul.debug")

    # runs the cleanup environment state, to be able to
    # release all the currently allocated resources for
    # the current tiberium soul instance
    cleanup_environment()

def cleanup_environment():
    # references the a series of variables as a global variables
    # avoids problems with forward references
    global CLEANUP

    # in case the cleanup operation has been already processed
    # no need for duplicated operations (returns immediately)
    if CLEANUP: return

    # in case the current execution was done inside a daemon
    # process must try to run the cleanup operation in it
    daemon and daemon.cleanup()

    # stop the execution thread so that it's possible to
    # the process to return the calling
    execution_thread and execution_thread.stop()
    execution_thread and execution_thread.join()

    # stops the proxy server from executing, this should
    # take a while to take any effect (timeout value)
    proxy_server and proxy_server.stop()
    proxy_server and proxy_server.join()

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

def cleanup_environment_s(signum, frame):
    # calls the general purpose cleanup environment handler
    # to proceed with the cleanup operations
    cleanup_environment()

def start():
    # references the a series of variables as a global variables
    # avoids problems with forward references
    global execution_thread
    global proxy_server

    # retrieves the current configuration and tries to retrieve
    # the paths for the encryption (ssl) based connections
    config = get_config()
    cert_path = config.get("cert_path", None)
    key_path = config.get("key_path", None)

    # registers the cleanup environment function to be executed
    # once the environment exits and when the terminate signal
    # is raised this ensures a correct cleanup
    atexit.register(cleanup_environment)
    signal.signal(signal.SIGTERM, cleanup_environment_s)

    # creates the proxy server with the reference to
    # the current state map to be used for the proxy
    # routing rules
    proxy_server = proxy.ProxyServer(
        CURRENT,
        cert_path = cert_path,
        key_path = key_path
    )
    proxy_server.start()

    # creates the thread that it's going to be used to
    # execute the various background tasks and starts
    # it, providing the mechanism for execution
    execution_thread = execution.ExecutionThread()
    execution_thread.start()

    # redeploys the currently installed sun file so that
    # the system is restores to the actual state
    redeploy()

    # starts the running of the process structure, this
    # is the main entry point of the soul server
    run()

def execute():
    global daemon

    try: opts, _args = getopt.getopt(sys.argv[1:], "d", ["daemon"])
    except getopt.GetoptError: sys.exit(2)

    is_daemon = False
    for option, _args in opts:
        if option in ("-d", "--daemon"): is_daemon = True

    if is_daemon:
        daemon = TiberiumSoulDaemon()
        daemon.start(register = False)
    else:
        start()

class TiberiumSoulDaemon(quorum.Daemon):
    """
    Daemon based class, responsible for the execution
    of the tiberium soul process under daemon mode.
    """

    DAEMON_PID_FILE = "/var/run/tiberium_soul.pid"
    """ The path to the daemon pid file to be used
    in case the tiberium soul is run as a daemon """

    DAEMON_STDIN = "/dev/null"
    """ The path to the daemon file to be used as
    the standard input during daemon execution """

    DAEMON_STDOUT = "/var/log/tiberium_soul.log"
    """ The path to the daemon file to be used as
    the standard output during daemon execution """

    DAEMON_STDERR = "/var/log/tiberium_soul.err"
    """ The path to the daemon file to be used as
    the standard error output during daemon execution """

    def __init__(self, pid_file = None, stdin = None, stdout = None, stderr = None):
        quorum.Daemon.__init__(
            self,
            pid_file or TiberiumSoulDaemon.DAEMON_PID_FILE,
            stdin or TiberiumSoulDaemon.DAEMON_STDIN,
            stdout or TiberiumSoulDaemon.DAEMON_STDOUT,
            stderr or TiberiumSoulDaemon.DAEMON_STDERR
        )

    def run(self):
        try: start()
        finally: self.cleanup()

if __name__ == "__main__":
    execute()
