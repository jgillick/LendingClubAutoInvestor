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
import requests
import getpass
from pybars import Compiler
from bs4 import BeautifulSoup
from requests.exceptions import *

baseUrl = 'https://www.lendingclub.com/'
logger = None

session = requests.Session()
cookies = {}
requestHeaders = {
    'Referer': 'https://www.lendingclub.com/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31'
}


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
            logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s #%(lineno)d - %(message)s', '%Y-%m-%d %H:%M'))
        else:
            logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s - %(message)s', '%Y-%m-%d %H:%M'))

        logger.addHandler(logHandler)

    return logger


def is_site_available():
    """
    Returns true if we can access LendingClub.com
    This is also a simple test to see if there's an internet connection
    """
    try:
        response = requests.head(baseUrl, headers=requestHeaders)
        status = response.status_code
        return 200 <= status < 400
    except Exception:
        return False


def start_session(email, password):
    """
    Login user to LendingClub and preserve the user session for future requests
    This will raise an exception if the login appears to have failed.

    The problem is that LendingClub doesn't seem to have a login API that we can access directly,
    so the code has to try to decide if the login worked or not.
    """
    global session

    try:
        session = requests.Session()
        session.headers = requestHeaders

        url = '{0}{1}'.format(baseUrl, '/account/login.action')
        url = re.sub('([^:])//', '\\1/', url)  # Remove double slashes
        payload = {
            'login_email': email,
            'login_password': password
        }
        response = session.post(url, data=payload, allow_redirects=False)

        # Get URL endpoint
        responseUrl = response.url
        if response.status_code == 302:
            responseUrl = response.headers['location']
        endpoint = responseUrl.split('/')[-1]

        # Debugging
        logger.debug('Status code: {0}'.format(response.status_code))
        logger.debug('Redirected to: {0}'.format(responseUrl))
        logger.debug('Cookies: {0}'.format(str(response.cookies.keys())))

        # Parse any errors
        soup = BeautifulSoup(response.text, "html5lib")
        errors = soup.find(id='master_error-list')
        if errors:
            errors = errors.text.strip()

            # Remove extra spaces and newlines from error message
            errors = re.sub('\t+', '', errors)
            errors = re.sub('\s*\n+\s*', ' * ', errors)

            if errors == '':
                errors = None

        # Raise error
        if errors is not None:
            raise Exception(errors)

        # Redirected back to the login page...must be an error
        if endpoint == 'login.action':
            raise Exception('An unknown error occurred')

    except (RequestException, ConnectionError, TooManyRedirects, HTTPError) as e:
        raise Exception('Could not get login from: {0}\n{1}'.format(url, str(e)))
    except Timeout:
        raise Exception('Timed out trying login using: {0}'.format(url))

    return True


def post_url(relUrl, params={}, data={}, useCookies=True):
    """
    Sends POST request to the relative URL of www.lendingclub.com
    """
    global cookies, session

    url = '{0}{1}'.format(baseUrl, relUrl)
    try:
        url = re.sub('([^:])//', '\\1/', url)  # Remove double slashes
        cookies = cookies if useCookies else {}

        logger.debug('POSTING {0}'.format(url))
        req = session.post(url, params=params, data=data, cookies=cookies)
        return req

    except (RequestException, ConnectionError, TooManyRedirects, HTTPError) as e:
        raise Exception('Could not post to: {0}\n{1}'.format(url, str(e)))
    except Timeout:
        raise Exception('Timed out trying to post to: {0}'.format(url))

    return False


def get_url(relUrl, params={}, useCookies=True):
    """
    Sends GET request to the relative URL of www.lendingclub.com
    """
    global cookies, session

    url = '{0}{1}'.format(baseUrl, relUrl)
    try:
        url = re.sub('([^:])//', '\\1/', url)  # Remove double slashes
        cookies = cookies if useCookies else {}

        logger.debug('GETTING {0}'.format(url))
        req = session.get(url, params=params, cookies=cookies)
        return req

    except (RequestException, ConnectionError, TooManyRedirects, HTTPError) as e:
        raise Exception('Could not get URL "{0}" with {1}\n{2}'.format(url, str(params), str(e)))
    except Timeout:
        raise Exception('Timed out trying to get URL "{0}" with {1}'.format(url, str(params)))

    return False


def get_password():
    """
    Wrapper for getpass.getpas that can be overridden for unit testing
    """
    return getpass.getpass()


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


