#!/usr/bin/env python

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

import os
import json
import time
import pause
from time import sleep
from lendingclub import LendingClub, LendingClubError
from lendingclub.filters import *
from lcinvestor import util
from lcinvestor.settings import Settings


class AutoInvestor:
    """
    Regularly check a LendingClub account for available cash and reinvest it
    automatically.
    """

    lc = None
    authed = False
    verbose = False
    auto_execute = True
    settings = None
    loop = False
    app_dir = None

    # The file that the summary from the last investment is saved to
    last_investment_file = 'last_investment.json'

    def __init__(self, verbose=False, auto_execute=True):
        """
        Create an AutoInvestor instance
         - Set verbose to True if you want to see debugging logs
        """
        self.verbose = verbose
        self.auto_execute = auto_execute
        self.logger = util.create_logger(verbose)
        self.app_dir = util.get_app_directory()
        self.lc = LendingClub()

        # Set logger on lc
        if self.verbose:
            self.lc.set_logger(self.logger)

        # Create settings object
        self.settings = Settings(investor=self, settings_dir=self.app_dir, logger=self.logger, verbose=self.verbose)

        self.settings.investor = self  # create a link back to this instance

    def version(self):
        """
        Return the version number of the Lending Club Investor tool
        """
        return util.get_version();

    def welcome_screen(self):
        print "\n///--------------------------- $$$ ---------------------------\\\\\\"
        print '|    Welcome to the unofficial Lending Club investment tool     |'
        print " ---------------------------------------------------------------- \n"

    def get_auth(self):
        print 'To start, we need to log you into Lending Club (your password will never be saved)\n'
        while True:
            self.settings.get_auth_settings()

            print '\nAuthenticating...'
            try:
                return self.authenticate()
            except Exception as e:
                print '\nLogin failed: {0}'.format(str(e.value))
                print "Please try again\n"

    def setup(self):
        """
        Setup the investor to run
        """
        if self.verbose:
            print 'VERBOSE OUTPUT IS ON\n'

        if not self.authed:
            self.get_auth()
            self.settings.select_profile()

        print 'You have ${0} in your account, free to invest\n'.format(self.lc.get_cash_balance())

        # Investment settings
        print 'Now let\'s define what you want to do'

        # Use the settings from last time
        if self.settings.profile_loaded is not False:
            summary = self.settings.show_summary()

            if summary is False: # there was an error with saved settings
                print '\nThere was an error with your saved settings. Please go through the prompts again.\n'
                self.settings.get_investment_settings()

            if util.prompt_yn('Would you like to use these settings?', 'y'):
                self.settings.save()  # to save the email that was just entered
            else:
                self.settings.get_investment_settings()
        else:
            self.settings.get_investment_settings()

        # All ready to start running
        print '\nThat\'s all we need. Now, as long as this is running, your account will be checked every {0} minutes and invested if enough funds are available.\n'.format(self.settings['frequency'])

    def authenticate(self):
        """
        Attempt to authenticate the user with the email/pass from the Settings object.
        This is just a wrapper for LendingClub.authenticate()
        Returns True or raises an exceptions
        """
        self.authed = self.lc.authenticate(self.settings.auth['email'], self.settings.auth['pass'])
        return self.authed

    def run(self):
        """
        Alias for investment_loop.
        This is used by python-runner
        """
        self.investment_loop()

    def run_once(self):
        """
        Try to invest, based on your settings, and then end the program.
        """
        self.loop = False

        # Make sure the site is available
        attempts = 0
        while not self.lc.is_site_available():
            attempts += 1
            if attempts % 5 == 0:
                self.logger.warn('LendingClub is not responding. Trying again in 10 seconds...')
            sleep(10)

        # Invest
        self.attempt_to_invest()

    def stop(self):
        """
        Called when the investment loop should end.
        If the loop is currently attempting to invest cash, this will not be canceled.
        """
        self.loop = False
        self.logger.info("Stopping investor...")

    def get_order_summary(self, portfolio):
        """
        Log a summary of the investment portfolio which was ordered
        """
        summary = 'Investment portfolio summary: {0} loan notes ('.format(portfolio['numberOfLoans'])

        breakdown = []
        for grade in ['a', 'aa', 'b', 'c', 'd', 'e', 'f', 'g']:
            if portfolio[grade] > 0.0:
                percent = int(round(portfolio[grade]))
                breakdown.append('{0}:{1}%'.format(grade.upper(), percent))

        if len(breakdown) > 0:
            summary += ', '.join(breakdown)
            summary += ')'

        return summary

    def attempt_to_invest(self):
        """
        Attempt an investment if there is enough available cash and matching investment option
        Returns true if money was invested
        """

        # Authenticate
        try:
            self.authenticate()
            self.logger.info('Authenticated')
        except Exception as e:
            self.logger.error('Could not authenticate: {0}'.format(e.value))
            return False

        # Try to invest
        self.logger.info('Checking for funds to invest...')
        try:

            # Get current cash balance
            cash = self.lc.get_investable_balance()
            if cash > 0 and cash >= self.settings['min_cash']:

                # Invest
                self.logger.info(" $ $ $ $ $ $ $ $ $ $")  # Create break in logs

                try:
                    # Refresh saved filter
                    filters = self.settings['filters']
                    if type(filters) is SavedFilter:
                        filters.reload()

                    # Find investment portfolio, starting will all your cash,
                    # down to the minimum you're willing to invest
                    # No more than 10 searches
                    i = 0
                    portfolio = False
                    decrement = None
                    while portfolio is False and cash >= self.settings['min_cash'] and i < 10:
                        i += 1

                        # Try to find a portfolio
                        try:

                            self.logger.info('Searching for a portfolio for ${0}'.format(cash))
                            portfolio = self.lc.build_portfolio(cash,
                                max_per_note=self.settings['max_per_note'],
                                min_percent=self.settings['min_percent'],
                                max_percent=self.settings['max_percent'],
                                filters=filters,
                                do_not_clear_staging=True)

                        except LendingClubError as e:
                            pass

                        # Try a lower amount of cash to invest
                        if not portfolio:
                            self.logger.info('Could not find any matching portfolios for ${0}'.format(cash))

                            # Create decrement value that will search up to 5 more times
                            if decrement is None:
                                delta = cash - self.settings['min_cash']

                                if delta < 25:
                                    break
                                elif delta <= 100:
                                    decrement = 25
                                else:
                                    decrement = delta / 4

                            # Just to be safe, shouldn't decrement in $10 increments
                            if decrement < 10:
                                break

                            # We are at our lowest
                            if cash <= self.settings['min_cash']:
                                break

                            # New amount to search for
                            cash -= decrement
                            if cash < self.settings['min_cash']:
                                cash = self.settings['min_cash']
                            else:
                                cash = util.nearest_25(cash)

                    if portfolio:
                        # Invest
                        assign_to = self.settings['portfolio']

                        order = self.lc.start_order()
                        order.add_batch(portfolio['loan_fractions'])

                        if self.auto_execute:
                            self.logger.info('Auto investing ${0} at {1}%...'.format(cash, portfolio['percentage']))
                            sleep(5)  # last chance to cancel

                            order._Order__already_staged = True  # Don't try this at home kids
                            order._Order__i_know_what_im_doing = True  # Seriously, don't do it
                            order_id = order.execute(portfolio_name=assign_to)
                        else:
                            self.logger.info('Order staged but not completed, please to go LendingClub website to complete the order. (see the "--no-auto-execute" command flag)')
                            return False

                        # Success! Show summary and save the order
                        summary = self.get_order_summary(portfolio)
                        self.logger.info(summary)
                        self.logger.info('Done\n')

                        self.save_last_investment(cash, portfolio, order_id, portfolio_name=assign_to)
                    else:
                        self.logger.warning('No investment portfolios matched your filters at this time -- Trying again in {2} minutes'.format(self.settings['min_percent'], self.settings['max_percent'], self.settings['frequency']))

                except Exception as e:
                    self.logger.exception('Failed trying to invest: {0}'.format(str(e)))

            else:
                self.logger.info('Only ${0} available for investing (of your ${1} balance)'.format(cash, self.lc.get_cash_balance()))
                return False

        except Exception as e:
            self.logger.error(str(e))

        return False

    def save_last_investment(self, cash, portfolio, order_id, portfolio_name=None):
        """"
        Save a log of the last investment to the last_investment file
        """
        try:
            last_invested = {
                'timestamp': int(time.time()),
                'order_id': order_id,
                'portfolio': portfolio_name,
                'cash': cash,
                'investment': portfolio
            }

            # Convert to JSON
            json_out = json.dumps(last_invested)
            self.logger.debug('Saving last investment file with JSON: {0}'.format(json_out))

            # Save
            file_path = os.path.join(self.app_dir, self.last_investment_file)
            f = open(file_path, 'w')
            f.write(json_out)
            f.close()
        except Exception as e:
            self.logger.warning('Couldn\'t save the investment summary to file (this warning can be ignored). {0}'.format(str(e)))

    def get_last_investment(self):
        """
        Return the last investment summary that has been saved to the last_investment file
        """
        try:
            file_path = os.path.join(self.app_dir, self.last_investment_file)
            if os.path.exists(file_path):

                # Read file
                f = open(file_path, 'r')
                json_str = f.read()
                f.close()

                # Convert to dictionary and return
                return json.loads(json_str)

        except Exception as e:
            self.logger.warning('Couldn\'t read the last investment file. {0}'.format(str(e)))

        return None

    def investment_loop(self):
        """
        Start the investment loop
        Check the account every so often (default is every 60 minutes) for funds to invest
        The frequency is defined by the 'frequency' value in the ~/.lcinvestor/settings.yaml file
        """
        self.loop = True
        frequency = self.settings.user_settings['frequency']
        while self.loop:

            # Make sure the site is available (network could be reconnecting after sleep)
            attempts = 0
            while not self.lc.is_site_available() and self.loop:
                attempts += 1
                if attempts % 5 == 0:
                    self.logger.warn('LendingClub is not responding. Trying again in 10 seconds...')
                sleep(10)

            # Invest
            self.attempt_to_invest()
            pause.minutes(frequency)


class AutoInvestorError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
