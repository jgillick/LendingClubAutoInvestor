#!/usr/bin/env python
#
# Tests the portfolio picker
#

import sys
import os

sys.path.insert(0, '.')
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
import lcinvestor
from lcinvestor.settings import Settings
from lcinvestor import util


"""
Setup
"""
base_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.join(base_dir, '.folio_picker_test')

settings = Settings(settings_dir=app_dir)
investor = lcinvestor.AutoInvestor(settings=settings, verbose=True)
investor.lc.get_portfolio_list = lambda names_only: ['apple', 'bar', 'foo']

"""
With default option
"""
print '\nWith a default option'
while True:
    chosen = settings.portfolio_picker('The default')
    print 'You chose: {0}\n'.format(chosen)

    if not util.prompt_yn('Again?', 'n'):
        break

"""
No default option
"""
print '\nWithout a default option'
while True:
    chosen = settings.portfolio_picker()
    print 'You chose: {0}\n'.format(chosen)

    if not util.prompt_yn('Again?', 'n'):
        break

"""
No options
"""
print '\nWithout any options'
investor.lc.get_portfolio_list = lambda names_only: []
while True:
    chosen = settings.portfolio_picker()
    print 'You chose: {0}\n'.format(chosen)

    if not util.prompt_yn('Again?', 'n'):
        break


class TestLogger():
    """ A simple and incomplete replacement for logger for testing. All logs are added to arrays """

    infos = []
    errors = []
    warnings = []
    debugs = []

    def __init__(self):
        self.infos = []
        self.errors = []
        self.warnings = []
        self.debugs = []

    def info(self, msg):
        #print '\nINVESTOR INFO: {0}\n'.format(msg)
        self.infos.append(msg)

    def error(self, msg):
        self.errors.append(msg)
        print '\nINVESTOR ERROR: {0}'.format(msg)

        # Traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=2, file=sys.stdout)

    def warning(self, msg):
        print '\nINVESTOR WARNING: {0}\n'.format(msg)
        self.warnings.append(msg)

    def debug(self, msg):
        print 'INVESTOR DEBUG: {0}'.format(msg)
        self.debugs.append(msg)
