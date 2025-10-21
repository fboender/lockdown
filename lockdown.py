#!/bin/env python3

import os
import sys
import argparse
import logging

from project import Project, ProjectError
from daemon import Daemon, DaemonError
from genkey import gen_key
from genconf import gen_conf
import common


__VERSION__ = "0.5"
__DESC__ = "Quickly lock and unlock (encrypt, decrypt) credentials in projects"
DAEMON_CONF_PATH=os.path.expanduser("~/.config/lockdown/daemon.conf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__DESC__
    )
    parser.add_argument('--version', action='version', version='%(prog)s v' + __VERSION__)
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Verbose info')

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command"
    )
    subparsers.required = True  # force user to choose a command
    sp_status = subparsers.add_parser("status", help="Show locked status")
    sp_lock = subparsers.add_parser("lock", help="Lock project")
    sp_unlock = subparsers.add_parser("unlock", help="Unlock project")
    sp_genkey = subparsers.add_parser("genkey", help="Generate a new key")
    sp_genkey.add_argument("-o", "--output", metavar="NAME", dest="output", type=str, default="lockdown", help="Output file name for private and public key (don't add an extension)")
    sp_genconf = subparsers.add_parser("genconf", help="Generate a new .lockdown.conf")
    sp_genconf.add_argument(metavar='FILE', dest="files", type=str, nargs='+', help='Files to lock')
    sp_daemon = subparsers.add_parser("daemon", help="Run lockdown background daemon")
    sp_daemon.add_argument("-c", "--config", metavar="PATH", dest="config", type=str, default=DAEMON_CONF_PATH, help="Path to configuration file. (default: ~/.config/lockdown/daemon.conf")
    args = parser.parse_args()

    # Configure application logging. Default level for interactive use is INFO,
    # because we use it to display info to the user.
    if args.verbose is False:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    if args.command == "daemon":
        fmt = '%(asctime)s %(levelname)8s %(name)s | %(message)s'
    else:
        fmt = '%(message)s'

    formatter = logging.Formatter(fmt)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger(__package__)
    logger.setLevel(loglevel)
    logger.addHandler(handler)

    try:
        # Find and load project, if command requires it
        if args.command in ("status", "lock", "unlock"):
            config_path = common.find_up(os.getcwd(), ".lockdown.conf")
            if not config_path:
                logger.error("No .lockdown.conf found in current or parent dirs")
                sys.exit(1)
            project = Project(config_path)

        if args.command == "status":
            project.status()
        elif args.command == "lock":
            project.lock()
        elif args.command == "unlock":
            project.unlock()
        elif args.command == "genkey":
            gen_key(args.output)
        elif args.command == "genconf":
            gen_conf(args.files)
        elif args.command == "daemon":
            daemon = Daemon(args.config)
            daemon.run()
    except DaemonError as err:
        logging.error(err.args[0])
    except ProjectError as err:
        logging.error(err.args[0])
    except KeyboardInterrupt:
        # Don't show backtrace
        pass
