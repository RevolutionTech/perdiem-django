# PerDiem
#### The world's first fan run record label

[![Build Status](https://travis-ci.org/RevolutionTech/perdiem-django.svg?branch=master)](https://travis-ci.org/RevolutionTech/perdiem-django)
[![codecov](https://codecov.io/gh/RevolutionTech/perdiem-django/branch/master/graph/badge.svg)](https://codecov.io/gh/RevolutionTech/perdiem-django)

## Setup

### Prerequisites

PerDiem requires [PostgreSQL](https://www.postgresql.org/) and [memcached](http://memcached.org/) to be installed.

### Installation

Use [poetry](https://github.com/sdispater/poetry) to install Python dependencies:

    poetry install

### Configuration

PerDiem reads in environment variables from your local `.env` file. See `.env-sample` for configuration options. Be sure to [generate your own secret key](http://stackoverflow.com/a/16630719).

With everything installed and all files in place, you may now create the database tables and collect static files. You can do this with:

    $ poetry run python manage.py migrate
    $ poetry run python manage.py collectstatic

### Deployment

Before deploying, you will need to add some additional environment variables to your `.env` file. See `ProdConfig` for the environment variables used in production.

###### Note: The remainder of this section assumes that PerDiem is deployed in a Debian Linux environment.

PerDiem uses Gunicorn with [runit](http://smarden.org/runit/) and [Nginx](http://nginx.org/). You can install them with the following:

    $ sudo apt-get install runit runit-systemd nginx

The rest of the README assumes that the PerDiem repo was checked out in `/home/perdiem/`. Please replace this path as necessary.

We need to copy the Nginx configuration:

    $ cd /etc/nginx/sites-enabled
    $ sudo ln -s /home/perdiem/perdiem-django/perdiem/nginx/investperdiem.com investperdiem.com

Then we need to create a script to run PerDiem on boot with runit:

    $ sudo mkdir /etc/sv/perdiem
    $ cd /etc/sv/perdiem
    $ sudo nano run

In this file, create a script similar to the following:

    #!/bin/sh

    GUNICORN=/home/perdiem/.cache/pypoetry/virtualenvs/perdiem-django-py3.8/bin/gunicorn
    ROOT=/home/perdiem/perdiem-django
    PID=/var/run/gunicorn.pid

    APP=perdiem.wsgi:application

    if [ -f $PID ]; then rm $PID; fi

    cd $ROOT
    exec $GUNICORN -c $ROOT/perdiem/gunicorn.py --pid=$PID $APP

Then change the permissions on the file to be executable and symlink the project to /etc/service:

    $ sudo chmod u+x run
    $ sudo ln -s /etc/sv/perdiem /etc/service/perdiem

PerDiem should now automatically be running on the local machine.

To configure your local machine to enable easier deployments, simply add comma-separated SSH-like "host strings" for all of the production instances to an environment variable called `PERDIEM_REMOTE_HOSTS`. You may want to add this in your `.bashrc` or similar. Here is an example of a line in `.bashrc` that defines two PerDiem production instances:

    PERDIEM_REMOTE_HOSTS=user@host1.example.com,user@host2.example.com

Then you will be able to deploy to all of your instances with Fabric, simply with:

    $ poetry run fab deploy

If you'd like Fabric to notify your `#general` Slack channel when deployments complete, you can also add an environment variable `PERDIEM_DEPLOYBOT_TOKEN` containing the token for a bot configured on Slack:

    PERDIEM_DEPLOYBOT_TOKEN=abc123
