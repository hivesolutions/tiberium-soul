#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Tiberium System
# Copyright (c) 2008-2020 Hive Solutions Lda.
#
# This file is part of Hive Tiberium System.
#
# Hive Tiberium System is free software: you can redistribute it and/or modify
# it under the terms of the Apache License as published by the Apache
# Foundation, either version 2.0 of the License, or (at your option) any
# later version.
#
# Hive Tiberium System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Apache License for more details.
#
# You should have received a copy of the Apache License along with
# Hive Tiberium System. If not, see <http://www.apache.org/licenses/>.

__author__ = "João Magalhães <joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2020 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "Apache License, Version 2.0"
""" The license for the module """

import os
import setuptools

setuptools.setup(
    name = "tiberium-soul",
    version = "0.1.2",
    author = "Hive Solutions Lda.",
    author_email = "development@hive.pt",
    description = "Tiberium Soul System",
    license = "Apache License, Version 2.0",
    keywords = "tiberium soul platform service",
    url = "http://tiberium_soul.hive.pt",
    zip_safe = False,
    packages = [
        "tiberium_soul",
        "tiberium_soul.util",
        "tiberium_soul.views",
        "tiberium_soul.views.api",
        "tiberium_soul.views.web"
    ],
    package_dir = {
        "" : os.path.normpath("src")
    },
    install_requires = [
        "flask",
        "quorum",
        "tiberium"
    ],
    package_data = {
        "tiberium_soul" : [
            "repos/README.md",
            "suns/README.md",
            "tmp/README.md",
            "cert/*",
            "global/*",
            "hooks/*",
            "static/css/*",
            "static/images/*",
            "static/js/*",
            "templates/*.tpl",
            "templates/app/*.tpl",
            "templates/partials/*.tpl"
        ]
    },
    entry_points = {
        "console_scripts" : [
            "tiberium_soul = tiberium_soul.run:main"
        ]
    },
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
    long_description = open(os.path.join(os.path.dirname(__file__), "README.md"), "rb").read().decode("utf-8"),
    long_description_content_type = "text/markdown"
)
