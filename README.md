Commandline tool to easily lock and unlock a project's secrets. Optionally
includes a daemon that automatically locks a project after a certain time.

> [!WARNING]
> Lockdown is a work in progress. See the [Notes and Todos](#notes-and-todos)
> section for more information.

# Table of Contents

* [Why?](#why)</li>
* [How it works](#how-it-works)</li>
* [Getting started](#getting-started)</li>
* [Notes and Todos](#notes-and-todos)</li>

<a name="why"></a>

# Why?

I have a lot of projects that I occasionally work on. Many of these projects
require tokens, secrets, `kubeconfig.yml` files, etc.

Recently there was [another high-profile supply chain
attack](https://socket.dev/blog/tinycolor-supply-chain-attack-affects-40-packages)
on various npm packages. This time, a credential stealer was embedded in the
attack.

When I'm not working on these projects, I don't want these tokens to be
vulnerable to credential exfiltration. But I also want it to be easy to get
back to working on a project I haven't worked on for a few weeks.

Lockdown automatically locks such credentials when I'm not working on a
project, and makes it easy to unlock all required credentials when I resume
work.


<a name="how-it-works"></a>

# How it works

Lockdown searches the current and parent dirs until it finds a
`.lockdown.conf` file. This file specifies how and what to lock:

    ~/Projects/bigbrother $ cat .lockdown.conf
    {
        "priv_key_path": "/home/fboender/.lockdown.key",
        "pub_key": "age15k5suy53vclwesnn5uzz7g6fn2e3w54epc86xxfqhwsqv5em6uyqccm90z",
        "lock_files": [
            "config.py",
            "google_api_secret.json",
            "google_api_tokens.json",
        ]
    }

You can safely commit this file or add `.lockdown.conf` to the local or global
`.gitigore` list.

To manually lock a project, run `lockdown lock` somewhere in the project
directory. You won't need to enter the key's password:

    ~/Projects/bigbrother $ lockdown lock
    Locking /home/fboender/Projects/bigbrother/config.py
    Locking /home/fboender/Projects/bigbrother/google_api_secret.json
    Locking /home/fboender/Projects/bigbrother/google_api_tokens.json

To unlock, use the `lockdown unlock` command. You will have to enter the
password for the key:

    ~/Projects/bigbrother $ lockdown unlock
    Password for /home/fboender/.lockdown.key: 
    Unlocking /home/fboender/Projects/bigbrother/config.py.age
    Unlocking /home/fboender/Projects/bigbrother/google_api_secret.json.age
    Unlocking /home/fboender/Projects/bigbrother/google_api_tokens.json.age

An **optional background daemon** (`lockdownd`) can run in the background and
scan for unlocked projects. It will automatically lock projects after a
certain (configurable) period.

    INFO lockdownd | Lock file '/home/fboender/Projects/bigbrother/config.py' older than 3600 seconds old. Locking project.

By default it will not lock a project if any of the current user's processes
has a working directory that's under the project's directory (i.e. you're
probably working on the project):

    INFO lockdownd | Lock file '/home/fboender/Projects/bigbrother/config.py' older than 3600 seconds old. Locking project.
    INFO lockdownd | User has process running in '/home/fboender/Projects/bigbrother'. Not locking.

As soon as we change directories in the shell, the project gets locked:

    ~/Projects/bigbrother $ cd ..

The logging shows the project being locked:

    INFO lockdownd | Lock file '/home/fboender/Projects/bigbrother/config.py' older than 3600 seconds old. Locking project.

Optionally, **a desktop notification** can be shown when a project gets
locked. This can be turned on in the `lockdownd.conf` file with the
`desktop_notify` setting. For this to work, `notify-send` must be available on
the system.


<a name="getting-started"></a>

# Getting started

Download [the latest release](https://github.com/fboender/lockdown/releases)
and install Lockdown:

    $ tar -vxf ~/Downloads/lockdown-*.tar.gz
    $ cd lockdown-<VERSION>

If you want to install Lockdown globally for all users:

    $ sudo ./install.sh

If you only want to install it for your own user:

    $ PREFIX="$HOME/.local" ./install.sh

Make sure that `$HOME/.local/bin` is in your PATH in this case.

Generate a new key:

    $ lockdown genkey > ~/.lockdown.key

Note the public key, you'll need it in the next step.

Go to a project's directory and create a lockdown configuration file.

    $ cd Projects/myproject
    $ vi .lockdown.conf
        {
            "pub_key": "<YOUR PUBLIC KEY>",
            "lock_files": [
                "jira-export.conf",
            ]
        }

Make sure to configure your public key and some paths to files containing
credentials. Paths are always relative to the location of the `.lockdown.conf`
file.

If the private key is not stored in `~/.lockdown.key`, you can specify the
`priv_key_path` option in the `.lockdown.conf`:

    {
        "priv_key_path": "~/Projects/myproject/.lockdown.key",
    }

You can now lock and unlock your project's secrets:

    $ lockdown lock
    Locking /path/to/project/jira-export.conf

View status:

    $ lockdown status
    Project '/path/to/project' is locked.

Unlock:

    $ lockdown unlock
    Password for /home/user/.lockdown.key:
    Unlocking /path/to/project/jira-export.conf.age


<a name="daemon"></a>

## Daemon

An optional daemon can be ran in the background to automatically lock projects
when they are not in use.

You can run the daemon under your user account using systemd.

Create the systemd service for your user:

    $ mkdir -p ~/.config/systemd/user
    $ mkdir -p ~/.config/lockdown
    $ cp lockdownd.service ~/.config/systemd/user
    $ cp lockdownd.conf.dist ~/.config/lockdown/lockdownd.conf
    $ systemctl --user daemon-reload
    $ systemctl --user enable --now lockdownd.service
    $ systemctl --user start lockdownd.service
    $ loginctl enable-linger $USER

If you want the service the keep running after you log out, you can enable
lingering:

    $ loginctl enable-linger $USER

To see the status:

    $ journalctl --follow --user -u lockdownd.service

<a name="notes-and-todos"></a>

# Notes and Todos

* Not thoroughly tested yet.
* Standalone bins built against GlibC v2.39, which is very recent. Binaries
  might not run everywhere.
* Unify `lockdown` and `lockdownd` for smaller binaries.

