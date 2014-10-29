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
import shutil

import tiberium

from tiberium_soul import util
from tiberium_soul.main import app
from tiberium_soul.main import flask
from tiberium_soul.main import quorum

@app.route("/apps/new", methods = ("GET",))
def new_app():
    return flask.render_template(
        "app/new.html.tpl",
        link = "new_app",
        app = {},
        errors = {}
    )

@app.route("/apps", methods = ("POST",))
def create_app():
    # runs the validation process on the various arguments
    # provided to the app
    errors, app = quorum.validate(util.validate_app_new)
    if errors:
        return flask.render_template(
            "app/new.html.tpl",
            link = "new_app",
            app = app,
            errors = errors
        )

    # retrieves the name and the description attributes of
    # the app to be used in the creation
    name = quorum.get_field("name", None)
    description = quorum.get_field("description", None)

    # retrieves the current configuration structure to be able
    # to retrieve a series of configuration attributes
    config = util.get_config()
    hostname = config.get("hostname", "repo.tiberium")
    domain_suffix = config.get("domain_suffix", "tibapp")
    user = config.get("user", "git")
    group = config.get("group", "git")

    # retrieves the directory used to store the repository
    # for the various applications
    repos_folder = util.get_repos_folder()

    # creates the map containing the complete description of the
    # app from the provided parameters and configuration
    app = dict(
        id = name,
        name = name,
        description = description,
        domain = "%s.%s" % (name, domain_suffix),
        schema = "http",
        git = "git@%s:%s.git" % (hostname, name),
        env = {},
        domains = []
    )

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
    names = os.listdir(util.HOOKS_FOLDER)
    for _name in names:
        file_path = os.path.join(util.HOOKS_FOLDER, _name)
        target_path = os.path.join(hooks_path, _name)
        shutil.copy(file_path, target_path)
        os.chmod(target_path, 0x1ed)

    # changes the owner and group of the repository path (all the
    # applications require the same user)
    util.chown_r(repo_path, user, group)

    return flask.redirect(
        flask.url_for("show_app", id = name)
    )

@app.route("/apps", methods = ("GET",))
def list_app():
    apps = util.get_apps()

    return flask.render_template(
        "app/list.html.tpl",
        link = "apps",
        apps = apps
    )

@app.route("/apps/<id>", methods = ("GET",))
def show_app(id):
    app = util.get_app(id)
    return flask.render_template(
        "app/show.html.tpl",
        link = "apps",
        sub_link = "info",
        app = app
    )

@app.route("/apps/<id>/edit", methods = ("GET",))
def edit_app(id):
    app = util.get_app(id)
    return flask.render_template(
        "app/edit.html.tpl",
        link = "apps",
        sub_link = "edit",
        app = app,
        errors = {}
    )

@app.route("/apps/<id>/delete_c", methods = ("GET",))
def delete_app_c(id):
    app = util.get_app(id)
    return flask.render_template(
        "app/delete.html.tpl",
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
    suns_folder = util.get_suns_folder()
    repos_folder = util.get_repos_folder()

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
    app = util.get_app(id)
    return flask.render_template(
        "app/help.html.tpl",
        link = "apps",
        sub_link = "help",
        app = app
    )

@app.route("/apps/<id>/restart", methods = ("GET",))
def restart_app(id):
    # retrieves the directory to be used as the
    # based for the sun files
    suns_folder = util.get_suns_folder()

    # creates the "full" path to the sun file associated
    # with the app with the provided id
    file_path = os.path.join(suns_folder, "%s.sun" % id)

    # retrieves the "clojure method" to be used in the
    # execution (restart) of the sun file and uses it
    # to execute the restart of the application
    execute_sun = util.get_execute_sun(id, file_path)
    quorum.run_back(execute_sun)

    return flask.redirect(
        flask.url_for("show_app", id = id)
    )

@app.route("/apps/<id>/name", methods = ("POST",))
def set_name_app(id):
    # retrieves the app from the provided identifier
    # value (this map will be updated)
    app = util.get_app(id)

    # retrieves the name value from the
    # request to be used to set the new name
    # in the app structure
    name = quorum.get_field("name")
    app["name"] = name

    # runs the validation process on new app created
    # structures (should meet the requirements)
    errors, app_v = quorum.validate(util.validate_app, object = app)
    if errors:
        return flask.render_template(
            "app/edit.html.tpl",
            link = "new_app",
            app = app_v,
            errors = errors
        )

    # saves the app back in the database to reflect
    # the changes that were made
    db = quorum.get_mongo_db()
    db.apps.save(app)

    return flask.redirect(
        flask.url_for("edit_app", id = id)
    )

@app.route("/apps/<id>/description", methods = ("POST",))
def set_description_app(id):
    # retrieves the app from the provided identifier
    # value (this map will be updated)
    app = util.get_app(id)

    # retrieves the description value from the
    # request to be used to set the new description
    # in the app structure
    name = quorum.get_field("description")
    app["description"] = name

    # runs the validation process on new app created
    # structures (should meet the requirements)
    errors, app_v = quorum.validate(util.validate_app, object = app)
    if errors:
        return flask.render_template(
            "app/edit.html.tpl",
            link = "new_app",
            app = app_v,
            errors = errors
        )

    # saves the app back in the database to reflect
    # the changes that were made
    db = quorum.get_mongo_db()
    db.apps.save(app)

    return flask.redirect(
        flask.url_for("edit_app", id = id)
    )

@app.route("/apps/<id>/env", methods = ("POST",))
def set_env_app(id):
    # retrieves the app from the provided identifier
    # value (this map will be updated)
    app = util.get_app(id)

    # retrieves the key and value values from the
    # request to be used to set the new environment
    # variable for the app
    key = quorum.get_field("key")
    value = quorum.get_field("value")
    app["env"][key] = value

    # runs the validation process on new app created
    # structures (should meet the requirements)
    errors, app_v = quorum.validate(util.validate_app, object = app)
    if errors:
        return flask.render_template(
            "app/edit.html.tpl",
            link = "new_app",
            app = app_v,
            errors = errors
        )

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
    app = util.get_app(id)
    host = app.get("domain", None)

    # retrieves the alias sent by the post value
    # adds it as an alias in the app
    alias = quorum.get_field("alias", None)
    app["domains"].append(alias)

    # runs the validation process on new app created
    # structures (should meet the requirements)
    errors, app_v = quorum.validate(util.validate_app, object = app)
    if errors:
        return flask.render_template(
            "app/edit.html.tpl",
            link = "new_app",
            app = app_v,
            errors = errors
        )

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
    app = util.get_app(id)

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
