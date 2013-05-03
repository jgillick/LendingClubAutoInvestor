#!/usr/bin/env python

import re
import os
import shutil
import yaml
import json
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
        'pass': False
    }

    # Defines the investment funding settings
    investing = {
        'minCash': 500,
        'minPercent': False,
        'maxPercent': False,
        'portfolio': False,
        'filters': False
    }

    # Default user settings
    user_settings = {
        'frequency': 60,
        'alert': False
    }

    def __init__(self, settings_dir=None, logger=False):
        """
        settings_dir is the directory that will be used to
        save the user and investment settings files
        """
        self.settings_dir = settings_dir

        # Create logger if none was passed in
        if not logger:
            self.logger = util.create_logger(False)
        else:
            self.logger = logger

        # Create the settings directory, if ti doesn't exist
        if self.settings_dir and not os.path.exists(self.settings_dir):
            os.mkdir(self.settings_dir)

        self.get_user_settings()
        self.load_investment_settings_file()

    def __getitem__(self, arg):
        """
        Attempts to get the setting or auth keys
        """
        if arg in self.investing:
            return self.investing[arg]
        if arg in self.auth:
            return self.auth[arg]
        return None

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

    def save(self):
        """
        Save the investment settings dict to a file
        """
        if not self.settings_dir:
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

    def load_investment_settings_file(self):
        """
        Returned the saved settings used last time this program was run
        """
        if not self.settings_dir:
            return

        investing_file = os.path.join(self.settings_dir, self.investing_file)
        if os.path.exists(investing_file):
            self.logger.debug('Loading saved investment settings file')
            try:
                # Read file
                f = open(investing_file, 'r')
                jsonStr = f.read()
                f.close()

                self.logger.debug('Saved investment settings: {0}'.format(jsonStr))

                # Convert JSON to dictionary
                saved_settings = json.loads(jsonStr)

                # Add values to dictionary
                for key, value in self.investing.iteritems():
                    if key in saved_settings:
                        self.investing[key] = saved_settings[key]

                # Add email to auth
                if 'email' in saved_settings:
                    self.auth['email'] = saved_settings['email']

                # Migrations
                if '36month' in self.investing['filters']:
                    self.investing['filters']['term36month'] = self.investing['filters']['36month']
                    del self.investing['filters']['36month']

                if '60month' in self.investing['filters']:
                    self.investing['filters']['term60month'] = self.investing['filters']['60month']
                    del self.investing['filters']['60month']

            except Exception as e:
                self.logger.debug('Could not read investment settings file: {0}'.format(str(e)))
        else:
            self.logger.debug('No saved investment settings file to load')

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
        print 'With at LEAST ${0} available to invest'.format(self.investing['minCash'])
        print 'Select a portfolio with an average interest rate between {0}% - {1}%'.format(self.investing['minPercent'], self.investing['maxPercent'])

        if self.investing['portfolio']:
            print 'Add investments to: "{0}"'.format(self.investing['portfolio'])

        # Filters
        if self.investing['filters'] is not False:
            print '\nAdvanced filters:'

            # Exclude existing
            if self.investing['filters']['exclude_existing']:
                print '  + Exclude loans already invested in'

            # Loan term
            terms = []
            if 'term36month' in self.investing['filters'] and self.investing['filters']['term36month']:
                terms.append('36')
            if 'term60month' in self.investing['filters'] and self.investing['filters']['term60month']:
                terms.append('60')
            print '  + Term: {0} months'.format(' & '.join(terms))

            # Interest rate grades
            if self.investing['filters']['grades']['All']:
                print '   + All interest rate grades'
            else:
                grades = []
                for grade in self.investing['filters']['grades']:
                    if grade != 'All' and self.investing['filters']['grades'][grade] is True:
                        grades.append(grade)
                print '  + Interest rates grades: {0}'.format(', '.join(sorted(grades)))

        print '=========={0}==========\n'.format(''.center(len(title), '='))

    def get_investment_settings(self):
        """
        Display a series of prompts to get how the user wants to invest their available cash.
        This fills out the investing dictionary.
        """

         # Minimum cash
        print '---------'
        print 'The auto investor will automatically try to invest ALL available cash into a diversified portfolio'
        while(True):
            self.investing['minCash'] = util.prompt_int('What\'s the MINIMUM amount of cash you want to invest each round?', self.investing['minCash'])
            if self.investing['minCash'] < 25:
                print '\nYou cannot invest less than $25. Please try again.'
            else:
                break

        # Min/max percent
        print '---------'
        while(True):
            print 'When auto investing, the LendingClub API will provide us a list of possible investment portfolios available at that moment.'
            print 'To pick the appropriate one for you, it needs to know what the minimum and maximum AVERAGE interest rate value you will accept.'
            print 'The investment option closest to the maximum value will be chosen and all your available cash will be invested in it.\n'

            self.investing['minPercent'] = util.prompt_float('What\'s MININUM average interest rate portfolio that you will accept?', self.investing['minPercent'])

            # Max percent should default to being larger than the min percent
            if self.investing['maxPercent'] is False or self.investing['maxPercent'] < self.investing['minPercent']:
                self.investing['maxPercent'] = self.investing['minPercent'] + 1
            self.investing['maxPercent'] = util.prompt_float('What\'s MAXIMUM average interest rate portfolio that you will accept?', self.investing['maxPercent'])

            # Validation
            if self.investing['maxPercent'] < self.investing['minPercent']:
                print 'The maximum value must be larger than, or equal to, the minimum value. Please try again.'
            elif self.investing['maxPercent'] == self.investing['minPercent']:
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

        # Advanced filter settings
        print '\n---------'
        if util.prompt_yn('Would you like to set advanced filter settings?', self.investing['filters'] is not False):
            self.get_filter_settings()

        # Review summary
        self.show_summary()
        if util.prompt_yn('Would you like to continue with these settings?', 'y'):
            self.save()
        else:
            self.get_investment_settings()

        return True

    def get_filter_settings(self):
        """
        Setup the advanced portfolio filters (terms, grades, existing notes, etc.)
        """
        filters = self.investing['filters']
        if not filters:
            filters = {
                'exclude_existing': True,
                'term36month': True,
                'term60month': True,
                'grades': {
                    'All': True,
                    'A': True,
                    'B': True,
                    'C': True,
                    'D': True,
                    'E': True,
                    'F': True,
                    'G': True
                }
            }

        print 'The following questions are from the filters section of the Invest page on LendingClub\n'

        filters['exclude_existing'] = util.prompt_yn('Exclude loans already invested in?', filters['exclude_existing'])

        print '---------'
        print 'Choose term (36 - 60 month)'

        while(True):
            filters['term36month'] = util.prompt_yn('Include 36 month term loans?', filters['term36month'])
            filters['term60month'] = util.prompt_yn('Include 60 month term loans?', filters['term60month'])

            # Validate 1 was chosen
            if not filters['term36month'] and not filters['term60month']:
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

    def portfolio_picker(self, previous_folio=False):
        """
        Load existing portfolios and let the user choose one or create a new one
        previous_folio is the name of the last portfolio selected
        """

        if not self.investor:
            return False

        print '\nPortfolios...'
        try:
            folios = self.investor.get_portfolio_list()

            # Print out the portfolio list
            i = 1
            other_index = 0
            cancel_index = 0
            previous_index = 0
            for folio in folios:
                print '{0}: {1}'.format(i, folio)

                if previous_folio == folio:
                    previous_folio = False

                i += 1

            if previous_folio is not False:
                previous_index = i
                print '{0}: {1}'.format(previous_index, previous_folio)
                i += 1

            other_index = i
            print '{0}: Other'.format(other_index)
            i += 1

            cancel_index = i
            print '{0}: Cancel'.format(cancel_index)

            # Choose a portfolio
            while(True):
                choice = util.prompt('Choose one')

                if not choice.isdigit():
                    continue
                choice = int(choice)

                # No zero
                if choice == 0:
                    continue

                # Existing portfolio chosen
                if choice <= len(folios):
                    break

                # Previous
                elif choice == previous_index:
                    return previous_folio

                # Other
                elif choice == other_index:
                    while(True):
                        other = util.prompt('Enter the name for your new portfolio')

                        # Empty string entered, show list again
                        if other.strip() == '':
                            break

                        # Invalid character
                        elif re.search('[^a-zA-Z0-9 ,_\-#\.]', other):
                            print 'The portfolio name is not valid, only alphanumeric space , _ - # and . are allowed.'

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

