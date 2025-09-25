#!/bin/env python3

import os
import sys
import argparse
import getpass

from project import Project
import common

import pyrage


__VERSION__ = "0.1"
__DESC__ = "Quickly lock and unlock (encrypt, decrypt) credentials in projects"


def gen_key():
    passwd1 = getpass.getpass("Password for the new key?: ")
    passwd2 = getpass.getpass("Verify password?: ")

    if passwd1 != passwd2:
        sys.stderr.write("Passwords do not match. Aborting\n")
        sys.exit(1)

    ident = pyrage.x25519.Identity.generate()
    public_key = ident.to_public()
    private_key = str(ident).encode("ascii")
    encrypted_pw = pyrage.passphrase.encrypt(private_key, passwd1)
    sys.stdout.buffer.write(encrypted_pw)
    sys.stderr.write(f"public key: {public_key}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__DESC__
    )
    parser.add_argument('--version', action='version', version='%(prog)s v' + __VERSION__)

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command"
    )
    subparsers.required = True  # force user to choose a command
    subparsers.add_parser("status", help="Show locked status")
    subparsers.add_parser("lock", help="Lock project")
    subparsers.add_parser("unlock", help="Unlock project")
    subparsers.add_parser("genkey", help="Generate a new key")
    args = parser.parse_args()

    if args.command != "genkey":
        config_path = common.find_up(os.getcwd(), ".lockdown.conf")
        if not config_path:
            common.console_msg("No .lockdown.conf found in current or parent dirs")
            sys.exit(1)
        project = Project(config_path)

    if args.command == "status":
        project.status()
    elif args.command == "lock":
        project.lock()
    elif args.command == "unlock":
        project.unlock()
    elif args.command == "genkey":
        gen_key()
