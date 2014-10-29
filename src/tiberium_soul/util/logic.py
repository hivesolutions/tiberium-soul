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
import json
import shutil

import tiberium

import quorum

CURRENT = {
}
""" The base of the map that will hold the various state
related configuration for the execution of the tiberium
soul runtime processes """

PORTS = [port for port in range(5001, 5100)]
""" The list containing the tcp ports that are currently
available for the working of the soul instance """

CLEANUP = False
""" The flag that controls if the cleanup operation has
been already processed """

CONFIG_PATHS = (
    "/etc/tiberium/config.json",
)
""" The various config paths to be searched before using
the default config file """

CURRENT_FOLDER = os.path.abspath(".")
GLOBAL_FOLDER = os.path.join(CURRENT_FOLDER, "global")
TEMP_FOLDER = os.path.join(CURRENT_FOLDER, "tmp")
SUNS_FOLDER = os.path.join(CURRENT_FOLDER, "suns")
REPOS_FOLDER = os.path.join(CURRENT_FOLDER, "repos")
HOOKS_FOLDER = os.path.join(CURRENT_FOLDER, "hooks")

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
        execute_sun = get_execute_sun(_name, file_path)
        quorum.run_back(execute_sun)

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

def get_execute_sun(name, file_path):
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
        process, temp_path = tiberium.run_sun(
            file_path, temp_path = temp_path, env = env, sync = False
        )
        CURRENT[name] = (process, temp_path, port)

    return execute_sun
