#!/usr/bin/python

import signal, sys, os
import re
import logging
import getpass
import requests
import json
from daemon import runner
from time import sleep
from bs4 import BeautifulSoup
import html5lib

class AutoInvestor:
  
  baseUrl = 'https://www.lendingclub.com/'
  baseDir = os.path.dirname(os.path.realpath(__file__))
  authed = False
  cookies = {}
  verbose = False
  logFile = os.path.join(baseDir, 'daemon.log')

  requestHeaders = {
    'Referer': 'https://www.lendingclub.com/account/summary.action',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31'
  }

  # Defines the investment funding options
  settings = {
    'email': False,
    'pass': False,
    'minCash': 500,
    'minPercent': False,
    'maxPercent': False,
    'portfolio': False
  }

  def __init__(self, verbose=False, daemon=False, stopping=False):
    self.verbose = verbose
    self.createLogger()

    if not stopping:
      print "\n///------------------------- $$$ -------------------------\\\\\\"
      print '|   Welcome to the unofficial Lending Club investment tool   |'
      print " ------------------------------------------------------------ \n"

      if self.verbose:
        print 'VERBOSE OUTPUT IS ON\n'

      # Load saved settings
      self.loadSavedSettings()

      # Auth settings
      self.getAuthSettings()

      if self.authed:

        # Investment settings
        print 'Now that you\'re signed in, let\'s define what you want to do\n'
        self.getInvestmentSettings()

        # All ready to start running
        print '\nThat\'s all we need. Now, as long as this is running, your account will be checked every 30 minutes and invested if enough funds are available.\n'

    # Daemon settings
    if daemon:
      self.stdin_path = '/dev/null'
      self.stdout_path = self.logFile
      self.stderr_path = self.logFile
      self.pidfile_path =  '/tmp/investor.pid'
      self.pidfile_timeout = 5

      if not stopping:
        print 'Starting auto investor daemon...'
        print 'pid at {0}'.format(self.pidfile_path)
        print 'Logging output to {0}'.format(self.logFile)
      else:
        print 'Stoping auto investor daemon...'

  def run(self):
    """
    Start the investment loop
    """
    self.investmentLoop()


  def createLogger(self):
    """
    Initialize the logger
    """

    self.logger = logging.getLogger('investor')
    if self.verbose:
      self.logger.setLevel(logging.DEBUG)
    else:
      self.logger.setLevel(logging.INFO)

    logHandler = logging.StreamHandler()
    if self.verbose:
      logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s #%(lineno)d - %(message)s', '%Y-%m-%d %H:%M'))
    else:
      logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s - %(message)s', '%Y-%m-%d %H:%M'))

    self.logger.addHandler(logHandler)

  def currencyToNumber(self, cashValue):
    """
    Converts a currency value, with or without symbols, to a floating point number,
    Returns -1.0, if the string is not a number or currency value
    """
    cash = -1.0
    cashMatch = re.search('^[^0-9]?([0-9\.,]+)[^0-9]?', cashValue)
    if cashMatch:
      cash = float(cashMatch.group(1))
    return cash

  def getSettingsFilePath(self):
    """
    Return the file path to the settings file
    """
    return os.path.join(self.baseDir, '.investor')

  def saveSettings(self):
    """
    Save the settings dict to a file
    """
    try:
      # Remove password
      settingsCopy = self.settings.copy()
      if 'pass' in settingsCopy:
        del(settingsCopy['pass'])

      # Convert to JSON
      jsonOut = json.dumps(settingsCopy)

      # Save
      self.logger.debug('Saving settings: {0}'.format(jsonOut))
      settingsFile = self.getSettingsFilePath()

      f = open(settingsFile, 'w')
      f.write(jsonOut)
      f.close()

      self.logger.debug('Saved')

    except Exception as e:
      self.logger.warn('Could not save the settings to file: {0}'.format(str(e)))

  def loadSavedSettings(self):
    """
    Returned the saved settings used last time this program was run
    """
    settingsFile = self.getSettingsFilePath()
    if os.path.exists(settingsFile):
      self.logger.debug('Loading saved settings file')
      try:
        # Read file
        f = open(settingsFile, 'r')
        jsonStr = f.read()
        f.close()

        self.logger.debug('Saved settings: {0}'.format(jsonStr))

        # Convert JSON to dictionary
        savedSettings = json.loads(jsonStr)

        # Add values to dictionary
        for key, value in self.settings.iteritems():
          if key in savedSettings:
            self.settings[key] = savedSettings[key]

      except Exception as e:
        self.logger.debug('Could not read settings file: {0}'.format(str(e)))
    else:
      self.logger.debug('No saved settings file to load')

  def post_url(self, relUrl, params={}, data={}, useCookies=True):
    """
    Sends POST request to the relative URL of www.lendingclub.com
    """
    url = '{0}{1}'.format(self.baseUrl, relUrl)
    self.logger.debug('POSTING {0}'.format(url))
    cookies = self.cookies if useCookies else {}
    return requests.post(url, params=params, data=data, cookies=cookies, headers=self.requestHeaders)

  def get_url(self, relUrl, params={}, useCookies=True):
    """
    Sends GET request to the relative URL of www.lendingclub.com
    """
    url = '{0}{1}'.format(self.baseUrl, relUrl)
    self.logger.debug('GETTING {0}'.format(url))
    cookies = self.cookies if useCookies else {}
    return requests.get(url, params=params, cookies=self.cookies, headers=self.requestHeaders) 

  def isFloat(self, string):
    """
    Returns true if the string can be cast to a float
    """
    try:
      float(string)
      return True
    except ValueError:
      return False

  def prompt(self, msg, prefill=False):
    """ Prompt the user for input and return the prefill value if the user did not enter anything """
    if prefill != False:
      msg = "{0} [{1}]: ".format(msg, str(prefill))
    else:
      msg = "{0}: ".format(msg)

    response = raw_input(msg)
    if response.strip() == '' and prefill != False: 
      return prefill
    else:
      return response

  def prompt_float(self, msg, prefill=False):
    """ Prompts the user for an decimal response """
    while(True):
      response = self.prompt(msg, prefill)
      if type(response) == float:
        return response
      if not self.isFloat(response):
        print 'The value you entered must be a whole number, without symbols or decimal points'
      else:
        return float(response)

  def prompt_int(self, msg, prefill=False):
    """ Prompts the user for an integer response """
    while(True):
      response = self.prompt(msg, prefill)

      # Remove commas
      if type(response) == str:
        response = response.replace(',', '')

      # Validate response
      if type(response) == int:
        return response
      if not response.isdigit():
        print 'The value you entered must be a whole number, without symbols or decimal points'
      else:
        return int(response)

  def prompt_yn(self, msg, default=False):
    """ 
    Prompts the user for a y/n response.
    default param should be either 'y' or 'n'
    Returns True if 'Y' and False if 'N'
    """
    if default == 'y':
      msg = "{0} [Y/n]: ".format(msg)
    elif default == 'n':
      msg = "{0} [y/N]: ".format(msg)
    else:
      msg = "{0} [y/n]: ".format(msg)

    while(True):
      response = raw_input(msg)

      # Normalize response
      response = response.lower().strip()
      if response == '' and default is not False:
        response = default

      # Return if valid
      if response in ['y', 'yes']:
        return True
      elif response in ['n', 'no']:
        return False

  def getInvestmentOption(self, cash):
    """
    When investing, lending club provides a list of investment portfolio options, all with different
    diversification of loan classes which come out to an average percent return.

    This method returns an investment option that best matches your available cash and min/max 
    percentage (defined in settings) desired. If there are multiple options between min & max, 
    the one closest to max will be chosen.
    """
    try:

      maxPercent = self.settings['maxPercent']
      minPercent = self.settings['minPercent']

      # Get all investment options
      payload = { 
        'amount': cash, 
        'max_per_note': 0, 
        'filter': 'default'
      }
      response = self.post_url('/portfolio/lendingMatchOptionsV2.action', data=payload)
      json = response.json()

      if json['result'] == 'success' and 'lmOptions' in json:
        options = json['lmOptions']
        lastOption = False

        # Loop through all the investment options
        i = 0
        for option in options:
          option['optIndex'] = i

          # A perfect match
          if option['percentage'] == maxPercent:
            return option

          # Over the max
          elif option['percentage'] > maxPercent:
            break;

          # Over the minimum
          elif option['percentage'] >= minPercent:
            lastOption = option

          i += 1

        # If the perfect match wasn't found, return the last 
        # option that was under the maximum percent
        return lastOption
      else:
        return False

    except Exception as e:
      self.logger.error(str(e))

    return False


  def sendInvestment(self, cash, investmentOption):
    """
    Submit an investment request for with an investment portfolio option selected from getInvestmentOption()
    """

    # Place the order
    try:
      if 'optIndex' not in investmentOption:
        self.logger.error('The \'optIndex\' key is not present in investmentOption passed to sendInvestment()! This value is set when selecting the option from getInvestmentOption()')
        return False

      # Prepare the order (don't process response)
      payload = { 
        'order_amount': cash,
        'lending_match_point': investmentOption['optIndex'],
        'lending_match_version': 'v2'
      }
      self.get_url('/portfolio/recommendPortfolio.action', params=payload)

      # Get struts token
      response = self.get_url('/portfolio/placeOrder.action')
      soup = BeautifulSoup(response.text, "html5lib")
      strutToken = soup.find('input', {'name':'struts.token'})

      # Place order
      payload = {}
      if strutToken:
        payload['struts.token.name'] = 'struts.token'
        payload['struts.token'] = strutToken['value']
      response = self.post_url('/portfolio/orderConfirmed.action', data=payload)

      self.processConfirmation(response.text)

    except Exception as e:
      self.logger.error('Could not complete your order (although, it might have gone through): {0}'.format(str(e)))
      return False

    return True

  def processConfirmation(self, html):
    """
    Given the confirmation page HTML, process the order number, loan ID and assign to portfolio
    """

    orderNum = 0
    loanID = 0

    # Process order confirmation page
    try:
      soup = BeautifulSoup(html)

      # Order num
      orderField = soup.find(id='order_id')
      if orderField:
        orderNum = int(orderField['value'])

      # Load ID
      loanField = soup.find('td', {'class': 'loan_id'})
      if loanField:
        loanID = int(loanField.text)

      # Print status message
      if orderNum == 0:
        self.logger.error('An investment order was submitted, but a confirmation could not be determined')
        return False
      else:
        self.logger.info('Order #{0} was successfully submitted for ${1} at {2}%'.format(orderNum, cash, investmentOption['percentage']))

      return self.assignToPortfolio(orderNum, loadID)

    except Exception as e:
      self.logger.error('Could not get your order number or loan ID from the order confirmation. {0}'.format(str(e)))
      return False

  def assignToPortfolio(self, orderNum=0, loanID=0):
    """
    Assign an order to a the portfolio named in the settings dictionary.
    """

    # Assign to portfolio
    try:
      if not self.settings['portfolio']:
        return True

      if loanID != 0 and orderNum != 0:
        postData = {
          'loan_id': str(loanID),
          'record_id': str(loanID),
          'order_id': str(orderNum)
        }
        paramData = {
          'method': 'addToLCPortfolio',
          'lcportfolio_name': self.settings['portfolio']
        }
        response = self.post_url('/data/portfolioManagement', params=paramData, data=postData)

        if response.status_code != 200 or response.json()['result'] != 'success':
          self.logger.error('Could not assign order #{0} to portfolio \'{1}: Server responded with {2}\''.format(str(orderNum), self.settings['portfolio'], response.text))
        else:
          self.logger.info('Added order #{0} to portfolio "{1}"'.format(str(orderNum), self.settings['portfolio']))
          return True

    except Exception as e:
      self.logger.error('Could not assign order #{0} to portfolio \'{1}\': {2}'.format(orderNum, setttings.settings['portfolio'], str(e)))

  def getCashBalance(self):
    """
    Returns the cash balance available to invest
    """
    cash = -1
    try:
      response = self.get_url('/browse/cashBalanceAj.action')
      json = response.json()

      if json['result'] == 'success':
        self.logger.debug('Cash available: {0}'.format(json['cashBalance']))
        cash = self.currencyToNumber(json['cashBalance'])
      else:
        self.logger.warn('Could not get cash balance: {0}'.format(response.text))

    except Exception as e:
      self.logger.error('Could not get the cash balance on the account: {0}\nJSON: {1}'.format(str(e), response.text))

    return cash

  def investmentLoop(self):
    """
    Invest cash every 30 minutes
    """
    while(True):
      self.logger.info('Checking for funds to invest...')
      try:

        # Get current cash balance
        allCash = self.getCashBalance()

        if allCash > 0:

          # Find closest cash amount divisible by $25
          cash = int(allCash)
          while cash % 25 != 0:
            cash -= 1        

          # Invest
          self.logger.debug('Cash to invest: ${0} (of ${1} total)'.format(cash, allCash))
          if cash >= self.settings['minCash']:
            self.logger.info('Attempting to investing ${0}'.format(cash))
            option = self.getInvestmentOption(cash)

            # Submit investment
            if option:
              self.logger.info('Auto investing your available cash (${0}) at {1}%...'.format(cash, option['percentage']))
              sleep(10) # last chance to cancel

              if self.sendInvestment(cash, option):
                self.logger.info('Done\n')
              else:
                self.logger.error('Errors occurred. Will try again in 30 minutes\n')

            else:
              self.logger.warn('No investment options are available at this time for portfolios between {0}% - {1}% -- Trying again in 30 minutes'.format(self.settings['minPercent'], self.settings['maxPercent']))
          else:
            self.logger.info('Only ${0} available'.format(allCash))

      except Exception as e:
        self.logger.error(str(e))

      # Reauthentication loop
      while(True):

        # Sleep for 30 minutes and then authenticate and move to the main loop
        sleep(60 * 30)

        # Authenticated, continue in the main loop
        if self.authenticate():
          self.logger.info('Authenticated')
          break

        # Try again in another 30 minutes
        else:
          self.logger.error('Could not authenticate')


  def authenticate(self):
    """ 
    Attempt to authenticate the user with the email/pass in the settings dictionary. 
    Returns True/False
    """

    payload = {
      'login_email': self.settings['email'],
      'login_password': self.settings['pass']
    }
    response = self.post_url('/account/login.action', data=payload, useCookies=False)

    if (response.status_code == 200 or response.status_code == 302) and 'LC_FIRSTNAME' in response.cookies:
      self.authed = True
      self.cookies = response.cookies
      return True
    return False

  def portfolioPicker(self, previousFolio=False):
    """
    Load existing portfolios and let the user choose one or create a new one
    """

    print '\nPortfolios...'

    try:
      # Get portfolio page HTML
      response = self.get_url('/data/portfolioManagement?method=getLCPortfolios')
      json = response.json()

      if json['result'] == 'success':

        # Print out the portfolio list
        folios = json['results']
        i = 1
        otherIndex = 0
        cancelIndex = 0
        previousIndex = 0
        for folio in folios:
          print '{0}: {1}'.format(i, folio['portfolioName'])

          if previousFolio == folio['portfolioName']:
            previousFolio = False

          i += 1

        if previousFolio is not False: 
          previousIndex = i
          print '{0}: {1}'.format(previousIndex, previousFolio)
          i += 1

        otherIndex = i
        print '{0}: Other'.format(otherIndex)
        i += 1

        cancelIndex = i
        print '{0}: Cancel'.format(cancelIndex)

        # Choose a portfolio
        while(True):
          choice = self.prompt('Choose one')

          if not choice.isdigit():
            continue
          choice = int(choice)

          # No zero
          if choice == 0:
            continue

          # Existing portfolio chosen
          if choice <= len(folios):
            break;

          # Previous
          elif choice == previousIndex:
            return previousFolio

          # Other
          elif choice == otherIndex:
            while(True):
              other = self.prompt('Enter the name for your new portfolio')

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
            return False;

        # Existing portfolio
        if choice < otherIndex:
          return folios[choice - 1]['portfolioName']


      else:
        print 'Could not retrieve portfolio list'
        return False;

    except Exception as e:
      self.logger.error(e)

  def showSummary(self, title='Summary'):
    """
    Show a summary of the settings that will be used for auto investing
    """

    print '\n========= {0} ========='.format(title)
    print 'Invest ALL available funds with the following criteria\n'
    print 'With at LEAST ${0} available to invest'.format(self.settings['minCash'])
    print 'Select a portfolio with an average interest rate between {0}% - {1}%'.format(self.settings['minPercent'], self.settings['maxPercent'])

    if self.settings['portfolio']:
      print 'Add investments to: "{0}"'.format(self.settings['portfolio'])

    print '=========={0}==========\n'.format(''.center(len(title), '='))


  def getInvestmentSettings(self):
    """
    Show the user a series of prompts to determine how they want the tool to automatically invest.
    This fills out the settings dictionary.
    """

    # Use the settings from last time
    if self.settings['minPercent'] is not False and self.settings['maxPercent'] is not False:
      self.showSummary('Prior Settings')
      if self.prompt_yn('Would you like to use these settings from last time?', 'y'):
        return True


     # Minimum cash
    print '---------'
    print 'The auto investor will automatically try to invest ALL available cash into a diversified portfolio'
    while(True):
      self.settings['minCash'] = self.prompt_int('What\'s the MINIMUM amount of cash you want to invest each round?', self.settings['minCash'])
      if self.settings['minCash'] < 25:
        print '\nYou cannot invest less than $25. Please try again.'
      else:
        break

    # Min/max percent
    print '---------'
    while(True):
      print 'When auto investing, the LendingClub API will provide us a list of possible investment portfolios available at that moment.'
      print 'To pick the appropriate one for you, it needs to know what the minimum and maximum AVERAGE interest rate value you will accept.'
      print 'The investment option closest to the maximum value will be chosen and all your available cash will be invested in it.\n'

      self.settings['minPercent'] = self.prompt_float('What\'s MININUM average interest rate portfolio that you will accept?', self.settings['minPercent'])

      # Max percent should default to being larger than the min percent
      if self.settings['maxPercent'] is False or self.settings['maxPercent'] < self.settings['minPercent']:
        self.settings['maxPercent'] = self.settings['minPercent'] + 1
      self.settings['maxPercent'] = self.prompt_float('What\'s MAXIMUM average interest rate portfolio that you will accept?', self.settings['maxPercent'])

      # Validation
      if self.settings['maxPercent'] < self.settings['minPercent']:
        print 'The maximum value must be larger than, or equal to, the minimum value. Please try again.'
      elif self.settings['maxPercent'] == self.settings['minPercent']:
        print 'It\'s very uncommon to find an available portfolio that will match an exact percent.'
        if not self.prompt_yn('Would you like to specify a broader range?'):
          break
      else:
        break

    # Portfolio
    print '---------'
    folioOption = False 
    if self.settings['portfolio']: # if saved settings has a portfolio set, default the prompt to 'Y' to choose
      folioOption = 'y'

    if self.prompt_yn('Do you want to put your new investments into a named portfolio?', folioOption):
      self.settings['portfolio'] = self.portfolioPicker(self.settings['portfolio'])
    else:
      self.settings['portfolio'] = False

    # Review summary
    self.showSummary()
    if self.prompt_yn('Would you like to continue with these settings?', 'y'):
      self.saveSettings()
    else:
      self.getInvestmentSettings()

    return True;


  def getAuthSettings(self):
    """
    Get the initial settings for the funder
    """

    # Authenticate
    print 'To start, we need to log you into Lending Club (your password will never be saved)\n'
    while(True):
      self.settings['email'] = self.prompt('LendingClub email', self.settings['email'])
      self.settings['pass'] = getpass.getpass()

      print '\nAuthenticating...'
      if self.authenticate():
        break
      else:
        print "\nCould not authenticate, please try again"

    print 'Success!\n'
    print 'You have ${0} in your account, free to invest\n'.format(self.getCashBalance())
    return True


def interuptHandler(signum, frame):
  """
  Exit gracefully
  """
  print '\n\nStopping program...\n'
  exit()
signal.signal(signal.SIGINT, interuptHandler)


    

# Process command flags
isVerbose = ('-v' in sys.argv)
isDaemon = ('start' in sys.argv or 'stop' in sys.argv)
isStopping = ('stop' in sys.argv)
if '-h' in sys.argv:
  print 'Usage: {0} [flags]\n'.format(sys.argv[0])
  print '   -h  Show this message'
  print '   -v  Verbose output\n'
  print '   start  Start this as a daemon process'
  print '   stop   Stop the running daemon process'
  exit();

# Start program
investor = AutoInvestor(verbose=isVerbose, daemon=isDaemon, stopping=isStopping)
if isDaemon:
  daemon_runner = runner.DaemonRunner(investor)
  daemon_runner.do_action()
else:
  investor.run()