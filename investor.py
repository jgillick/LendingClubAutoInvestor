import sys, re, logging, getpass
import requests, json
from time import sleep
from bs4 import BeautifulSoup
import html5lib

baseUrl = 'https://www.lendingclub.com/'
authed = False
cookies = {}
verbose = False

requestHeaders = {
  'Referer': 'https://www.lendingclub.com/account/summary.action',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31'
}

# Defines the investment funding options
settings = {
  'email': False,
  'pass': False,
  'minCash': 500,
  'maxPercent': 0,
  'portfolio': False
}

# Set verbosity
verbose = (len(sys.argv) >= 2 and sys.argv[1] == '-v')

# Create logger
logger = logging.getLogger('funder')
if verbose:
  logger.setLevel(logging.DEBUG)
else:
  logger.setLevel(logging.ERROR)

logHandler = logging.StreamHandler()
if verbose:
  logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s #%(lineno)d - %(message)s', '%Y-%m-%d %H:%M'))
else:
  logHandler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s - %(message)s', '%Y-%m-%d %H:%M'))
logHandler.setLevel(logging.DEBUG)

logger.addHandler(logHandler)


def post_url(relUrl, params={}, data={}):
  """
  Sends POST request to the relative URL of www.lendingclub.com
  """
  global cookies, requestHeaders

  url = '{0}{1}'.format(baseUrl, relUrl)
  logger.debug('POSTING {0}'.format(url))
  return requests.post(url, params=params, data=data, cookies=cookies, headers=requestHeaders)

def get_url(relUrl, params={}):
  """
  Sends GET request to the relative URL of www.lendingclub.com
  """
  global cookies, requestHeaders

  url = '{0}{1}'.format(baseUrl, relUrl)
  logger.debug('GETTING {0}'.format(url))
  return requests.get(url, params=params, cookies=cookies, headers=requestHeaders) 

def isFloat(string):
  """
  Returns true if the string can be cast to a float
  """
  try:
    float(string)
    return True
  except ValueError:
    return False

def prompt(msg, prefill=False):
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

def prompt_float(msg, prefill=False):
  """ Prompts the user for an decimal response """
  while(True):
    response = prompt(msg, prefill)
    if type(response) == float:
      return response
    if not isFloat(response):
      print 'The value you entered must be a whole number, without symbols or decimal points'
    else:
      return float(response)

def prompt_int(msg, prefill=False):
  """ Prompts the user for an integer response """
  while(True):
    response = prompt(msg, prefill)
    if type(response) == int:
      return response
    if not response.isdigit():
      print 'The value you entered must be a whole number, without symbols or decimal points'
    else:
      return int(response)

def prompt_yn(msg, default=False):
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
    if response == '' and default != False:
      response = default

    # Return if valid
    if response in ['y', 'yes']:
      return True
    elif response in ['n', 'no']:
      return False

def getInvestmentOption(cash, maxPercent):
  """
  Returns the highest percent option to invest in for the cash, without crossing maxPercent
  """
  try:

    # Get all investment options
    payload = { 'amount': cash, 'max_per_note': 0, 'filter': 'default'}
    response = post_url('/portfolio/lendingMatchOptionsV2.action', data=payload)
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

        i += 1
        lastOption = option

      # If the perfect match wasn't found, return the last 
      # option that was under the maximum percent
      return lastOption
    else:
      return False

  except Exception as e:
    logger.error(str(e))

  return False


def sendInvestment(cash, investmentOption):
  """
  Submit an investment request with an option retrieved with getInvestmentOption
  """

  try:

    # Prepare the order
    payload = { 
      'order_amount': cash,
      'lending_match_point': investmentOption['optIndex'],
      'lending_match_version': 'v2'
    }
    get_url('/portfolio/recommendPortfolio.action', params=payload)

    # Get struts token
    response = get_url('/portfolio/placeOrder.action')
    soup = BeautifulSoup(response.text, "html5lib")
    strutToken = soup.find('input', {'name':'struts.token'})

    # Place order
    payload = {}
    if strutToken:
      payload['struts.token.name'] = 'struts.token'
      payload['struts.token'] = strutToken['value']
    response = post_url('/portfolio/orderConfirmed.action', data=payload)

  except Exception as e:
    logger.error('Could not complete your order (although, it might have gone through): {0}'.format(str(e)))

  try:

    # Get order number
    orderNum = 0
    loanNum = 0
    try:
      soup = BeautifulSoup(response.text)
      orderField = soup.find(id='order_id')
      if orderField:
        orderNum = int(orderField['value'])
      loanField = soup.find('td', {'class': 'loan_id'})
      if loanField:
        loanNum = int(loanField.text)
    except Exception as e:
      logger.error(str(e))

    # Print status message
    if orderNum == 0:
      logger.error('An investment order was submitted, but a confirmation could not be determined')
      return False
    else:
      logger.info('Order #{0} was successfully submitted for ${1} at {2}%'.format(orderNum, cash, investmentOption['percentage']))

    # Assign to portfolio
    try:
      if settings['portfolio'] and loanNum != 0 and orderNum != 0:
        postData = {
          'loan_id': str(loanNum),
          'record_id': str(loanNum),
          'order_id': str(orderNum)
        }
        paramData = {
          'method': 'addToLCPortfolio',
          'lcportfolio_name': settings['portfolio']
        }
        response = post_url('/data/portfolioManagement', params=paramData, data=postData)

        if response.status_code != 200 or response.json()['result'] != 'success':
          logger.error('Could not assign order #{0} to portfolio \'{1}: Server responded with {2}\''.format(str(orderNum), settings['portfolio'], response.text))
        else:
          logger.info('And added to portfolio: {0}'.format(settings['portfolio']))
          return True

      elif not settings['portfolio']:
        return True

    except Exception as e:
      logger.error('Could not assign order #{0} to portfolio \'{1}\': {2}'.format(orderNum, settings['portfolio']['portfolioName'], str(e)))

  except Exception as e:
    logger.error('Could not get your order number or move it to the specified portfolio: {0}'.format(str(e)))

  return False

