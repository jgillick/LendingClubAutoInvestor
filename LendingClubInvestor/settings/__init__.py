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

import re
import os
import shutil
import yaml
import json
from lendingclub.filters import Filter, SavedFilter
from LendingClubInvestor import util


class Settings():
    """
    Handles all the user and investment settings
    """

    logger = None
    investor = None

    # Files
    settings_dir = None  # The directory that holds all the settings files
    settings_file = 'settings.yaml'  # User settings
    investing_file = 'investing.json'  # Investment settings

    # Auth settings
    auth = {
        'email': False,
        'pass': None
    }

    # Defines the investment funding settings
    investing = {
        'min_cash': 500,
        'min_percent': False,
        'max_percent': False,
        'portfolio': None,
        'filters': Filter()
    }

    # If the investing settings have been updated
    # False: The settings are still set to the defaults
    # True: The settings have been updated by the user or file
    is_dirty = False

    # Default user settings
    user_settings = {
        'frequency': 60,
        'alert': False
    }

    def __init__(self, investing_file=None, settings_dir=None, logger=False, verbose=False):
        """
        file: A JSON file will the settings to use. Setting this parameter will prevent
              saving settings to the cache file.
        settings_dir: The directory that will be used to save the user and investment settings files
        """
        self.settings_dir = settings_dir

        # Create logger if none was passed in
        if not logger:
            self.logger = util.create_logger(verbose)
        else:
            self.logger = logger

        # Create the settings directory, if it doesn't exist
        if investing_file is None and self.settings_dir is not None and not os.path.exists(self.settings_dir):
            os.mkdir(self.settings_dir)

        self.get_user_settings()
        self.load_investment_settings_file(file_path=investing_file)

    def __getitem__(self, key):
        """
        Attempts to a value from one of the dictionaries
        """
        if key in self.investing:
            return self.investing[key]
        if key in self.user_settings:
            return self.user_settings[key]
        if key in self.auth:
            return self.auth[key]
        return None

    def __setitem__(self, key, value):
        """
        Add a setting
        """
        if key in self.investing:
            self.investing[key] = value
            self.is_dirty = True
        elif key in self.user_settings:
            self.user_settings[key] = value
        elif key in self.auth:
            self.auth[key] = value

    def get_user_settings(self):
        """
        Load the settings.yaml file into memory.
        If this file doesn't exist, create in
        """
        if not self.settings_dir:
            return

        file_path = os.path.join(self.settings_dir, self.settings_file)

        # Create the file, if it doesn't exist
        if not os.path.exists(file_path):
            this_path = os.path.dirname(os.path.realpath(__file__))
            default_file = os.path.join(this_path, 'settings.yaml')
            shutil.copy2(default_file, file_path)

        # Read file
        self.user_settings = yaml.load(open(file_path).read())
        return self.user_settings

    def process_json(self, jsonStr):
        """
        Preprocess a JSON string.
        Currently this simply removes all single line comments
        """

        # Remove comment lines
        jsonStr = re.sub(r'\n\s*//.*?\n', '\n', jsonStr)

        return jsonStr

    def save(self):
        """
        Save the investment settings dict to a file
        """
        if self.settings_dir is None:
            return

        try:
            # Convert to JSON (and add email)
            to_save = self.investing.copy()
            to_save['email'] = self.auth['email']
            json_out = json.dumps(to_save)

            # Save
            self.logger.debug('Saving investment settings file: {0}'.format(json_out))
            investing_file = os.path.join(self.settings_dir, self.investing_file)
            f = open(investing_file, 'w')
            f.write(json_out)
            f.close()

            self.logger.debug('Saved')
        except Exception as e:
            self.logger.warning('Could not save the investment settings to file: {0}'.format(str(e)))

    def migrate_settings(self, settings):
        """
        Migrate old settings to what they should be now
        """

        # Investing filters
        if settings['filters']:

            if 'term' not in settings['filters']:
                settings['filters']['term'] = {}

            if '36month' in settings['filters']:
                settings['filters']['term']['Year3'] = settings['filters']['36month']
                del settings['filters']['36month']
            if 'term60month' in settings['filters']:
                settings['filters']['term']['Year3'] = settings['filters']['term36month']
                del settings['filters']['term36month']

            if '60month' in settings['filters']:
                settings['filters']['term']['Year5'] = settings['filters']['60month']
                del settings['filters']['60month']
            if 'term60month' in settings['filters']:
                settings['filters']['term']['Year5'] = settings['filters']['term60month']
                del settings['filters']['term60month']

            if 'minPercent' in settings:
                settings['min_percent'] = settings['minPercent']
                del settings['minPercent']
            if 'maxPercent' in settings:
                settings['max_percent'] = settings['maxPercent']
                del settings['maxPercent']

            if 'minCash' in settings:
                settings['min_cash'] = settings['minCash']
                del settings['minCash']

        return settings

    def load_investment_settings_file(self, file_path=None):
        """
        Returned the saved settings used last time this program was run
        """
        if not self.settings_dir and file_path is None:
            return False

        if file_path is None:
            file_path = os.path.join(self.settings_dir, self.investing_file)

        if os.path.exists(file_path):
            self.logger.debug('Loading investment settings file: {0}'.format(file_path))
            try:
                # Read file
                f = open(file_path, 'r')
                jsonStr = f.read()
                f.close()

                self.logger.debug('Investment settings JSON: {0}'.format(jsonStr))

                # Convert JSON to dictionary
                jsonStr = self.process_json(jsonStr)
                saved_settings = json.loads(jsonStr)

                # Migrations
                saved_settings = self.migrate_settings(saved_settings)

                # Add values to dictionary
                for key, value in self.investing.iteritems():
                    if key in saved_settings:
                        self.investing[key] = saved_settings[key]
                        self.is_dirty = True

                # Add email to auth
                if 'email' in saved_settings:
                    self.auth['email'] = saved_settings['email']

            except Exception as e:
                self.logger.debug('Could not read investment settings file: {0}'.format(str(e)))
                print jsonStr
                raise Exception('Could not process file \'{0}\': {1}'.format(file_path, str(e)))

            # Create filter object
            try:
                if self.investing['filters'] and len(self.investing['filters']) > 0:
                    self.investing['filters'] = Filter(filters=self.investing['filters'])
                else:
                    self.investing['filters'] = False
            except Exception as e:
                raise Exception('Could load filter settings: {0}'.format(str(e)))

            return True
        else:
            self.logger.debug('The file \'{0}\' doesn\'t exist'.format(file_path))

        return False

    def get_auth_settings(self):
        """
        Get the email and password from the user
        """
        self.auth['email'] = util.prompt('LendingClub email', self.auth['email'])
        self.auth['pass'] = util.get_password()
        return self.auth

    def show_summary(self, title='Summary'):
        """
        Show a summary of the settings that will be used for auto investing
        """

        print '\n========= {0} ========='.format(title)
        print 'Invest ALL available funds with the following criteria\n'
        print 'With at LEAST ${0} available to invest'.format(self.investing['min_cash'])
        print 'Select a portfolio with an average interest rate between {0}% - {1}%'.format(self.investing['min_percent'], self.investing['max_percent'])

        if self.investing['portfolio']:
            print 'Add investments to: "{0}"'.format(self.investing['portfolio'])

        # Filters
        if self.investing['filters'] is not False:
            print '\nAdvanced filters:'

            # Exclude existing
            if self.investing['filters']['exclude_existing']:
                print '  + Exclude loans already invested in'

            # Funding progress
            if self.investing['filters']['funding_progress'] > 0:
                print '  + Only loans which are at least {0}% funded'.format(self.investing['filters']['funding_progress'])

            # Loan term
            terms = []
            if self.investing['filters']['term']['Year3'] is True:
                terms.append('36')
            if self.investing['filters']['term']['Year5'] is True:
                terms.append('60')
            print '  + Term: {0} months'.format(' & '.join(terms))

            # Interest rate grades
            if self.investing['filters']['grades']['All']:
                print '  + All interest rate grades'
            else:
                grades = []
                for grade in self.investing['filters']['grades']:
                    if grade != 'All' and self.investing['filters']['grades'][grade] is True:
                        grades.append(grade)
                print '  + Interest rates grades: {0}'.format(', '.join(sorted(grades)))

        print '=========={0}==========\n'.format(''.center(len(title), '='))

    def confirm_settings(self):
        self.show_summary()
        if util.prompt_yn('Would you like to continue with these settings?', 'y'):
            self.save()
        else:
            self.get_investment_settings()

    def get_investment_settings(self):
        """
        Display a series of prompts to get how the user wants to invest their available cash.
        This fills out the investing dictionary.
        """

         # Minimum cash
        print '---------'
        print 'The auto investor will automatically try to invest ALL available cash into a diversified portfolio'
        while(True):
            self.investing['min_cash'] = util.prompt_int('What\'s the MINIMUM amount of cash you want to invest each round?', self.investing['min_cash'])
            if self.investing['min_cash'] < 25:
                print '\nYou cannot invest less than $25. Please try again.'
            else:
                break

        # Min/max percent
        print '---------'
        while(True):
            print 'When auto investing, the LendingClub API will search for diversified investment portfolios available at that moment.'
            print 'To pick the appropriate one for you, it needs to know what the minimum and maximum AVERAGE interest rate value you will accept.'
            print 'The investment option closest to the maximum value will be chosen and all your available cash will be invested in it.\n'

            self.investing['min_percent'] = util.prompt_float('What\'s MININUM average interest rate portfolio that you will accept?', self.investing['min_percent'])

            # Max percent should default to being larger than the min percent
            if self.investing['max_percent'] is False or self.investing['max_percent'] < self.investing['min_percent']:
                self.investing['max_percent'] = self.investing['min_percent'] + 1
            self.investing['max_percent'] = util.prompt_float('What\'s MAXIMUM average interest rate portfolio that you will accept?', self.investing['max_percent'])

            # Validation
            if self.investing['max_percent'] < self.investing['min_percent']:
                print 'The maximum value must be larger than, or equal to, the minimum value. Please try again.'
            elif self.investing['max_percent'] == self.investing['min_percent']:
                print 'It\'s very uncommon to find an available portfolio that will match an exact percent.'
                if not util.prompt_yn('Would you like to specify a broader range?'):
                    break
            else:
                break

        # Portfolio
        print '---------'
        folioOption = False
        if self.investing['portfolio']:  # if saved settings has a portfolio set, default the prompt to 'Y' to choose
            folioOption = 'y'

        if util.prompt_yn('Do you want to put your new investments into a named portfolio?', folioOption):
            self.investing['portfolio'] = self.portfolio_picker(self.investing['portfolio'])
        else:
            self.investing['portfolio'] = False

        print '\n---------'

        # Using saved filter
        if type(self.investing['filters']) is SavedFilter:
            print 'Using saved filter {0}: {1}'.format(self.investing['filters'].id, self.investing['filters'].name)
            util.prompt('FYI: No custom advanced filters can best set while using a saved filter [enter]')

        # Advanced filter settings
        else:
            if util.prompt_yn('Would you like to set advanced filter settings?', self.investing['filters'] is not False):
                self.get_filter_settings()

        # Review summary
        self.confirm_settings()
        return True

    def get_filter_settings(self):
        """
        Setup the advanced portfolio filters (terms, grades, existing notes, etc.)
        """
        filters = Filter()

        print 'The following questions are from the filters section of the Invest page on LendingClub\n'

        # Existing loans
        filters['exclude_existing'] = util.prompt_yn('Exclude loans already invested in?', filters['exclude_existing'])

        # Funding progress rounded to the nearest tenth
        print '---------'
        print 'Funding progress'
        progress = util.prompt_float('Only include loans which already have at least __% funding (0 - 100)', filters['funding_progress'])
        filters['funding_progress'] = int(round(progress / 10) * 10)

        print '---------'
        print 'Choose term (36 - 60 month)'

        while(True):
            filters['term']['Year3'] = util.prompt_yn('Include 36 month term loans?', filters['term']['Year3'])
            filters['term']['Year5'] = util.prompt_yn('Include 60 month term loans?', filters['term']['Year5'])

            # Validate 1 was chosen
            if not filters['term']['Year3'] and not filters['term']['Year5']:
                print 'You have to AT LEAST choose one term length!'
            else:
                break

        print '---------'
        print 'Choose interest rate grades (7.4% - 24.84%)'
        while(True):
            if util.prompt_yn('Include ALL interest rate grades', filters['grades']['All']):
                filters['grades']['All'] = True
            else:
                filters['grades']['All'] = False
                filters['grades']['A'] = util.prompt_yn('A - ~7.41%', filters['grades']['A'])
                filters['grades']['B'] = util.prompt_yn('B - ~12.12%', filters['grades']['B'])
                filters['grades']['C'] = util.prompt_yn('C - ~15.80%', filters['grades']['C'])
                filters['grades']['D'] = util.prompt_yn('D - ~18.76%', filters['grades']['D'])
                filters['grades']['E'] = util.prompt_yn('E - ~21.49%', filters['grades']['E'])
                filters['grades']['F'] = util.prompt_yn('F - ~23.49%', filters['grades']['F'])
                filters['grades']['G'] = util.prompt_yn('G - ~24.84%', filters['grades']['G'])

            # Verify one was chosen
            gradeChosen = False
            for grade in filters['grades']:
                if filters['grades'][grade] is True:
                    gradeChosen = True
            if not gradeChosen:
                print 'You have to AT LEAST choose one interest rate grade!'
            else:
                break

        self.investing['filters'] = filters

    def portfolio_picker(self, default_folio=False):
        """
        Load existing portfolios and let the user choose one or create a new one
        default_folio is the name of the default portfolio, or the one that was used last time.
        """

        if not self.investor:
            return False

        print '\nPortfolios...'
        try:
            folios = self.investor.lc.get_portfolio_list()

            # Convert object array into array of names
            for i, folio in enumerate(folios):
                folios[i] = folio['portfolioName']

            # Add default portfolio to the list
            if default_folio and default_folio not in folios:
                folios.append(default_folio)

            # Print out the portfolio list
            folios.sort()
            i = 1
            other_index = 0
            cancel_index = 0
            default_indicator = ''
            default_index = False
            for folio in folios:
                default_indicator = '  '
                if default_folio == folio:
                    default_indicator = '> '
                    default_index = str(i)

                print '{0}{1}: {2}'.format(default_indicator, i, folio)
                i += 1

            other_index = i
            print '  {0}: Other'.format(other_index)
            i += 1

            cancel_index = i
            print '  {0}: Cancel'.format(cancel_index)

            # Choose a portfolio
            while(True):
                choice = util.prompt('Choose one', default_index)

                # If no digit was chosen, ask again unless a default portfolio is present
                if not choice.isdigit():
                    if default_folio:
                        return default_folio
                    else:
                        continue
                choice = int(choice)

                # No zero
                if choice == 0:
                    continue

                # Existing portfolio chosen
                if choice <= len(folios):
                    break

                # Other
                elif choice == other_index:
                    while(True):
                        other = util.prompt('Enter the name for your new portfolio')

                        # Empty string entered, show list again
                        if other.strip() == '':
                            break

                        # Invalid character
                        elif re.search('[^a-zA-Z0-9 ,_\-#\.]', other):
                            print 'The portfolio name \'{0}\' is not valid! Only alphanumeric, spaces , _ - # and . are allowed.'.format(other)

                        # Return custom portfolio name
                        else:
                            return other

                # Cancel
                else:
                    return False

            # Existing portfolio
            if choice < other_index:
                return folios[choice - 1]

        except Exception as e:
            self.logger.error(e)
