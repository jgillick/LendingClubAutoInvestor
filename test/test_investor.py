#!/usr/bin/python

import unittest
import sys
import subprocess

sys.path.insert(0,'../')

from investor import *


class TestInvestorUtils(unittest.TestCase):
    """ Tests the utility functions, like prompt and isfloat """

    count = 0
    investor = False

    def setUp(self):
        self.count = 0
        self.investor = AutoInvestor()

    def assertStrictEqual(self, first, second, msg=None):
        isSame = first == second and type(first) == type(second)
        self.assertTrue(isSame, msg)

    def test_prompt(self):
        # User enters 'test'
        self.investor.get_input = lambda msg: 'test'
        self.assertEqual(self.investor.prompt('msg'), 'test')
        self.assertEqual(self.investor.prompt('msg', 'not test'), 'test')

    def test_prompt_prefill(self):
        # User enters empty string, select prefill
        self.investor.get_input = lambda msg: ''
        self.assertEqual(self.investor.prompt('msg'), '')
        self.assertEqual(self.investor.prompt('msg', 'not test'), 'not test')

    def test_prompt_yn(self):
        # Yes
        self.investor.get_input = lambda msg: 'y'
        self.assertTrue(self.investor.prompt_yn('msg'))
        self.investor.get_input = lambda msg: 'Y'
        self.assertTrue(self.investor.prompt_yn('msg'))
        self.investor.get_input = lambda msg: 'Yes'
        self.assertTrue(self.investor.prompt_yn('msg'))

        # No
        self.investor.get_input = lambda msg: 'n'
        self.assertFalse(self.investor.prompt_yn('msg'))
        self.investor.get_input = lambda msg: 'N'
        self.assertFalse(self.investor.prompt_yn('msg'))
        self.investor.get_input = lambda msg: 'No'
        self.assertFalse(self.investor.prompt_yn('msg'))

        # Invalid user input
        def get_input(msg):
            self.count += 1
            return 'Hi' if self.count == 1 else 'Y'
        self.investor.get_input = get_input
        self.assertTrue(self.investor.prompt_yn('msg'))
        self.assertEqual(self.count, 2)

    def test_prompt_yn_prefill(self):
        # User enters empty string, select prefill
        self.investor.get_input = lambda msg: ''
        self.assertTrue(self.investor.prompt_yn('msg', 'y'))
        self.assertFalse(self.investor.prompt_yn('msg', 'n'))

    def test_prompt_float(self):
        self.count = 0

        # Return empty string first, then string, finally a float value the last time asked
        def get_input(msg):
            self.count += 1
            if self.count == 1:
                return ''
            elif self.count == 2:
                return 'Hi'
            else:
                return '10.0'

        self.investor.get_input = get_input
        self.assertEqual(self.investor.prompt_float('msg'), 10.0)
        self.assertEqual(self.count, 3)

        # Values with commas
        self.investor.get_input = lambda msg: '1,000.1'
        self.assertEqual(self.investor.prompt_float('msg'), 1000.1)

    def test_prompt_float_prefill(self):
        # User enters empty string, select prefill
        self.investor.get_input = lambda msg: ''
        self.assertEqual(self.investor.prompt_float('msg', 10.1), 10.1)

    def test_prompt_int(self):

        # Return empty string first, then string, finally an int value the last time asked
        def get_input(msg):
            self.count += 1
            if self.count == 1:
                return ''
            elif self.count == 2:
                return 'Hi'
            else:
                return '10'

        self.investor.get_input = get_input
        self.assertEqual(self.investor.prompt_float('msg'), 10)
        self.assertEqual(self.count, 3)

        # Values with commas
        self.investor.get_input = lambda msg: '1,000.1'
        self.assertEqual(self.investor.prompt_float('msg'), 1000.1)

    def test_prompt_int_prefill(self):
        # User enters empty string, select prefill
        self.investor.get_input = lambda msg: ''
        self.assertEqual(self.investor.prompt_int('msg', 15), 15)

    def test_is_float(self):
        self.assertTrue(self.investor.isfloat('10'))
        self.assertTrue(self.investor.isfloat('11.5'))
        self.assertTrue(self.investor.isfloat('-13'))
        self.assertTrue(self.investor.isfloat(14.5))

        self.assertFalse(self.investor.isfloat('NotANumber'))
        self.assertFalse(self.investor.isfloat('PartNumber123'))

    def test_currency_to_number(self):
        self.assertStrictEqual(self.investor.currency_to_float('123.45'), 123.45)
        self.assertStrictEqual(self.investor.currency_to_float('$123.45'), 123.45)
        self.assertStrictEqual(self.investor.currency_to_float('123.45$'), 123.45)
        self.assertStrictEqual(self.investor.currency_to_float('123.45$USD'), 123.45)
        self.assertStrictEqual(self.investor.currency_to_float('1,230.45'), 1230.45)
        self.assertStrictEqual(self.investor.currency_to_float('123'), 123.0)
        self.assertStrictEqual(self.investor.currency_to_float('$123'), 123.0)


