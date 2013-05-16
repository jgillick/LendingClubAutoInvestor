#!/usr/bin/env python
#
# Does a real investment search on LendingClub with your credentials to test that
# the filters work. This will use your existing settings and will save any changes you make.
#

import sys
import os
import json

sys.path.insert(0, '.')
sys.path.insert(0, '../')
sys.path.insert(0, '../../')
import LendingClubInvestor

baseDir = os.path.dirname(os.path.realpath(__file__))

investor = LendingClubInvestor.AutoInvestor()
investor.settings_file = os.path.join(baseDir, '.browsetest')

investor.setup()
results = investor.browse_notes()
print '\nJSON RESULT'
print json.dumps(results)
