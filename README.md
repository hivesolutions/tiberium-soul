# [Tiberium Soul Server](http://tiberiumapp.com)
The Tiberium Soul server is the "heart" of the tiberium system it's responsible for the forwarding of the various
HTTP related request from the client to the proper tiberium instance. 

## Configuration

This series of sets assume that the target machine is running Ubuntu Linux 12.10.

### Dependencies

Currently Tiberium Soul depends on:

* git
* python-setuptools
* pip
* virtualenv
* tiberium
* flask
* linux

### Creation of the git user

In order to be able to run the deployment of the server using the "default" git user it
must be created in the target machine.

	$ adduser git
	$ passwd git
	$ usermod -d /usr/local/lib/python2.7/dist-packages/tiberium_soul-0.1.0-py2.7.egg/repos/ git

You can then verify the user information with.

	$ finger git

### Execution

After correctly installing tiberium soul execute the following command to start the gateway
and deployment infra-structures.

	$ tiberium_soul.sh

## Types of servers

* repository server -> repo.tiberium
* admin server -> admin.tiberium
* proxy server -> proxy.tiberium

## Build

### Uploading to pypi

If the configuration file for pypi (setup.py) is correctly defined and you ha ve the correct
permission for it you may upload it to the python package index.

	$ python setup.py sdist upload