class TestInvestorFlow(unittest.TestCase):
    """ Tests the investor flow and communication with LendingClub """

    server = None
    investor = None

    def setUp(self):
        # Start dummy server
        self.server = subprocess.Popen('node ./node/server.js', shell=True, stdout=subprocess.PIPE)
        sleep(.2)  # startup time

        # Create investor object
        self.investor = AutoInvestor()
        self.investor.baseUrl = 'http://localhost:7357'
        self.investor.get_settings_filepath = lambda: os.path.join(os.path.dirname(os.path.realpath(__file__)), '.investortest')
        self.investor.settings = {
            'email': 'test@test.com',
            'pass': 'testpassword',
            'minCash': 100,
            'minPercent': 16.5,
            'maxPercent': 19.0,
            'portfolio': 'TestPortfolio',
            'filters': False
        }
        self.investor.logger = TestLogger()

    def tearDown(self):
        # Stop node
        if(self.server):
            self.server.kill()

        # Delete settings file
        settingsFile = self.investor.get_settings_filepath()
        if os.path.exists(settingsFile):
            os.remove(settingsFile)

    def test_login(self):
        self.assertTrue(self.investor.authenticate())

    def test_invalid_login(self):
        self.investor.settings['email'] = 'wrong@wrong.com'
        self.assertFalse(self.investor.authenticate())

    def test_get_cash_balance(self):
        self.assertEqual(self.investor.get_cash_balance(), 216.02)

    def test_portfolios(self):
        portfolios = self.investor.get_portfolio_list()
        self.assertNotEquals(len(portfolios), 0)

    def test_investment_option(self):
        """ Match settings to investment options -- closest match should be 18.66 """
        match = self.investor.get_investment_option(200)
        self.assertEqual(match['percentage'], 18.66)

    def test_investment_option_minimums(self):
        """ Test min percent: no investment options between 18.7 - 19.0 """
        self.investor.settings['minPercent'] = 18.7
        match = self.investor.get_investment_option(200)
        self.assertFalse(match)

    def test_investment_option_filters_below_percent(self):
        """ Investment Options within below percent settings.
        With filters set, the fixture data will return options below the min/max percent settings """

        self.investor.settings['filters'] = {
            'exclude_existing': True,
            '36month': False,
            '60month': True,
            'grades': {
                'All': False,
                'A': True,
                'B': True,
                'C': True,
                'D': False,
                'E': False,
                'F': False,
                'G': False
            }
        }
        match = self.investor.get_investment_option(200)
        self.assertFalse(match)

    def test_investment_option_filters_within_percent(self):
        """ Investment Options within percent settings.
        Set min/max settings to be within options returned with filters """

        self.investor.settings['filters'] = {
            'exclude_existing': True,
            '36month': False,
            '60month': True,
            'grades': {
                'All': False,
                'A': True,
                'B': True,
                'C': True,
                'D': False,
                'E': False,
                'F': False,
                'G': False
            }
        }

        # Default min/max are 16.5 - 19.0, filtered results fixture only goes up to 15.03
        self.investor.settings['minPercent'] = 13.0
        self.investor.settings['maxPercent'] = 14.5
        match = self.investor.get_investment_option(200)
        self.assertEqual(match['percentage'], 14.5)  # should be a perfect match


    def test_prepare_order(self):
        investmentOption = self.investor.get_investment_option(200)
        strutToken = self.investor.prepare_investment_order(200, investmentOption)
        self.assertEqual(strutToken, 'abc123')

    def test_place_order(self):
        investmentOption = self.investor.get_investment_option(200)
        (orderID, loanID) = self.investor.place_order('abc123', 200, investmentOption)
        self.assertEqual(orderID, 123)
        self.assertEqual(loanID, 345)

    def test_assign_to_porfolio(self):
        """ Standard assign to portfolio with order and loan IDs """
        ret = self.investor.assign_to_portfolio(123, 456)
        self.assertTrue(ret)

        # Should have info, no errors or warnings
        self.assertEqual(len(self.investor.logger.infos), 1)
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 0)

    def test_assign_to_porfolio_no_order(self):
        """ Assigning to portfolio without an order ID """
        ret = self.investor.assign_to_portfolio(0, 456)
        self.assertFalse(ret)

    def test_assign_to_porfolio_no_loan(self):
        """ Assigning to portfolio without a loan ID """
        ret = self.investor.assign_to_portfolio(123, 0)
        self.assertFalse(ret)

    def test_assign_to_porfolio_no_portfolio(self):
        """ If not assigning to portfolio, it should still return true """
        self.investor.settings['portfolio'] = False
        ret = self.investor.assign_to_portfolio(123, 456)
        self.assertTrue(ret)

        # Should be no errors or info
        self.assertEqual(len(self.investor.logger.infos), 0)
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 0)

    def test_attempt_to_invest(self):
        """ Test end-to-end investment """
        ret = self.investor.attempt_to_invest()
        self.assertTrue(ret)

        # Shouldn't be any errors or warnings
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 0)

    def test_attempt_to_invest_no_folio(self):
        """ Test end-to-end investment without portfolio """
        self.investor.settings['portfolio'] = False
        ret = self.investor.attempt_to_invest()
        self.assertTrue(ret)

        # Shouldn't be any errors or warnings
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 0)

    def test_attempt_to_invest_not_enough_cash(self):
        """ Test end-to-end investment without portfolio """
        self.investor.settings['minCash'] = 1000
        ret = self.investor.attempt_to_invest()
        self.assertFalse(ret)

        # Shouldn't be any errors or warnings
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 0)

    def test_attempt_to_invest_no_option_match(self):
        """ Test end-to-end investment without investment option match """
        # No options between 18.7 - 19.0
        self.investor.settings['minPercent'] = 18.7
        ret = self.investor.attempt_to_invest()
        self.assertFalse(ret)

        # Should be 0 errors and 1 warning
        self.assertEqual(len(self.investor.logger.errors), 0)
        self.assertEqual(len(self.investor.logger.warnings), 1)


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
        print '\nINVESTOR ERROR: {0}\n'.format(msg)
        self.errors.append(msg)

    def warning(self, msg):
        print '\nINVESTOR WARNING: {0}\n'.format(msg)
        self.warnings.append(msg)

    def debug(self, msg):
        #print 'INVESTOR DEBUG: {0}'.format(msg)
        self.debugs.append(msg)


if __name__ == '__main__':
    unittest.main()