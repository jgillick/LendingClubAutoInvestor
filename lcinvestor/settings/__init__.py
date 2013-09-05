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
from lendingclub.filters import Filter, SavedFilter, SavedFilterError
from lcinvestor import util


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
        'max_per_note': 25,
        'portfolio': None,
        'filter_id': None,
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

    def __init__(self, investor, investing_file=None, settings_dir=None, logger=False, verbose=False):
        """
        file: A JSON file will the settings to use. Setting this parameter will prevent
              saving settings to the cache file.
        settings_dir: The directory that will be used to save the user and investment settings files
        """
        self.is_dirty = False
        self.investor = investor
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
        self.load_investment_settings_file(investing_file)

    def __getitem__(self, key):
        """
        Attempts to a value from one of the dictionaries
        """
        if key in self.investing:
            if key == 'filters' and self.investing['filter_id'] and type(self.investing['filters']) is not SavedFilter:
                try:
                    self.investing['filters'] = SavedFilter(self.investor.lc, self.investing['filter_id'])
                except Exception:
                    self.investing['filters'] = None

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

            # Prepare JSON
            to_save = self.investing.copy()
            to_save['email'] = self.auth['email']

            if type(to_save['filters']) is SavedFilter:
                to_save['filter_id'] = to_save['filters'].id
                to_save['filters'] = to_save['filters'].id
            else:
                to_save['filter_id'] = None

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

            if 'filter_id' not in settings:
                settings['filter_id'] = None

            if type(settings['filters']) is Filter:
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

        if 'max_per_note' not in settings:
            settings['max_per_note'] = 25

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

                # Load saved filter
                if saved_settings['filter_id']:
                    saved_settings['filter'] = False

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
                if self.investing['filters'] and type(self.investing['filters']) is dict and len(self.investing['filters']) > 0:
                    self.investing['filters'] = Filter(filters=self.investing['filters'])
                elif self.investing['filter_id']:
                    pass
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
        print 'Invest ALL available funds...\n'
        print 'With at LEAST ${0} available to invest'.format(self.investing['min_cash'])
        print 'Select a portfolio with an average interest rate between {0}% - {1}%'.format(self.investing['min_percent'], self.investing['max_percent'])
        print 'Invest as much as ${0} per loan note'.format(self.investing['max_per_note'])

        if self.investing['portfolio']:
            print 'Add investments to: "{0}"'.format(self.investing['portfolio'])

        # Filters
        if self.investing['filter_id'] and type(self['filters']) is not SavedFilter:
            print '\n!!! ERROR !!!'
            print 'Saved filter \'{0}\' could not be loaded from LendingClub. Check the ID and try again.\n'.format(self.investing['filter_id'])

        elif type(self['filters']) is SavedFilter:
            filters = self.investing['filters']
            print '\nUsing saved filter "{0}" (id:{1})'.format(filters.name, filters.id)

        elif self['filters'] is not False:
            print '\nAdvanced filters:'
            filters = self['filters']

            # Exclude existing
            if filters['exclude_existing']:
                print '  + Exclude loans already invested in'

            # Funding progress
            if filters['funding_progress'] > 0:
                print '  + Only loans which are at least {0}% funded'.format(filters['funding_progress'])

            # Loan term
            terms = []
            if filters['term']['Year3'] is True:
                terms.append('36')
            if filters['term']['Year5'] is True:
                terms.append('60')
            print '  + Term: {0} months'.format(' & '.join(terms))

            # Interest rate grades
            if filters['grades']['All']:
                print '  + All interest rate grades'
            else:
                grades = []
                for grade in filters['grades']:
                    if grade != 'All' and filters['grades'][grade] is True:
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

        # Max per note
        print '---------'
        while(True):
            self.investing['max_per_note'] = util.prompt_int('How much are you willing to invest per loan note (max per note)?', self.investing['max_per_note'])

            if self.investing['max_per_note'] < 25:
                print 'You have to invest AT LEAST $25 per note.'
                self.investing['max_per_note'] = 25
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

        # Advanced filter settings
        if util.prompt_yn('Would you like to set advanced filter settings?', self.investing['filters'] is not False):
            self.get_filter_settings()

        # Review summary
        self.confirm_settings()
        return True

    def get_filter_settings(self):
        """
        Setup the advanced portfolio filters (terms, grades, existing notes, etc.)
        """

        # Saved filter
        saved_filters = self.investor.lc.get_saved_filters()
        if len(saved_filters) > 0 and util.prompt_yn('Would you like to select one of your saved filters from LendingClub.com?', self.investing['filter_id'] is not None):

            # Get the selected one from list (has to be same-same object)
            selected = None
            if self.investing['filter_id']:
                selected = self.investing['filter_id']

            print '\nSelect a saved filter from the list below:'
            saved = self.list_picker(
                items=saved_filters,
                default=selected,
                label_key='name',
                id_key='id')

            if saved is False:
                print '\nDefine all your filters manually...'
            else:
                print 'Using {0}'.format(saved)
                self.investing['filters'] = saved
                self.investing['filter_id'] = saved.id
                return

        filters = Filter()

        # Manual entry
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

    def portfolio_picker(self, default=None):
        """
        Shows a list picker of porfolios

        Parameters:
            default -- The portfolio name to have selected by default
        """

        folios = self.investor.lc.get_portfolio_list(names_only=True)

        print '\nPortfolios...'
        folios.sort()
        while True:
            if len(folios) == 0:
                picked = util.prompt('Enter the name for your new portfolio')
            else:
                picked = self.list_picker(
                    items=folios,
                    default=default,
                    allow_other=True,
                    other_prompt='Enter the name for your new portfolio')

            # Validate custom value
            if picked and picked not in folios and re.search('[^a-zA-Z0-9 ,_\-#\.]', picked):
                print 'The portfolio name \'{0}\' is not valid! Only alphanumeric, spaces , _ - # and . are allowed.'.format(picked)
            else:
                break

        return picked

    def list_picker(self, items, default=None, label_key=None, id_key=None, allow_other=None, other_prompt='Enter a value'):
        """
        Shows a list of items the user can pick from.

        Parameters
            items -- The list of items to display. This is either a list of strings or
                objects. If objects, the label_key must be set
            default -- The item or ID that should be selected by default.
            label_key -- If items is a list of objects, this is the key or attribute of the object with the
                label to show for each item.
            id_key -- If items is a list of objects, this defined what the ID key/attribute is on each object.
            allow_other -- If an 'Other' option should be allowed. If selected the user will be able to type
                their own item, which will be returned.
            other_prompt -- The prompt to show when the user selects 'Other'

        Returns The item chosen from the list, a string if the user choose 'Other' or False if
        the user cancels the selection
        """
        assert len(items) > 0 or default is not False, 'You cannot select from a list without any items'

        try:
            string_list = False
            if (len(items) > 0 and type(items[0]) in [str, unicode]) or (len(items) == 0 and type(default) is str):
                string_list = True

            # If the default item isn't in the list of strings, add it
            if default and default not in items and string_list:
                items.append(default)

            # Print out the list
            i = 1
            other_index = -1
            cancel_index = 0
            default_index = False
            for item in items:
                gutter = '  '
                is_default = False

                # Get item label
                if string_list:
                    label = item
                else:
                    label = str(item)
                    if label_key:
                        if type(item) is dict and label_key in item:
                            label = item[label_key]
                        elif hasattr(item, label_key):
                            label = getattr(item, label_key)

                # Selected indicator
                if default is not None:

                    if string_list and default == item:
                        is_default = True

                    elif id_key is not None:
                        if type(item) is dict and id_key in item and item[id_key] == default:
                            is_default = True
                        elif hasattr(item, label_key) and getattr(item, id_key) == default:
                            is_default = True

                    if is_default:
                        gutter = '> '
                        default_index = str(i)

                print '{0}{1}: {2}'.format(gutter, i, label)
                i += 1

            if allow_other:
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
                    if not default_index:
                        continue
                    else:
                        return default

                choice = int(choice)

                # Out of range
                if choice == 0 or choice > cancel_index:
                    continue

                # List item chosen
                if choice <= len(items):
                    return items[choice - 1]

                # Other
                elif choice == other_index:
                    while(True):
                        other = util.prompt(other_prompt)

                        # Empty string entered, show list again
                        if other.strip() == '':
                            break

                        # Return custom portfolio name
                        else:
                            return other

                # Cancel
                else:
                    return False

        except Exception as e:
            self.logger.error(e)
