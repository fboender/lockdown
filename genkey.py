import getpass
import sys

import pyrage


def gen_key():
    """
    Generate password protected (encrypted) age private and public key and
    output to stdout.
    """
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
