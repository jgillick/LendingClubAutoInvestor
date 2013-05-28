#!/usr/bin/env python
#
# Runs tests against the LendingClub.com using your username and password.
#

import sys
import os
import unittest

sys.path.insert(0, '.')
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
import LendingClubInvestor
from LendingClubInvestor.settings import Settings


class LiveTestAPIs(unittest.TestCase):
    """ Live test the APIs on lendingclub.com with your username and password """

    investor = None

    def setUp(self):
        logger = TestLogger()
        baseDir = os.path.dirname(os.path.realpath(__file__))

        settings = Settings(settings_dir=baseDir, logger=logger)
        self.investor = LendingClubInvestor.AutoInvestor(settings=settings, verbose=True)

        self.investor.settings.get_auth_settings()
        self.investor.authenticate()

        self.investor.logger = logger
        self.investor.settings.save()

    def test_portfolio_list(self):
        """ test_portfolio_list
        Get the portfolio list
        """
        folios = self.investor.get_portfolio_list()

        if len(folios) > 0:
            print folios
            self.assertEqual(type(folios[0]), unicode)

        # Should have no errors or warnings
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 0)


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


if __name__ == '__main__':
    unittest.main()