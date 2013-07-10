#!/usr/bin/env python

import sys
import os
import unittest
import subprocess
import urllib
import traceback
import shutil
from time import sleep

sys.path.insert(0, '.')
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
from LendingClubInvestor import util
from LendingClubInvestor import AutoInvestor
from LendingClubInvestor.settings import Settings


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
        util.get_input = lambda msg: 'test'
        self.assertEqual(util.prompt('msg'), 'test')
        self.assertEqual(util.prompt('msg', 'not test'), 'test')

    def test_prompt_prefill(self):
        # User enters empty string, select prefill
        util.get_input = lambda msg: ''
        self.assertEqual(util.prompt('msg'), '')
        self.assertEqual(util.prompt('msg', 'not test'), 'not test')

    def test_prompt_yn(self):
        # Yes
        util.get_input = lambda msg: 'y'
        self.assertTrue(util.prompt_yn('msg'))
        util.get_input = lambda msg: 'Y'
        self.assertTrue(util.prompt_yn('msg'))
        util.get_input = lambda msg: 'Yes'
        self.assertTrue(util.prompt_yn('msg'))

        # No
        util.get_input = lambda msg: 'n'
        self.assertFalse(util.prompt_yn('msg'))
        util.get_input = lambda msg: 'N'
        self.assertFalse(util.prompt_yn('msg'))
        util.get_input = lambda msg: 'No'
        self.assertFalse(util.prompt_yn('msg'))

        # Invalid user input
        def get_input(msg):
            self.count += 1
            return 'Hi' if self.count == 1 else 'Y'
        util.get_input = get_input
        self.assertTrue(util.prompt_yn('msg'))
        self.assertEqual(self.count, 2)

    def test_prompt_yn_prefill(self):
        # User enters empty string, select prefill
        util.get_input = lambda msg: ''
        self.assertTrue(util.prompt_yn('msg', 'y'))
        self.assertFalse(util.prompt_yn('msg', 'n'))

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

        util.get_input = get_input
        self.assertEqual(util.prompt_float('msg'), 10.0)
        self.assertEqual(self.count, 3)

        # Values with commas
        util.get_input = lambda msg: '1,000.1'
        self.assertEqual(util.prompt_float('msg'), 1000.1)

    def test_prompt_float_prefill(self):
        # User enters empty string, select prefill
        util.get_input = lambda msg: ''
        self.assertEqual(util.prompt_float('msg', 10.1), 10.1)

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

        util.get_input = get_input
        self.assertEqual(util.prompt_float('msg'), 10)
        self.assertEqual(self.count, 3)

        # Values with commas
        util.get_input = lambda msg: '1,000.1'
        self.assertEqual(util.prompt_float('msg'), 1000.1)

    def test_prompt_int_prefill(self):
        # User enters empty string, select prefill
        util.get_input = lambda msg: ''
        self.assertEqual(util.prompt_int('msg', 15), 15)

    def test_is_float(self):
        self.assertTrue(util.isfloat('10'))
        self.assertTrue(util.isfloat('11.5'))
        self.assertTrue(util.isfloat('-13'))
        self.assertTrue(util.isfloat(14.5))

        self.assertFalse(util.isfloat('NotANumber'))
        self.assertFalse(util.isfloat('PartNumber123'))

    def test_currency_to_number(self):
        self.assertStrictEqual(util.currency_to_float('123.45'), 123.45)
        self.assertStrictEqual(util.currency_to_float('$123.45'), 123.45)
        self.assertStrictEqual(util.currency_to_float('123.45$'), 123.45)
        self.assertStrictEqual(util.currency_to_float('123.45$USD'), 123.45)
        self.assertStrictEqual(util.currency_to_float('1,230.45'), 1230.45)
        self.assertStrictEqual(util.currency_to_float('123'), 123.0)
        self.assertStrictEqual(util.currency_to_float('$123'), 123.0)


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