def get_filter_json(filters):
    """"
    Given search filters, this function returns the JSON that
    LendingClub expects for it's investment search
    """
    compiler = Compiler()

    if not filters:
        return False

    tmpl_source = u"""
    [
        {
            "m_id": 39,
            "m_metadata": {
                "m_controlValues": [
                    {
                        "value": "Year3",
                        "label": "36-month",
                        "sqlValue": null,
                        "valueIndex": 0
                    },
                    {
                        "value": "Year5",
                        "label": "60-month",
                        "sqlValue": null,
                        "valueIndex": 1
                    }
                ],
                "m_type": "MVAL",
                "m_rep": "CHKBOX",
                "m_label": "Term (36 - 60 month)",
                "id": 39,
                "m_onHoverHelp": "Select the loan maturities you are interested to invest in",
                "m_className": "classname",
                "m_defaultValue": [
                    {
                        "value": "Year3",
                        "label": "36-month",
                        "sqlValue": null,
                        "valueIndex": 0
                    },
                    {
                        "value": "Year5",
                        "label": "60-month",
                        "sqlValue": null,
                        "valueIndex": 1
                    }
                ]
            },
            "m_value": [
            {{#if term36month}}
                {
                    "value": "Year3",
                    "label": "36-month",
                    "sqlValue": null,
                    "valueIndex": 0
                },
            {{/if}}
            {{#if term60month}}
                {
                    "value": "Year5",
                    "label": "60-month",
                    "sqlValue": null,
                    "valueIndex": 1
                }
            {{/if}}
            ],
            "m_visible": false,
            "m_position": 0
        },
        {
            "m_id": 38,
            "m_metadata": {
                "m_controlValues": [
                    {
                        "value": true,
                        "label": "Exclude loans invested in",
                        "sqlValue": null,
                        "valueIndex": 0
                    }
                ],
                "m_type": "SVAL",
                "m_rep": "CHKBOX",
                "m_label": "Exclude Loans already invested in",
                "id": 38,
                "m_onHoverHelp": "Use this filter to exclude loans from a borrower that you have already invested in.",
                "m_className": "classname",
                "m_defaultValue": [
                    {
                        "value": true,
                        "label": "Exclude loans invested in",
                        "sqlValue": null,
                        "valueIndex": 0
                    }
                ]
            },
            "m_value": [
            {{#if exclude_existing}}
                {
                    "value": true,
                    "label": "Exclude loans invested in",
                    "sqlValue": null,
                    "valueIndex": 0
                }
            {{/if}}
            ],
            "m_visible": false,
            "m_position": 0
        },
        {{#if funding_progress}}
        {
            "m_id": 15,
            "m_metadata": {
              "m_controlValues": [
                {
                  "value": 0,
                  "label": "0%",
                  "sqlValue": null,
                  "valueIndex": 0
                },
                {
                  "value": 10,
                  "label": "10%",
                  "sqlValue": null,
                  "valueIndex": 1
                },
                {
                  "value": 20,
                  "label": "20%",
                  "sqlValue": null,
                  "valueIndex": 2
                },
                {
                  "value": 30,
                  "label": "30%",
                  "sqlValue": null,
                  "valueIndex": 3
                },
                {
                  "value": 40,
                  "label": "40%",
                  "sqlValue": null,
                  "valueIndex": 4
                },
                {
                  "value": 50,
                  "label": "50%",
                  "sqlValue": null,
                  "valueIndex": 5
                },
                {
                  "value": 60,
                  "label": "60%",
                  "sqlValue": null,
                  "valueIndex": 6
                },
                {
                  "value": 70,
                  "label": "70%",
                  "sqlValue": null,
                  "valueIndex": 7
                },
                {
                  "value": 80,
                  "label": "80%",
                  "sqlValue": null,
                  "valueIndex": 8
                },
                {
                  "value": 90,
                  "label": "90%",
                  "sqlValue": null,
                  "valueIndex": 9
                },
                {
                  "value": 100,
                  "label": "100%",
                  "sqlValue": null,
                  "valueIndex": 10
                }
              ],
              "m_type": "SVAL",
              "m_rep": "SLIDER",
              "m_label": "Funding Progress",
              "id": 15,
              "m_onHoverHelp": "Specify a minimum funding level percentage desired.",
              "m_className": "classname",
              "m_defaultValue": [
                {
                  "value": 0,
                  "label": "0%",
                  "sqlValue": null,
                  "valueIndex": 0
                }
              ]
            },
            "m_value": [
              {
                "value": {{funding_progress}},
                "label": "{{funding_progress}}%",
                "sqlValue": null,
                "valueIndex": 1
              }
            ],
            "m_visible": false,
            "m_position": 0
        },
        {{/if}}
        {
            "m_id": 10,
            "m_metadata": {
                "m_controlValues": [
                    {
                        "value": "All",
                        "label": "All",
                        "sqlValue": null,
                        "valueIndex": 0
                    },
                    {
                        "value": "D",
                        "label": "<span class=\\"grades d-loan-grade\\">D</span> 18.76%",
                        "sqlValue": null,
                        "valueIndex": 1
                    },
                    {
                        "value": "A",
                        "label": "<span class=\\"grades a-loan-grade\\">A</span> 7.41%",
                        "sqlValue": null,
                        "valueIndex": 2
                    },
                    {
                        "value": "E",
                        "label": "<span class=\\"grades e-loan-grade\\">E</span> 21.49%",
                        "sqlValue": null,
                        "valueIndex": 3
                    },
                    {
                        "value": "B",
                        "label": "<span class=\\"grades b-loan-grade\\">B</span> 12.12%",
                        "sqlValue": null,
                        "valueIndex": 4
                    },
                    {
                        "value": "F",
                        "label": "<span class=\\"grades f-loan-grade\\">F</span> 23.49%",
                        "sqlValue": null,
                        "valueIndex": 5
                    },
                    {
                        "value": "C",
                        "label": "<span class=\\"grades c-loan-grade\\">C</span> 15.80%",
                        "sqlValue": null,
                        "valueIndex": 6
                    },
                    {
                        "value": "G",
                        "label": "<span class=\\"grades g-loan-grade\\">G</span> 24.84%",
                        "sqlValue": null,
                        "valueIndex": 7
                    }
                ],
                "m_type": "MVAL",
                "m_rep": "CHKBOX",
                "m_label": "Interest Rate",
                "id": 10,
                "m_onHoverHelp": "Specify the interest rate ranges of the notes  you are willing to invest in.",
                "m_className": "short",
                "m_defaultValue": [
                    {
                        "value": "All",
                        "label": "All",
                        "sqlValue": null,
                        "valueIndex": 0
                    }
                ]
            },
            "m_value": [
            {{#if grades.All }}
                {
                    "value": "All",
                    "label": "All",
                    "sqlValue": null,
                    "valueIndex": 0
                }
            {{else}}
                {{#if grades.D}}
                {
                    "value": "D",
                    "label": "<span class=\\"grades d-loan-grade\\">D</span> 18.76%",
                    "sqlValue": null,
                    "valueIndex": 1
                },
                {{/if}}
                {{#if grades.A}}
                {
                    "value": "A",
                    "label": "<span class=\\"grades a-loan-grade\\">A</span> 7.41%",
                    "sqlValue": null,
                    "valueIndex": 2
                },
                {{/if}}
                {{#if grades.E}}
                {
                    "value": "E",
                    "label": "<span class=\\"grades e-loan-grade\\">E</span> 21.49%",
                    "sqlValue": null,
                    "valueIndex": 3
                },
                {{/if}}
                {{#if grades.B}}
                {
                    "value": "B",
                    "label": "<span class=\\"grades b-loan-grade\\">B</span> 12.12%",
                    "sqlValue": null,
                    "valueIndex": 4
                },
                {{/if}}
                {{#if grades.F}}
                {
                    "value": "F",
                    "label": "<span class=\\"grades f-loan-grade\\">F</span> 23.49%",
                    "sqlValue": null,
                    "valueIndex": 5
                },
                {{/if}}
                {{#if grades.C}}
                {
                    "value": "C",
                    "label": "<span class=\\"grades c-loan-grade\\">C</span> 15.80%",
                    "sqlValue": null,
                    "valueIndex": 6
                },
                {{/if}}
                {{#if grades.G}}
                {
                    "value": "G",
                    "label": "<span class=\\"grades g-loan-grade\\">G</span> 24.84%",
                    "sqlValue": null,
                    "valueIndex": 7
                }
                {{/if}}
            {{/if}}
            ],
            "m_visible": false,
            "m_position": 0
        },
        {
            "m_id": 37,
            "m_metadata": {
                "m_controlValues": null,
                "m_type": "SVAL",
                "m_rep": "TEXTBOX",
                "m_label": "Keyword",
                "id": 37,
                "m_onHoverHelp": "Type any keyword",
                "m_className": "classname",
                "m_defaultValue": []
            },
            "m_value": null,
            "m_visible": false,
            "m_position": 0
        }
    ]
    """

    template = compiler.compile(tmpl_source)
    out = template(filters)
    if not out:
        return False
    out = ''.join(out)

    # remove extra spaces
    out = re.sub('\n', '', out)
    out = re.sub('\s{3,}', ' ', out)

    # Remove hanging commas i.e: [1, 2,]
    out = re.sub(',\s*([}\\]])', '\\1', out)

    # Space between brackets i.e: ],  [
    out = re.sub('([{\\[}\\]])(,?)\s*([{\\[}\\]])', '\\1\\2\\3', out)

    # Cleanup spaces around [, {, }, ], : and , characters
    out = re.sub('\s*([{\\[\\]}:,])\s*', '\\1', out)

    return out


class AutoInvestorUtilError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)