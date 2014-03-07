#!/usr/bin/env python

#
# Utilities used by the LendingClubInvestor
#

"""
The MIT License (MIT)

Copyright (c) 2013 Jeremy Gillick

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import re
import os
import logging
import getpass

logger = None


def get_app_directory():
    """
    Setup and return the path to the directory that holds all the user settings and files for this app (~/.lcinvestor/).
    """

    app_dir = os.path.join(os.path.expanduser('~'), '.lcinvestor')
    if os.path.exists(app_dir) and not os.path.isdir(app_dir):
        raise AutoInvestorUtilError('The path \'{0}\' is not a directory.'.format(app_dir))
    elif not os.path.exists(app_dir):
        os.mkdir(app_dir)

    return app_dir


def create_logger(verbose=False):
    """
    Initialize a logger for the autoinvestor
    """
    global logger

    if logger is None:
        logger = logging.getLogger('investor')
        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        logHandler = logging.StreamHandler()
        if verbose:
            logHandler.setFormatter(logging.Formatter('%(levelname)s:\t%(asctime)s - %(message)s (line #%(lineno)d)', '%m-%d %H:%M'))
        else:
            logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s - %(message)s', '%Y-%m-%d %H:%M'))

        logger.addHandler(logHandler)

    return logger


def set_logger(loggerObj):
    global logger
    logger = loggerObj

def get_password():
    """
    Wrapper for getpass.getpas that can be overridden for unit testing
    """
    return getpass.getpass()

def get_version():
    """
    Return the lcinvestor version number
    """
    this_path = os.path.dirname(os.path.realpath(__file__))
    version_file = os.path.join(this_path, 'VERSION')
    return open(version_file).read().strip()

def get_input(msg):
    """
    Wrapper for raw_input that can be overridden for unit testing
    """
    return raw_input(msg)


def prompt(msg, prefill=False):
    """
    Prompt the user for input and return the prefill value if the user does not enter anything
    """
    if prefill is not False:
        msg = "{0} [{1}]: ".format(msg, str(prefill))
    else:
        msg = "{0}: ".format(msg)

    response = get_input(msg)
    if response.strip() == '' and prefill is not False:
        return prefill
    else:
        return response.strip()


def prompt_float(msg, prefill=False):
    """ Prompts the user for an decimal response """
    while(True):
        response = prompt(msg, prefill)

        # Remove commas and symbol suffix/prefix
        if type(response) == str:
            response = response.replace(',', '')
            response = re.sub('^([^0-9]*)|([^0-9]*)$', '', response)

        if type(response) == float:
            return response
        if not isfloat(response):
            print 'The value you entered must be a whole number, without symbols or decimal points'
        else:
            return float(response)

def prompt_int(msg, prefill=False):
    """ Prompts the user for an integer response """
    while(True):
        response = prompt(msg, prefill)

        # Remove commas and symbol suffix/prefix
        if type(response) == str:
            response = response.replace(',', '')
            response = re.sub('^([^0-9]*)|([^0-9]*)$', '', response)

        # Validate response
        if type(response) == int:
            return response
        if not response.isdigit():
            print 'The value you entered must be a whole number, without symbols or decimal points'
        else:
            return int(response)

def prompt_yn(msg, default=None):
    """
    Prompts the user for a y/n response.
    default param should be either 'y' or 'n'
    Returns True if 'Y' and False if 'N'
    """
    if default is True:
        default = 'y'
    elif default is False:
        default = 'n'

    if default == 'y' or default is True:
        msg = "{0} [Y/n]: ".format(msg)
    elif default == 'n':
        msg = "{0} [y/N]: ".format(msg)
    else:
        msg = "{0} [y/n]: ".format(msg)

    while(True):
        response = get_input(msg)

        # Normalize response
        response = response.lower().strip()
        if response == '' and default is not False:
            response = default

        # Return if valid
        if response in ['y', 'yes'] or response is True:
            return True
        elif response in ['n', 'no']:
            return False


def nearest_25(num):
    """
    Round the number to the nearest whole number dividable by 25.
    This will round up or down, to find the closest number

    Examples:
    ---------

        >>> nearest_25(5)
        0
        >>> nearest_25(25)
        25
        >>> nearest_25(40)
        50
        >>> nearest_25(810)
        800
    """
    num = float(num) / 100
    num = round(num * 4) / 4
    num = num * 100
    return int(num)


def currency_to_float(cashValue):
    """
    Converts a currency value, with or without symbols, to a floating point number,
    Returns -1.0, if the string is not a number or currency value
    """
    cash = -1.0
    try:
        # Match values like $1,000.12 or 1,0000$
        cashMatch = re.search('^[^0-9]?([0-9\.,]+)[^0-9]?', cashValue)
        if cashMatch:
            cashStr = cashMatch.group(1)
            cashStr = cashStr.replace(',', '')
            cash = float(cashStr)
    except Exception as e:
        logger.error('Could not convert the currency value \'{0}\' to a float number. Error: {1}'.format(cashValue, str(e)))

    return cash


def isfloat(string):
    """
    Returns true if the string can be cast to a float
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


class AutoInvestorUtilError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
