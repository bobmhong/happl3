import hashlib

def hash_command(command):
    return hashlib.md5(command.encode()).hexdigest()