def investmentLoop():
  """
  Invest cash every 30 minutes
  """
  try:

    # Get current cash balance
    response = get_url('/browse/cashBalanceAj.action')
    json = response.json()

    logger.debug(json);

    if json['result'] == 'success':
      cashMatch = re.search('^[^0-9]?([0-9\.]+)[^0-9]?', json['cashBalance'])
      if cashMatch:
        logger.debug('Cash available: {0}'.format(json['cashBalance']))
        cash = int(float(cashMatch.group(1)))

        # Find closest cash amount divisible by $25
        while cash % 25 != 0:
          cash -= 1        

        # Invest
        logger.debug('Cash to invest: {0}'.format(cash))
        if cash >= settings['minCash']:
          logger.info('Attempting to investing {0}'.format(cash))
          option = getInvestmentOption(cash, settings['maxPercent'])

          # Submit investment
          if option:
            logger.info('Auto investing your available cash ({0}) at {1}%...'.format(cash, option['percentage']))
            sleep(10) # last chance to cancel
            if sendInvestment(cash, option):
              logger.info('Done\n')
            else:
              logger.error('Errors occurred. Will try again in 30 minutes\n')

          else:
            logger.warn('No investment options are available at this time for {0}% - Trying again in 30 minutes'.format(settings['maxPercent']))

    else:
      logger.warn('Could not get cash balance: {0}'.format(response.text))

  except Exception as e:
    logger.error(str(e))

  # Sleep for 30 minutes and then do it again
  sleep(60 * 30)
  authenticate()
  investmentLoop()


def authenticate():
  """ 
  Attempt to authenticate the user with the email/pss in the settings dictionary. 
  Returns True/False
  """
  global cookies, authed

  
  payload = {
    'login_email': settings['email'],
    'login_password': settings['pass']
  }
  response = post_url('/account/login.action', data=payload)

  if (response.status_code == 200 or response.status_code == 302) and 'LC_FIRSTNAME' in response.cookies:
    authed = True
    cookies = response.cookies
    return True
  
  return False

def portfolioPicker():
  """
  Load existing portfolios and let the user choose one or create a new one
  """

  print '\nPortfolios...'

  try:

    # Get portfolio page HTML
    response = get_url('/data/portfolioManagement?method=getLCPortfolios')
    json = response.json()

    if json['result'] == 'success':

      # Print out the portfolio list
      i = 1
      otherIndex = 0
      cancelIndex = 0
      folios = json['results']
      for folio in folios:
        print '{0}: {1}'.format(i, folio['portfolioName'])
        i += 1

      otherIndex = i
      print '{0}: Other'.format(otherIndex)

      cancelIndex = otherIndex + 1
      print '{0}: Cancel'.format(cancelIndex)

      # Choose a portfolio
      while(True):
        choice = prompt_int('Choose one')
        if choice < otherIndex:
          break;

        # Other
        elif choice == otherIndex:
          other = prompt('Enter the name of your new portfolio')

          # Empty string entered, show list again
          if other.strip() != '':
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
    logger.error(e)


def getSettings():
  """
  Get the initial settings for the funder
  """

  # Authenticate
  print 'To start, we need to log you into Lending Club\n'
  while(True):
    settings['email'] = prompt('LendingClub email', 'j_gillick@yahoo.com')
    settings['pass'] = getpass.getpass()

    print '\nAuthenticating...'
    if authenticate():
      break
    else:
      print "\nCould not authenticate, please try again"

  print 'Success!\n'
  print 'Now that you\'re signed in, let\'s define what you want to do\n'

  # Minimum shares
  print 'The funder will only invest when there is money in your account. The more money,'
  print 'the more diversity in each investment. Now choose how much money you want in your'
  print 'account before this tool tries to invest it.'
  print '(at least 25)\n'
  while(True):
    settings['minCash'] = prompt_int('What\'s the minimum amount of cash you want available before reinvesting?', 500)
    if settings['minCash'] < 25:
      print '\nYou cannot invest less than $25. Please try again.'
    else:
      break

  # Max percent
  settings['maxPercent'] = prompt_float('What\'s the maximum average percent portfolio you want to invest in?')

  # Portfolio
  if prompt_yn('Do you want to put the investment into a specific portfolio?'):
    settings['portfolio'] = portfolioPicker()

  # Start watching
  print '\nThat\'s all we need. Now, as long as this is running, your account will be checked every 30 minutes and invested if enough funds are available.\n'

  investmentLoop()

print "\n///------------------------- $$$ -------------------------\\\\\\"
print '|   Welcome to the unofficial Lending Club investment tool   |'
print " ------------------------------------------------------------ \n"

if verbose:
  print 'VERBOSE OUTPUT IS ON\n'

getSettings();