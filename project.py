import getpass
import random
import getpass
import os
import time

import common

import pyrage


class Project:
    """
    A project is basically a directory with a .lockdown.conf file. This object
    can be used to read that config file, see the status, lock and unlock all
    files defined in the configuration.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.base_dir = os.path.dirname(os.path.expanduser(self.config_path))
        self.config = common.read_config(self.config_path)
        self.pub_key = self.config["pub_key"]
        self.priv_key_path = self.find_priv_key(self.base_dir)
        self.lock_files = self.config["lock_files"]

    def find_priv_key(self, base_dir):
        priv_key_path = None

        if "priv_key_path" in self.config:
            if self.config["priv_key_path"].startswith("/"):
                priv_key_path = self.config["priv_key_path"]
            else:
                priv_key_path = os.path.join(self.base_dir, os.path.expanduser(self.config["priv_key_path"]))
        else:
            priv_key_path = common.find_up(base_dir, ".lockdown.key")

        if not os.path.exists(priv_key_path):
            raise FileNotFoundError(f"No such file or directory: {priv_key_path}")

        if priv_key_path is None:
            raise FileNotFoundError("Cannot find a .lockdown.key file in the current or any of the parent directories")

        return priv_key_path

    def status(self):
        fully_locked = True

        for lock_file in self.lock_files:
            path_decrypted = os.path.join(self.base_dir, f"{lock_file}")

            if os.path.exists(path_decrypted):
                fully_locked = False

        if fully_locked is True:
            common.console_msg(f"Project '{self.base_dir}' is locked")
        else:
            common.console_msg(f"Project '{self.base_dir}' is not (fully) locked")

    def lock(self):
        pub_key = pyrage.x25519.Recipient.from_str(self.pub_key)

        for lock_file in self.lock_files:
            path_decrypted = os.path.join(self.base_dir, f"{lock_file}")
            path_encrypted = os.path.join(self.base_dir, f"{lock_file}.age")

            if os.path.exists(path_encrypted):
                common.console_msg(f"{lock_file} alrleady locked. Skipping")
                continue

            common.console_msg(f"Locking {path_decrypted}")
            with open(path_decrypted, "rb") as fh_decrypted:
                encrypted = pyrage.encrypt(fh_decrypted.read(), [pub_key])
                with open(path_encrypted, "wb") as fh_cipher:
                    fh_cipher.write(encrypted)
                os.unlink(path_decrypted)

    def unlock(self):
        priv_key = self.get_priv_key()

        for lock_file in self.lock_files:
            path_decrypted = os.path.join(self.base_dir, f"{lock_file}")
            path_encrypted = os.path.join(self.base_dir, f"{lock_file}.age")

            if not os.path.exists(path_encrypted):
                print(f"{path_decrypted} not locked. Skipping")
                continue

            common.console_msg(f"Unlocking {path_encrypted}")
            with open(path_encrypted, "rb") as fh_encrypted:
                decrypted = pyrage.decrypt(fh_encrypted.read(), [priv_key])
                with open(path_decrypted, "wb") as fh_decrypted:
                    fh_decrypted.write(decrypted)

                # We just unlink (rm) the original file. There's no point in
                # secure wipe these days.
                os.unlink(path_encrypted)

    def get_priv_key(self):
        password = getpass.getpass(f"Password for {self.priv_key_path}: ")
        with open(self.priv_key_path, "rb") as fh:
            for line in pyrage.passphrase.decrypt(fh.read(), password).decode("utf-8").splitlines():
                if line.startswith("AGE-SECRET-KEY-"):
                    key = line.strip()
                    identity = pyrage.x25519.Identity.from_str(key)
                    return identity

    def lock_age(self):
        lock_file_ages = {}
        for lock_file in self.lock_files:
            full_path = os.path.join(self.base_dir, lock_file)
            if os.path.exists(full_path):
                age_seconds = time.time() - os.path.getmtime(full_path)
                lock_file_ages[full_path] = age_seconds
        return lock_file_ages
