import getpass
import random
import getpass
import os
import time
import logging
import glob
import stat
import hashlib

import common

import pyrage


logger = logger = logging.getLogger(__name__)


class ProjectError(Exception):
    pass


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
        self.pub_key_path = self.get_pub_key_path()  # Can be None
        self.pub_key = self.get_pub_key()
        self.priv_key_path = self.get_priv_key_path()
        self.lock_files = self.get_lock_files(self.config["lock_files"])

        if self.priv_key_readable_by_others(self.priv_key_path):
            logger.warning("WARNING: '%s' is readable by others. You probably want to change its permissions to 700", self.priv_key_path)

    def get_lock_files(self, lock_files):
        """
        Return a list of lock files for this project. Supports globbing
        ("**/*.conf").
        """
        results = set()

        # Unlocked files
        for lock_file_unlocked in lock_files:
            path = os.path.join(self.base_dir, lock_file_unlocked)
            for f in glob.glob(path, recursive=True):
                results.add(f)

        # We also look for lockfiles that are already locked. This is so we can
        # support globbing ('*'). Without this, we wouldn't find files for
        # globs (e.g. "*.yaml" wouldn't find anything because the files are
        # called "*.yaml.age")
        for lock_file_locked in lock_files:
            path = os.path.join(self.base_dir, f"{lock_file_locked}.age")
            for f in glob.glob(path, recursive=True):
                results.add(f[:-4])  # Add file without .age extension

        # Display when verbose
        for result in results:
            logger.debug(f"Using lock file: {result}")

        return results

    def get_priv_key_path(self):
        """
        Try various locations for a private key and return the first one that
        is found.
        """
        try_paths = []

        # Path in configuration
        if "priv_key_path" in self.config:
            if self.config["priv_key_path"].startswith("/"):
                # Absolute path
                try_paths.append(self.config["priv_key_path"])
            else:
                # Relative to base dir
                try_paths.append(os.path.join(self.base_path, self.config["priv_key_path"]))

                # Also try expand user path
                try_paths.append(os.path.expanduser(self.config["priv_key_path"]))

        # File relative to base dir
        try_paths.append(os.path.join(self.base_dir, ".lockdown.key"))

        # Default location (~/.config/lockdown
        try_paths.append(common.xdg_config_home(os.path.join("lockdown", "lockdown.key")))

        for try_path in try_paths:
            if os.path.exists(try_path):
                return try_path

        # No private key found anywhere
        err_msg = f"No private key defined in {self.config_path} or found in " + ", ".join(try_paths)
        raise ProjectError(err_msg, 1)

    def get_pub_key(self):
        """
        Try various locations for a public key and return the contents of the
        first public key found.
        """
        if "pub_key" in self.config:
            return self.config["pub_key"]
        else:
            pub_key_path = self.get_pub_key_path()
            logger.debug("Loading public key from '%s'", pub_key_path)
            try:
                with open(pub_key_path, "r") as fh:
                    return fh.read().strip()
            except FileNotFoundError:
                pass

        # No public key found anywhere
        err_msg = f"No public key defined in {self.config_path} or found in " + ", ".join(try_paths)
        raise ProjectError(err_msg, 2)

    def get_pub_key_path(self):
        try_paths = []

        # Path in configuration
        if "pub_key_path" in self.config:
            if self.config["pub_key_path"].startswith("/"):
                # Absolute path
                try_paths.append(self.config["pub_key_path"])
            else:
                # Relative to base dir
                try_paths.append(os.path.join(self.base_path, self.config["pub_key_path"]))

                # Also try expand user path
                try_paths.append(os.path.expanduser(self.config["pub_key_path"]))

        # File relative to base dir
        try_paths.append(os.path.join(self.base_dir, ".lockdown.pub"))

        # Default location (~/.config/lockdown
        try_paths.append(common.xdg_config_home(os.path.join("lockdown", "lockdown.pub")))

        for try_path in try_paths:
            if os.path.exists(try_path):
                return try_path

    def priv_key_readable_by_others(self, path):
        """
        Check if the private key is readable by anybody other than the current
        user or group.
        """
        st = os.stat(path)
        key_readable = bool(st.st_mode & (stat.S_IROTH))

        return key_readable

    def decrypt_priv_key(self):
        """
        Ask the user for a password and decrypt the private key.

        Do NOT use this without a TTY attached to the process.
        """
        while True:
            try:
                password = getpass.getpass(f"Password for {self.priv_key_path}: ")
                with open(self.priv_key_path, "rb") as fh:
                    for line in pyrage.passphrase.decrypt(fh.read(), password).decode("utf-8").splitlines():
                        if line.startswith("AGE-SECRET-KEY-"):
                            key = line.strip()
                            identity = pyrage.x25519.Identity.from_str(key)
                            return identity
            except pyrage.DecryptError as err:
                logger.error("Decryption of '%s' failed: %s", self.priv_key_path, err)

    def status(self):
        """
        Show the status of the current project.
        """
        fully_locked = True

        for lock_file in self.lock_files:
            path_decrypted = os.path.join(self.base_dir, f"{lock_file}")

            if os.path.exists(path_decrypted):
                logger.debug("%s is not locked", lock_file)
                fully_locked = False
            else:
                logger.debug("%s is locked", lock_file)

        if fully_locked is True:
            logger.info(f"Project '{self.base_dir}' is locked")
        else:
            logger.info(f"Project '{self.base_dir}' is not (fully) locked")

    def lock(self):
        """
        Lock all lock files in the project using the public key
        """
        pub_key = pyrage.x25519.Recipient.from_str(self.pub_key)
        fingerprint = hashlib.sha256(str(pub_key).encode("utf-8")).hexdigest()
        logger.info("Using public key '%s' (%s)", self.pub_key_path, fingerprint.upper()[0:16])

        for lock_file in self.lock_files:
            path_decrypted = os.path.join(self.base_dir, f"{lock_file}")
            path_encrypted = os.path.join(self.base_dir, f"{lock_file}.age")

            if os.path.exists(path_encrypted):
                logger.warning(f"'{lock_file}' already locked. Skipping")
                continue

            logger.info(f"Locking '{lock_file}'")
            with open(path_decrypted, "rb") as fh_decrypted:
                encrypted = pyrage.encrypt(fh_decrypted.read(), [pub_key])
                with open(path_encrypted, "wb") as fh_cipher:
                    fh_cipher.write(encrypted)
                os.unlink(path_decrypted)

    def unlock(self):
        """
        Unlock all the lock files in this project using the private key

        Do NOT use this without a TTY attached to the process
        """
        priv_key = self.decrypt_priv_key()

        for lock_file in self.lock_files:
            path_decrypted = os.path.join(self.base_dir, f"{lock_file}")
            path_encrypted = os.path.join(self.base_dir, f"{lock_file}.age")

            if not os.path.exists(path_encrypted):
                print(f"'{lock_file}' not locked. Skipping")
                continue

            logger.info(f"Unlocking '{lock_file}'")
            with open(path_encrypted, "rb") as fh_encrypted:
                decrypted = pyrage.decrypt(fh_encrypted.read(), [priv_key])
                with open(path_decrypted, "wb") as fh_decrypted:
                    fh_decrypted.write(decrypted)

                # We just unlink (rm) the original file. There's no point in
                # secure wipe these days.
                os.unlink(path_encrypted)

    def lock_age(self):
        """
        Return a dict with every lock file (as the key of the dict), with the
        value being the mtime of the file in seconds.

        When lock files are unlocked, they are newly created from the .age
        files, so their mtime indicated how long ago they were unlocked. This
        is used by the daemon to automatically lock them.

        If the user edits one of the lock files, the mtime gets reset, but
        we'll accept that since that does indicate the user is actively working
        on the project.
        """
        lock_file_ages = {}
        for lock_file in self.lock_files:
            full_path = os.path.join(self.base_dir, lock_file)
            if os.path.exists(full_path):
                age_seconds = time.time() - os.path.getmtime(full_path)
                lock_file_ages[full_path] = age_seconds
        return lock_file_ages

    def auto_lock(self, age_sec, skip_if_in_use):
        """
        Automatically lock this project, depending on `age_sec`. See
        `lock_age()` for more info.
        """
        logger.debug("Inspecting '%s' for stale lock files", self.base_dir)
        for lock_file, lock_file_age in self.lock_age().items():
            if lock_file_age > age_sec:
                logger.info("Lock file '%s' older than %s seconds old. Locking project.", lock_file, age_sec)

                if (
                    skip_if_in_use and
                    common.user_session_in_dir(self.base_dir)
                ):
                    logger.info("User has process running in '%s'. Not locking.", self.base_dir)
                    # Continue to next project
                    break

                self.lock()
                # Project was locked
                return True

        # Project was not locked
        return False
