#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re

from . import exceptions
from . import file_utils


_hostname_regex = re.compile(r"(?!-)[\w-]{1,63}(?<!-)$")


def is_valid_host(host):
    """IDN compatible domain validation.

    Parameters
    ----------
    host : str
        The host name to check.

    Returns
    -------
    bool
        Whether the host name is valid or not.

    Note
    ----
    Based on: `Validate-a-hostname-string \
    <https://stackoverflow.com/questions/2532053/validate-a-hostname-string>`__
    """
    host = host.rstrip(".")

    return all([len(host) > 1,
                len(host) < 253] + [_hostname_regex.match(x) for x in host.split(".")])


def validate_output_path(x):
    """Validate output path.

    Checks that a given path is not a user's home folder nor "/".

    Parameters
    ----------
    x : str
        The entered option to validate.

    Returns
    -------
    str
        The validated option.

    Raises
    ------
    exceptions.ValidationError
        Halt execution if option is not valid.
    """
    if x == file_utils.expand_path("~") or x == "~":
        raise exceptions.ValidationError("Seriously, don't be daft! Choose another location!")
    elif x == "/":
        raise exceptions.ValidationError(
            "Are you freaking kidding me!? The root partition!? Use your brain!")

    return x


def validate_options_1_2(x):
    """Validate 1 or 2.

    Parameters
    ----------
    x : str
        The entered option to validate.

    Returns
    -------
    str
        The validated option.

    Raises
    ------
    exceptions.ValidationError
        Halt execution if option is not valid.
    """
    if not x or x not in ["1", "2"]:
        raise exceptions.ValidationError('Possible options are "1" or "2".')

    return x


def validate_options_1_2_3(x):
    """Validate 1, 2 or 3.

    Parameters
    ----------
    x : str
        The entered option to validate.

    Returns
    -------
    str
        The validated option.

    Raises
    ------
    exceptions.ValidationError
        Halt execution if option is not valid.
    """
    if not x or x not in ["1", "2", "3"]:
        raise exceptions.ValidationError('Possible options are "1", "2" or "3".')

    return x


if __name__ == "__main__":
    pass
