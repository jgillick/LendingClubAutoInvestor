Lending Club Auto Investing Tool
================================

A program that watches your LendingClub account and automatically invests cash as it becomes available based on your personalized investment preferences.


Disclaimer
==========

I have tested this tool to the best of my ability, but understand that it may have bugs. Use at your own risk!


Why?
====

I built this tool to solve the common annoyance when investing money in
LendingClub. When not all the loans get funded, it becomes a two steps
forward, one step back process of reinvesting the cash every few days
until it's all invested. For large sums of money this process can take
over a month to complete.


How it works
============

When running, it will monitor your account for available cash. If the available cash meets or exceeds a minimum amount you define, it's all automatically invested into a collection of loans that match the criteria that you have set (average interest rates, rate grades, term length, etc.). See the *Options* section for information on these settings.

To put it simply, the tool does the same thing as if you were to:

* Log into your account
* Click Invest and select any filters you want to use
* Select an average interest rate portfolio you want to invest in
* Now click Continue and to through the following two pages to invest in that portfolio.


Source
======

Find the latest version on github: https://github.com/jgillick/LendingClubAutoInvestor

Feel free to fork and contribute!

Requirements
============

Python
------
Python 2.6 and 2.7 (does **NOT** support Python 3.x)

Modules
-------
* `lendingclub <https://github.com/jgillick/LendingClub>`_ 0.1.7+ 
* `argparse <https://pypi.python.org/pypi/argparse>`_
* `pyyaml <http://pyyaml.org/wiki/PyYAML>`_
* `pause <https://github.com/jgillick/python-pause>`_
* `keyring <https://pypi.python.org/pypi/keyring>`_ (only for Mac OS X)

These will automatically be installed when using pip.

Optional Modules
----------------
* python-daemon

If this is installed, lcinvestor can be run as a background deamon processes (not supported on windows).


Install (OSX, Linux, Posix)
===========================

The easiest way to install is with pip::

    sudo pip install lcinvestor

Or manually (assuming all required modules are installed on your system)::

    sudo python ./setup.py install


Instructions for Windows
========================

1) Make sure you have Python 2.7 and pip installed
   * http://www.anthonydebarros.com/2011/10/15/setting-up-python-in-windows-7/
2) Open the command prompt: Start Menu > Accessories > Command Prompt
3) Run the following command:: ``pip install lcinvestor``


Running lcinvestor
==================

Foreground
----------

To start the tool in the foreground, open a command line terminal and enter::

    lcinvestor

The script will run continuously and print all the output to the screen until you exit with CTRL+C.

Background Daemon
------------------
**(This is not supported by Windows)**

To run it as a background daemon::

    lcinvestor start

All output will be sent to ``/var/log/daemon.log``.

To stop the daemon run::

    lcinvestor stop


With a JSON config file
-----------------------

You can pass a JSON config file that has your investment criteria and bypass most of the prompts::

    lcinvestor --config ./investing.json

*(See the 'Saved Filters' section below, for how to use existing Lending Club saved searches).*

Here's an example config file (NOTE: Comments are usually not allowed in JSON and are here purely for explanation)::

  {
    // The minimum amount of cash you want to invest each round (at least 25)
    "min_cash": 1000,

    // The minimum average interest rate portfolio that you will accept
    "min_percent": 16.5,

    // The maximum average interest rate portfolio that you will accept
    "max_percent": 19,

    // The most you want to invest in each loan note (must be at least $25)
    "max_per_note": 25,

    // The named portfolio to put all new investments in
    // (only alphanumeric, spaces , _ - # and . are allowed)
    "portfolio": "Autoinvested",

    // Saved filter ID (from LendingClub.com)
    // NOTE: If set, this will override everything in the 'filters' hash, below
    //"filter_id": 123456,

    // Advanced filters
    "filters": {

      // Exclude loans you're already invested in
      "exclude_existing": true,

      // A loan note must be at least this percent funded
      "funding_progress": 90,

      // Include 60 month term loans
      "term60month": true,

      // Include 36 month term loans
      "term36month": true,

      // Loan grades
      "grades": {
        // Allow any loan grade
        "All": true,

        // Or select which loan grades you will accept, A - G
        "A": false,
        "B": false,
        "C": false,
        "D": false,
        "E": false,
        "F": false,
        "G": false
      }
    }
  }

To bypass ALL prompting
-----------------------
You can also pass the command your email and password to bypass all prompts and have it start running right away::

    lcinvestor --config=./investing.json --email=you@email.com --pass=mysecret --quiet

To run it as a daemon, add `start` to the command::

    lcinvestor start --config=./investing.json --email=you@email.com --pass=mysecret --quiet

Help and Usage
--------------

