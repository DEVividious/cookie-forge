"""Errors reported to the user: the CLI prints them and exits with status 1."""


class ForgeError(Exception):
    """A problem with the user's input or files, explained in the message."""


def fail(msg):
    raise ForgeError(msg)
