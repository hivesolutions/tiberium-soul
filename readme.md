# [Tiberium Soul](http://tiberium_soul.hive.pt)

The Tiberium Soul server is the "heart" of the tiberium system it's responsible for the forwarding of the various
HTTP related request from the client to the proper tiberium instance.

## Ideas

* Full Heroku compatibility (eg: `Procfile`)
* Modular back-end usage with support for Digital Ocean (in the future [EC2](http://aws.amazon.com/ec2), [Azure](http://azure.microsoft.com/en-us), etc.)
* Support for add-ons using env variables of heroku (eg: `MONGOHQ_URL`)
* Optimization of resources (minimizing user cost)
* SSH key upload to Digital Ocean for provisioning of VM via [API](https://developers.digitalocean.com)
* Sandboxing of execution using LXC containers through [Docker API](https://docs.docker.com/reference/api/docker_remote_api)
* User managed proxy server (as opposed to the Heroku approach) with full SSL key support
* Possible manual management of infrastructure by the user (at his own risk)
* Direct support for GitHub repositories (deploy using specialized branch)
* One click configuration through OAuth login (in both Digital Ocean and GitHub)
* Infra-structure for selling our own (Hive Solutions) addons like a clone of [Parse](https://parse.com)

## Inspiration

### Technology

* [AppScale](https://github.com/AppScale)

### Logics/Workflow

* [Heroku](http://www.heroku.com)
* [Cloud66](http://www.cloud66.com) / [Blog](http://blog.cloud66.com)
* [Amazon Beanstalk](http://aws.amazon.com/elasticbeanstalk)
* [Vagrant](http://www.vagrantup.com)
* [Docker](https://www.docker.com)

### UI/UX

* [Dropbox](http://www.dropbox.com)
* [Digital Ocean](https://www.digitalocean.com)
* [MongoHQ](https://www.mongohq.com)

### Mocks

* [Mock 1](https://dribbble.com/shots/1635230-Tackkle-Dashboard-Freelancing-Tool-WIP) - Design, UX
* [Mock 2](https://dribbble.com/shots/1635231-Personal-Website-Redesign) - Design
* [Mock 3](https://dribbble.com/shots/1636389-HelpDesk-WIP) - Typography
* [Mock 4](https://dribbble.com/shots/1630145-Gmail-Redesign) - Design
* [Mock 5](https://dribbble.com/shots/1625429-Helpdesk) - Design, Icons
* [Mock 6](https://dribbble.com/shots/1603565-Groove-Helpdesk) - Design
* [Mock 7](https://dribbble.com/shots/1608896-Community-webpage) - Design
* [Mock 8](https://dribbble.com/shots/1616804-Businessworld-2) - Design
* [Mock 9](https://dribbble.com/shots/1619740-Photo-Video-Page) - Design, Minimal, Icons
* [Mock 10](https://dribbble.com/shots/1636572-Rethinking-Email) - Design, Email, Minimal, Icons, Layers
* [Svbtle](https://svbtle.com/about) - Design
* [Dropbox](https://dribbble.com/dropbox) - Illustrations

## Typefaces

* [Avenir](http://en.wikipedia.org/wiki/Avenir_(typeface))
* [Muli](http://www.google.com/fonts/specimen/Muli)
* [ASAP](http://www.fontsquirrel.com/fonts/asap)
* [Benton Sans](http://www.fontbureau.com/fonts/BentonSans/styles/) - Heroku

## Homepage

* [Mock 1](https://dribbble.com/shots/1065238-Home-Page-Project-Gif) - Design, Size
* [Dropbox](https://www.dropbox.com) - Design, Simplicity, Focus, Illustrations
* [Heroku](https://www.heroku.com) - Design, Focus, Code Example

## Naming

* Fanti
* Jetopia
* Ventogo - Domain
* URriver - Domain
* Panode
* Beroute - Domain
* Routeship - Domain
* Shipado - Domain, Winner

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

Optional/optimal dependencies include:

* mongodb
* redis
* python-mongo
* python-redis

### Creation of the git user

In order to be able to run the deployment of the server using the "default" git user it
must be created in the target machine.

    $ adduser git
    $ passwd git
    $ usermod -d /usr/local/lib/python2.7/dist-packages/tiberium_soul-0.1.0-py2.7.egg/repos/ git

You can then verify the user information with.

    $ finger git

### Configuration

In order to configure tiberium create an `/etc/tiberium/config.json` file with the contents
of `global/config.json`.

An example configuration would be:

    {
        "hostname" : "repo.hostname",
        "domain_suffix" : "hostname",
        "user" : "git",
        "group" : "git",
        "cert_path" : "/etc/tiberium/cerfile.cer",
        "key_path" : "/etc/tiberium/keyfile.key",
        "suns_dir" : "/var/tiberium/suns",
        "repos_dir" : "/var/tiberium/repos"
    }

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

    $ python setup.py register sdist bdist_wheel upload