To see the usage info, type ``lcinvestor --help``::

    lcinvestor --help

    usage: lcinvestor [options] [start/stop/status]

    A program that watches your LendingClub account and automatically invests cash
    as it becomes available based on your personalized investment preferences.

    Daemon Commands:
      start/stop/status     Start or stop the this as a background task (daemon).
                            Use status to see the current daemon status

    Options:
      -h, --help            show this help message and exit
      --email EMAIL         The email used to login to LendingClub
      --pass pass           Your LendingClub password.
      --keychain            (MacOS X only) Use MacOS X keychain to store password
      -c CONFIG_FILE, --config CONFIG_FILE
                            A JSON file with the investment settings you want to
                            use.
      -q, --quiet           Don't show a confirmation prompt with your investment
                            settings. Must be used with --config.
      --version             Print the lcinvestor version number
      --run-once            Try to invest and then end the program. (Best used
                            with --config, --email and --pass flags)
      -v, --verbose         Verbose output

Investment Prompts
===================

When you run the tool, it will take you though a series of prompts to define how to invest your cash.

Email / Password
----------------

This is the email and password you use to sign into LendingClub. Your password will be kept in memory but *never* saved to file.

Minimum cash
------------

When the auto investor runs it will attempt to invest **ALL** available cash in your account into a investment portfolio. This option tells the tool how much money should be in the account before investing. i.e. What is the *minimum* amount of cash you want to invest at a time. For example, $25 can only be invested in a single loan note, whereas $1000 could be invested across up to 40 notes.

Min/Max Percent interest rate
-----------------------------

When the minimum available cash option is met, the auto investor will query the LendingClub API and get a list of possible investment portfolios available at that moment. To pick the appropriate one for you, it needs to know what the minimum and maximum *AVERAGE* interest rate value you will accept. The investment option closest to the maximum value will be chosen and all your available cash will be submitted to it.

This value relates to finding a investment portfolio using the slider on the `Invest page <https://www.lendingclub.com/portfolio/autoInvest.action>`_ on LendingClub.com. It's not possible, at any given time, to define an absolute interest rate value, so we need to know the range that you will accept.

**Note** This does *NOT* filter out individual notes based on interest rate. It defines the average interest across all notes. Use the Advanced Filters to filter out notes by loan grade.

Max per note
------------

This is the most you want to invest in any one note (at least $25). The actual amount invested in each loan will vary, but not go above this amount.

Named portfolio
---------------

You can choose to have all new investments assigned to a named portfolio. You can either choose an existing portfolio or create a new one.

Advanced Filters
----------------

The advanced filters section brings in a few of the filters from the `Invest page <https://www.lendingclub.com/portfolio/autoInvest.action>`_ on LendingClub, such as:

* Filter by loan grade (A - G)
* Exclude loans you're already invested in
* Include loans by their funding progress
* Filter by term length (36 - 60 months)

Saved Filters
-------------
You can used any of your saved filters on Lending Club in the tool, instead of defining them manually. This will give you finer control over what you're investing in and provide search options not supported in the lcinvestor tool.

Go to LendingClub.com, click Browse Notes and define your search filters there. When you're done click 'Save' and give it a name. Now run `lcinvestor` and when it asks you "Would you like to select one of your saved filters...", enter `Y` and choose your filter from the list.

Final Review
------------

After all the options are set, you will be given a review screen to verify those values. If you approve, type ``Y + <Enter>`` to start the program. It will now check your account every 30 minutes to see if there is enough available cash in your account to invest.


Tips and Tricks
===============

Running at a specific time
--------------------------
What if you want to invest at an exact time? For example, you want to setup the program to run when that Lending Club releases new loans. 

You can do this by scheduling a task on your system to call the tool command with the `--run-once` flag (along with the `--email`, `--pass`, `--config` and `--quiet` flags). This will run the program immediately and then end. **NOTE** Forgetting to use the `--run-once` flag will cause the program to continue running in the background and can cause big problems.

Example of the command to call::

    lcinvestor --config=./investing.json --email=you@email.com --pass=mysecret --quiet --run-once

Using Mac OS X Keychain for extra security
------------------------------------------

If you prefer to use Mac OS X keychain instead of passing ``--pass`` argument, you can use ``--keychain``.
In order to use this option, set up a new Keychain Item with Name and Account Name "LendingClub"

.. image:: keychain.png
   :target: https://monosnap.com/file/JiMjHItWA2I6kxgMAeGALMobPj3Qbg.png

How to schedule a command or task
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On OS X or Linux you'll use `crontab <http://www.pantz.org/software/cron/croninfo.html>`_.

On Windows you'll setup a `Task Scheduler <http://technet.microsoft.com/en-us/library/cc748993.aspx>`_ or the `at command <http://technet.microsoft.com/en-us/library/bb726974.aspx>`_

Help out
========

Please help me by forking and committing enhancements!


License
=======
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
