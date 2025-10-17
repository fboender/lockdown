Commandline tool to easily lock (encrypt) and unlock (decrypt) project tokens,
credentials and keys. Optionally includes a daemon that automatically locks a
project after a certain time.

It uses [Age](https://github.com/FiloSottile/age) for encryption, so no hassle
with GnuPG setup or anything.

A birds-eye view of how it works:

    $ ls
    README.md   secret.json   google_api_secret.json   script.py

    $ lockdown genconf secret.json google_api_secret.json
    Generated '.lockdown.conf' in current dir

    $ lockdown lock
    Using public key '/home/fboender/.config/lockdown/lockdown.pub'
    Locking 'secret.json'
    Locking 'google_api_secret.json'

    $ lockdown status
    Project '/path/to/project' is locked

    $ lockdown unlock
    Password for /home/fboender/.config/lockdown/lockdown.key:
    Unlocking 'secret.json'
    Unlocking 'google_api_secret.json'

> [!WARNING]
> Lockdown is a work in progress. See the [Notes and Todos](#notes-and-todos)
> section for more information.

# Table of Contents

* [Why?](#why)</li>
* [Features](#features)</li>
* [How it works](#how-it-works)</li>
* [Installation](#installation)</li>
* [Usage](#usage)</li>
    * [Default keys](#default_keys)</li>
    * [Additional keys](#additional_keys)</li>
    * [Daemon](#daemon)</li>
* [Security considerations](#security-considerations)</li>
* [Notes and Todos](#notes-and-todos)</li>

<a name="why"></a>

# Why?

Recently there was [another high-profile supply chain
attack](https://socket.dev/blog/tinycolor-supply-chain-attack-affects-40-packages)
on various npm packages. This time, a credential stealer was embedded in the
attack. We are always told to not execute untrusted code, but the reality is
that this simply cannot be avoided in all cases.

I have a lot of projects that I occasionally work on. Many of these projects
require tokens, secrets, `kubeconfig.yml` files, etc.

When I'm not working on these projects, I don't want these tokens to be
vulnerable to credential exfiltration. But I also want it to be easy to get
back to working on a project I haven't worked on for a while.

Lockdown automatically locks such credentials when I'm not working on a
project, and makes it easy to unlock all required credentials when I resume
work.

<a name="features"></a>

# Features

* Uses [Age](https://github.com/FiloSottile/age) for encryption, so no hassle
  with GnuPG setup or anything
* Unlock multiple secrets in one go
* Manually lock secrets or automatically with a background daemon
* Use a single key, or optionally specify a different key per project
* Recursive globbing for lock files ala Git is supported (e.g. `**/*.yml`)

<a name="how-it-works"></a>

# How it works

Lockdown searches the current and parent dirs until it finds a
`.lockdown.conf` file. This file specifies how and what to lock:

    $ cd /path/to/project
    $ cat .lockdown.conf
    {
        "lock_files": [
            "secret.json",
            "google_api_secret.json",
            "google_api_tokens.json",
        ]
    }

We can lock the credentials:

    $ lockdown lock
    Using public key '/home/fboender/.config/lockdown/lockdown.pub'
    Locking 'secret.json'
    Locking 'google_api_secret.json'
    Locking 'google_api_tokens.json'

This takes the configured files, and encrypts them using an
[Age](https://github.com/FiloSottile/age) public key:

    $ ls -l
    README.md
    secret.json.age
    google_api_secret.json.age
    google_api_tokens.json.age

To unlock:

    $ lockdown unlock
    Password for /home/fboender/.config/lockdown/lockdown.key:
    Unlocking 'secret.json'
    Unlocking 'google_api_secret.json'
    Unlocking 'google_api_tokens.json'

An **optional background daemon** (`lockdown daemon`) can run in the
background and scan for unlocked projects in defined directories. These are
specified in the `daemon.conf` configuration file:

    {
        # Top level dirs which are recursively scanned for .lockdown.conf files
        "base_dirs": [
            "~",
        ],
    ...

It will automatically lock projects after a certain (configurable) period.

    INFO lockdownd | Lock file '/path/to/project/secret.json' older than 3600 seconds old. Locking project.

By default it will not lock a project if any of the current user's processes
has a working directory that's under the project's directory (i.e. you're
probably working on the project):

    INFO lockdownd | Lock file '/path/to/project/secret.json' older than 3600 seconds old. Locking project.
    INFO lockdownd | User has process running in '/path/to/project'. Not locking.

As soon as we change directories in the shell, the project gets locked:

    /path/to/project $ cd ..

The logging shows the project being locked:

    INFO lockdownd | Lock file '/path/to/project/secret.json' older than 3600 seconds old. Locking project.

Optionally, **a desktop notification** can be shown when a project gets
locked. This can be turned on in the `~/.config/lockdown/daemon.conf` file
with the `desktop_notify` setting. For this to work, `notify-send` must be
available on the system.


<a name="installation"></a>

# Installation

Lockdown is distributed as a standalone linux x86-64 binary. There currently
is no support for Windows or MacOS.

Download [the latest release](https://github.com/fboender/lockdown/releases)
and install Lockdown:

    $ tar -vxf ~/Downloads/lockdown-*.tar.gz
    $ cd lockdown-<VERSION>
    $ ./install.sh

<a name="usage"></a>

# Usage

<a name="default_keys"></a>

## Default keys

If you generated default keys during installation, you can immediately start
using Lockdown. If not, see below on how to generate initial or additional
keys.

Go to a project's directory and create a lockdown configuration file.

    $ ls
    README.md   secret.json   google_api_secret.json   script.py

    $ lockdown genconf secret.json google_api_secret.json
    Generated '.lockdown.conf' in current dir

    $ lockdown lock
    Using public key '/home/fboender/.config/lockdown/lockdown.pub'
    Locking 'secret.json'
    Locking 'google_api_secret.json'

    $ lockdown status
    Project '/path/to/project' is locked

    $ lockdown unlock
    Password for /home/fboender/.config/lockdown/lockdown.key:
    Unlocking 'secret.json'
    Unlocking 'google_api_secret.json'

<a name="additional_keys"></a>

## Additional keys

You can generate additional keys and use those for more sensitive tokens.

Generate a new public / private key pair:

    $ lockdown genkey
    Password for the new key?:
    Verify password?:

    Wrote encrypted key to 'lockdown.key'
    Wrote public key to 'lockdown.pub'

You can configure the keys in a `.lockdown.conf` file somewhere:

    $ cd /path/to/project
    $ vi .lockdown.conf

        {
            # Separate keys
            "priv_key_path": "lockdown.key",
            "pub_key_path": "lockdown.pub",

            # List of files to lock/unlock
            "lock_files": [
                "secret.json",
            ],
        }

Paths are relative to the location of the `.lockdown.conf` file, unless you
specify an absolute path. You can refer to your home directory using `~/`:

        {
            # Separate keys
            "priv_key_path": "~/.config/lockdown/keys/sensitive.key",
            "pub_key_path": "~/.config/lockdown/keys/sensitive.pub",
        ...


<a name="daemon"></a>

## Lock file globbing (wildcards)

You can use wildcards (globbing) to have lockdown dynamically find out which
files to lock and unlock. You must quote the lock file when using `genconf`:

    $ lockdown genconf '*.yml'

    $ tail .lockdown.conf
    # List of files to lock/unlock
    "lock_files": [
        "*.yml",
    ],

    $ lockdown -v status
    Loading public key from '/home/fboender/.config/lockdown/lockdown.pub'
    Using lock file: /path/to/project/cred_prod.yml
    Using lock file: /path/to/project/cred_acc.yml
    /path/to/project/cred_prod.yml is not locked
    /path/to/project/cred_acc.yml is not locked
    Project '/path/to/project' is not (fully) locked
    
Recursive globbing is also supported. This will find matching files anywhere
in the project:

    $ lockdown genconf '**/*.yml'

## Daemon

An optional daemon can be ran in the background to automatically lock projects
when they are not in use.

### Global install

If you installed Lockdown globally, the daemon will run in the usual systemd
way:

    $ sudo journalctl -u lockdown.service
    Oct 01 09:50:51 hank systemd[5890]: Started lockdown.service - Lockdown daemon.
    Oct 01 09:50:51 hank lockdown[1161448]: 2025-10-01 09:50:51,194     INFO daemon | Finding directories containing .lockdown.conf files under /home/fboender
    Oct 01 09:50:53 hank lockdown[1161448]: 2025-10-01 09:50:53,166     INFO project | Lock file '/path/to/project/secret.json' older than 3600 seconds old. Locking project.
    Oct 01 09:50:53 hank lockdown[1161448]: 2025-10-01 09:50:53,210     INFO project | User has process running in '/path/to/project'. Not locking.

The daemon configuration is installed in `/etc/lockdown/daemon.conf` and a
systemd unit service file in `/etc/systemd/system/lockdown.service`.

### Local user install

If you installed Lockdown for just your user, the daemon runs under your user
account using systemd. It will automatically start at system boot and it will
persist even when you log out.

You can interact with the daemon in the usual systemd way, except you need to
add the `--user` flag.

    # See systemd unit status
    $ systemctl --user status lockdown.service

    # View logging
    $ journalctl --follow --user -u lockdown.service

The daemon configuration is installed in `~/.config/lockdown/daemon.conf` and
a (user) systemd unit service file in
`~/.config/systemd/user/lockdown.service`.

To enable verbose logging, edit
`/.config/systemd/user/lockdown.service` and add a `-v` parameter to
the `Exec` line:

    ExecStart=%h/.local/bin/lockdown -v daemon

Reload systemd and restart the service:

    $ systemctl --user daemon-reload
    $ systemctl --user restart lockdown.service

## Prompt indicator

To add a locked indicator to your prompt when you change to the directory of a
project, add the following to your `~/.bashrc`:

    prompt_lockdown_locked() {
        if [ -f ".lockdown.conf" ]; then
            if [ "$(lockdown status | grep "is locked$")" != "" ]; then
                echo "🔒"
            fi
        fi
    }

    PS1="$(prompt_lockdown_locked) $PS1"

<a name="security-considerations"></a>

# Security considerations

## Pyrage library

Lockdown uses a pure-python implementation of
[Age](https://github.com/FiloSottile/age) called
[pyrage](https://github.com/woodruffw/pyrage). There is no information
available on how well tested this is, and whether its crypto has been
reviewed. But hey, I guess badly encrypted tokens are better than plain text
tokens.

## Password-protected private keys

Age private keys are not encrypted by default. I encrypt them using Age's own
symmetric encryption, essentially "putting a password on the private key". I
assume I've done this correctly, but it has not been reviewed.

## Keep private key passwords in your head, not on disk

I *strongly* encourage you to **NEVER** store the password to Lockdown private
keys *anywhere* on the same system as where the private keys live. Keep it in
your mind, not in your password manager or whatever. If a credential stealer
nabs both the Lockdown keys and a plaintext dump of your password manager, the
show is over.

## Attack vectors

Lockdown makes *no* attempt to thwart anything running as your user from
obtaining the passwords to private keys, other than never storing passwords on
disk. There's no fancy memory protection or whipping.

Basically if a process dumps the memory of a lockdown process while you're
entering a private key's password, it's probably game over. See also the next
item.

## Use separate keys for important things

The security model of Lockdown is mostly to protect "idle" tokens from being
exfiltrated in plain-text, because they were on your system unprotected.
However, if you protect all your tokens with a *single* private key, and you
use that once to unlock a specific project, an attacker could use the same
private key to unlock all your other secrets.

To reduce the fallout from such a situation, you should use separate
private/public keys for important tokens.


<a name="notes-and-todos"></a>

# Notes and Todos

* Not thoroughly tested yet.
* Standalone bins built against GlibC v2.39, which is very recent. Binaries
  might not run everywhere. **Update:** v0.3 has been build against an older
  version (v2.31)
* Only linux support for now, but should (theoretically) be able to run under
  windows and macos
* Currently no easy way to change the password of a private key, although you
  can just decrypt and re-encrypt with the `age` cli (symmetric mode)
