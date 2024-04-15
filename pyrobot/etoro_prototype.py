import os
import ast
import time
import json
import pprint
import requests
import pandas as pd

from datetime import datetime
from typing import List
from typing import Dict

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class EtoroPrototype():

  def __init__(self, email: str, password: str, mode: str = 'real', multiple_trade: bool = True, allocate_amount: float = 0, trading_size: int = 1):

    self._system_start_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    self.email = email
    self.password = password
    self.mode = mode.lower() # real / virtual

    self.avaliable_equity = {}
    self.spreads_fees = {}
    
    self._multiple_trade = multiple_trade
    self._allocate_amount = allocate_amount
    self._trade_amount = allocate_amount
    self._trading_size = trading_size

    self.portfolio_records = []

    self._statistics = {}
    self._statistics['open'] = 0
    self._statistics['limit'] = 0
    self._statistics['repeat'] = 0
    self._statistics['error'] = 0

    self._statistics['profit_count'] = 0
    self._statistics['loss_count']   = 0
    self._statistics['total_profit'] = 0.0
    self._statistics['total_loss']   = 0.0

    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-erros")
    # options.add_argument('headless') # without showing the chrome
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # remove usb errors
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    self.options = options

    # Get the folder path
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Get the chromedriver.exe path
    chromedriver = dir_path + "/chromedriver"
    # Let the os execute the chromedriver
    os.environ["webdriver.chrome.driver"] = chromedriver

    self.driver = webdriver.Chrome(options=options, executable_path=chromedriver)
    self.driver.implicitly_wait(10) # wait for 10 seconds if cannot find the DOM element
    self.wait = WebDriverWait(self.driver, 10) # wait for 10 seconds

    # Execute initial functions
    # print('Getting spread fees ...')
    # self._get_spreads_fees()
    print('Logging ...')
    self.login()
    print('Switching to {} portfolio ...'.format(self.mode.capitalize()))
    self.switch_to_x_portfolio(mode=self.mode)
    print('Getting traded amount ...')
    self._traded_amount = self.get_total_allocated_amount()
  
  def go_to(self, url: str):
    driver = self.driver

    current_url = driver.current_url
    if url == current_url:
      return

    driver.get(url)
    self.wait_page_loaded()
  
  def wait_page_loaded(self):

    while True:
      time.sleep(3)
      page_state = self.driver.execute_script('return document.readyState;')

      if page_state == 'complete':
        break

  def login(self):
    driver = self.driver

    driver.get("https://www.etoro.com/login")

    # fill in data and click login button
    driver.find_element_by_id("username").send_keys(self.email)
    driver.find_element_by_id("password").send_keys(self.password)
    driver.find_element_by_id("CB").click()
    driver.find_element_by_class_name("blue-btn").click()

    self.wait_page_loaded()

  def close_browser(self):
    driver = self.driver
    driver.quit()

  def is_logged(self):
    driver = self.driver

    login_data = driver.execute_script("return window.atob(window.localStorage.loginData);")

    if login_data is not None:
      return True
    else:
      return False
  
  def get_total_allocated_amount(self) -> float:

    mode = self.mode
    driver = self.driver

    self.go_to("https://www.etoro.com/portfolio")

    # Check portfolio mode
    if mode != self.is_x_portfolio_mode(mode=mode):
      self.switch_to_x_portfolio(mode=mode)

    # Get total allocated amount
    total_allocated_amount = driver.find_elements_by_class_name("footer-unit-value")[1].text
    total_allocated_amount = float(total_allocated_amount.replace("$",",").replace(",",""))
   
    return total_allocated_amount
  
  def get_portfolio_mode(self) -> str:
    driver = self.driver

    try:
      driver.find_elements_by_class_name("header-text")[0]
    except NoSuchElementException:
      self.go_to("https://www.etoro.com/watchlists")

    mode = driver.find_elements_by_class_name("header-text")[0].text.lower()

    return mode

  def is_x_portfolio_mode(self, mode: str) -> bool:

    mode = mode.lower()
    current_mode = self.get_portfolio_mode()

    return mode == current_mode

  def switch_to_x_portfolio(self, mode: str):

    mode = mode.lower()
    if self.is_x_portfolio_mode(mode=mode):
      return

    mode_type = ["real", "virtual"]
    index = mode_type.index(mode)
    
    driver = self.driver
    driver.find_element_by_class_name("i-menu-link-mode-demo").click() 
    driver.find_elements_by_class_name("active")[index].click()
    driver.find_element_by_class_name("toggle-account-button").click()

    self.wait_page_loaded()
  
  def update_portfolio_records(self):

    driver = self.driver

    self.go_to("https://www.etoro.com/portfolio")

    self.portfolio_records = [elem.text.lower() for elem in driver.find_elements_by_class_name("table-first-name")]

  def open_position(
    self, 
    symbol: str, 
    buy_or_sell: str,
    amount: float = None, 
    leverage: str = None,
    stop_loss: float = None,
    take_profit: float = None,
  ):

    driver = self.driver

    # # Check able to multiple trade on the same symbol
    # if self.multiple_trade:

    #   # Get current total allocated amount
    #   total_allocated_amount = self.get_total_allocated_amount()

    #   # Substract the traded amount
    #   total_allocated_amount -= self._traded_amount

    # # Not able multiple trade
    # else: 
  
    # Update portfolio records
    self.update_portfolio_records()

    # Check the trading size over the opened positions anot
    if (len(self.portfolio_records) - 0) >= self._trading_size:
      self._statistics['limit'] += 1
      print("Unable to open '{symbol}' position due to reach the trading size limit.".format(symbol = symbol.upper()))
      return

    # Check if the symbol opened position
    if symbol in self.portfolio_records:
      self._statistics['repeat'] += 1
      print("{symbol} has opened position.".format(symbol = symbol.upper()))
      return

    # Redirect to the symbol page
    if driver.current_url != "https://www.etoro.com/markets/" + symbol:
      self.go_to("https://www.etoro.com/markets/" + symbol)

    time.sleep(2)

    # Get the 'TRADE' button
    trade_btn = driver.find_element_by_class_name("blue-btn")

    # Check the 'TRADE' button is disable anot
    disabled = trade_btn.get_attribute("disabled")
    if disabled:
      print('{symbol} TRADE button is disabled'.format(symbol = symbol.upper()))
      return

    # Open the trade dialog
    trade_btn.click()

    # Check got dialog opened anot
    try:
      driver.find_element_by_class_name('uidialog-content')
    except NoSuchElementException:
      print("{} unable to open position.".format(symbol.upper()))
      return
    
    time.sleep(2)

    # Start opening order trade
    print("=" * 50)
    print('{buy_or_sell} {symbol}'.format(
      buy_or_sell = buy_or_sell.upper(),
      symbol = symbol.upper()
    ))
    print("=" * 50)

    # Click the sell button if it is sell signal   # default is buy
    if buy_or_sell == 'sell':
      driver.find_elements_by_class_name('execution-head-button')[0].click()

    # Get trade amount
    if amount is None:
      amount = self._trade_amount / self._trading_size
    
    # Fill in the amount want to purchase
    element = driver.find_element_by_class_name('stepper-value')
    ActionChains(driver).click(element).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(str(amount)).perform()
    driver.find_element_by_class_name('stepper-value').send_keys(Keys.ENTER)

    # Check error
    error = driver.find_element_by_class_name('error').text
    if error != '':
      self._statistics['error'] += 1
      print("Unable to open {symbol} position due to ==> {error}".format(
        symbol = symbol.upper(),
        error = error)
      )
      print("-" * 50)
      print('')
      return
    
    # Print trade amount
    print(f'Amount: ${amount}')

    # Get and print current stock price
    stock_price = float(driver.find_element_by_class_name('execution-main-head-price-value').text)
    print('Stock price: ${}'.format(stock_price))

    # Check can set stop loss, leverage and take profit anot
    if driver.find_elements_by_class_name('box-tab-value'):

      # Get spreads fees
      # if symbol in self.spreads_fees.keys():
      #   spread_fee = self.spreads_fees[symbol] * 3
      # else:
      #   spread_fee = 0.0005

      # Check got atr anot
      # if not (atr is None):

      #   # Set earn and loss amount
      #   earn_amount = atr * float(self._risk_ratio.split(':')[0])
      #   loss_amount = atr * float(self._risk_ratio.split(':')[1])

      #   # Set stop loss & take profit
      #   if buy_or_sell == 'buy':
      #     stop_loss = stock_price - loss_amount
      #     take_profit = stock_price + earn_amount
      #   else:
      #     stop_loss = stock_price + loss_amount
      #     take_profit = stock_price - earn_amount

      # else:

      #   # Set earn and loss ratio
      #   earn_ratio = 1 + (float(self._risk_ratio.split(':')[0]) / 1000)
      #   loss_ratio = 1 + (float(self._risk_ratio.split(':')[1]) / 1000)

      #   # Set stop loss & take profit
      #   if buy_or_sell == 'buy':
      #     stop_loss = stock_price / loss_ratio
      #     take_profit = stock_price * earn_ratio
      #   else:
      #     stop_loss = stock_price * loss_ratio
      #     take_profit = stock_price / earn_ratio
      
      # Round the stop loss and take profit
      decimal_length = len(str(stock_price).split('.')[1])
      stop_loss   = round(stop_loss, decimal_length)   if stop_loss else None
      take_profit = round(take_profit, decimal_length) if take_profit else None

      # Set stop loss
      if stop_loss:
        driver.find_elements_by_class_name("box-tab-label")[0].click()
        element = driver.find_elements_by_class_name('stepper-value')[1]
        ActionChains(driver).click(element).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(str(stop_loss)).perform()

      # Set leverage
      if leverage:
        driver.find_elements_by_class_name("box-tab-label")[1].click()

        # Get all leverage options
        leverages = [elem.text for elem in driver.find_elements_by_class_name("risk-itemlevel")]

        # If leverage is in the options
        if leverage in leverages:
          index = leverages.index(leverage)
          driver.find_elements_by_class_name("risk-itemlevel")[index].click()

      # Set take profit
      if take_profit:
        driver.find_elements_by_class_name("box-tab-label")[2].click()
        element = driver.find_elements_by_class_name('stepper-value')[1]
        ActionChains(driver).click(element).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(str(take_profit)).perform()

      # Print out statistics
      driver.find_elements_by_class_name('stepper-value')[0].send_keys(Keys.ENTER) #[1]
      stop_loss = driver.find_elements_by_class_name("box-tab-value")[0].text
      print('Stop loss: {}'.format(stop_loss))
      leverage = driver.find_elements_by_class_name("box-tab-value")[1].text
      print('Leverage: {}'.format(leverage))
      take_profit = driver.find_elements_by_class_name("box-tab-value")[2].text
      print('Take profit: {}'.format(take_profit))    

    # If cannot set stop loss, leverage and take profit
    else:
      driver.find_element_by_class_name("head-button").click() # Close icon btn
      print("{} unable to open position due to no leverage.".format(symbol.upper()))
      return

    # Open position
    time.sleep(1)
    open_trade_btn = driver.find_element_by_class_name("execution-button")
    driver.execute_script("arguments[0].click();", open_trade_btn)

    # Check notification
    driver.find_element_by_class_name("status-notification-wrapper")
    self._statistics['open'] += 1
    print("-" * 50)
    print('{buy_or_sell} {symbol} position opened successful!'.format(
      buy_or_sell = buy_or_sell.capitalize(),
      symbol = symbol.upper())
    )
    print("-" * 50)
    print('')
    
    time.sleep(1)
  
  def close_positions(self, symbols: List[str]):

    driver = self.driver

    # Get current opened positions symbol
    self.update_portfolio_records()

    for symbol in symbols:

      symbol = symbol.split(' - ')[1]

      if not symbol in self.portfolio_records:
        print("No '{}' position opened!".format(symbol.upper()))
        continue

      self.go_to("https://www.etoro.com/portfolio/" + symbol)

      # Get all the the close icons
      # [1:] - remove the first element
      # [1::2] - get the odd number elements (close button)
      close_icons = driver.find_elements_by_class_name("i-ptc-action-icon")[1:][1::2]

      # Close all trades on this symbol
      for close_icon in close_icons:
        # Click the close icon
        close_icon.click()

        # Wait until the dialog appear
        driver.find_element_by_class_name('uidialog-content')

        # Wait for the close trade button prepared
        time.sleep(1)

        # Click the close trade button
        driver.find_element_by_class_name('w-sm-footer-button').click()

        # Wait for notification
        driver.find_element_by_class_name("notification-wrapper")

        time.sleep(1)

      print('All {} positions closed successful!'.format(symbol.upper()))
  
  def print_history_records(self) -> None:

    driver = self.driver

    # Go to history page
    self.go_to(url='https://www.etoro.com/portfolio/history')

    # Rest statistics data
    self._statistics['profit_count'] = 0
    self._statistics['loss_count']   = 0
    self._statistics['total_profit'] = 0.0
    self._statistics['total_loss']   = 0.0

    # Get histories data
    histories_data = driver.find_elements_by_class_name("ui-table-row")

    for history_data in histories_data:

      row_data = history_data.find_element_by_tag_name("ui-table-body-slot")

      # Get open time and prof/loss
      open_time = row_data.find_elements_by_tag_name("ui-table-cell")[3].text.replace('\n', ' ')
      prof_loss = float(row_data.find_elements_by_tag_name("ui-table-cell")[6].text.replace('$', ''))

      # Get the trade opened after the system start
      if open_time < self._system_start_time: # The open time is before system start
        break

      # Calculate profit and loss
      if prof_loss > 0.0:
        self._statistics['total_profit'] += prof_loss
        self._statistics['profit_count'] += 1
      else:
        self._statistics['total_loss'] += prof_loss
        self._statistics['loss_count'] += 1

    # Print statistics
    print("=" * 50)
    print('Statistics')
    print("=" * 50)
    print('Open position:   {}'.format(self._statistics['open']))
    print('Reached limit :  {}'.format(self._statistics['limit']))
    print('Repeat position: {}'.format(self._statistics['repeat']))
    print('Error occur:     {}'.format(self._statistics['error']))
    print('Profit count:    {}'.format(self._statistics['profit_count']))
    print('Loss count:      {}'.format(self._statistics['loss_count']))
    print("-" * 50)
    print('Total profit: ${}'.format(self._statistics['total_profit']))
    print('Total loss:   ${}'.format(self._statistics['total_loss']))
    print('Total earn:   ${}'.format(self._statistics['total_profit'] + self._statistics['total_loss']))
    print("-" * 50)

    self._trade_amount = self._allocate_amount + self._statistics['total_profit'] + self._statistics['total_loss']

  def get_spreads_fees(self) -> dict:
    """
    The spread is the difference between the Buy and Sell prices of a certain asset. 
    Spreads are a common way in which trading platforms charge fees.
    """

    driver = self.driver

    self.go_to(url='https://www.etoro.com/trading/fees/#cfds')

    # get the CFDs tab
    tab = driver.find_element_by_class_name("tab_2")

    # click the currencies
    tab.find_element_by_class_name("row-3").click()

    # get the currencies row
    row = tab.find_element_by_class_name("row-3")

    # click the load more button
    row.find_element_by_class_name("show-more").click()

    # get symbols and pips
    symbols = [elem.text.lower() for elem in row.find_elements_by_class_name("symbol")]
    spread_num = [float(elem.text) for elem in row.find_elements_by_class_name("spread_num")]
    pips = [round((elem * 0.0001), 5) for elem in spread_num]

    # convert 2 lists to dict
    key = symbols
    value = pips
    spreads_fees = {key[i]: value[i] for i in range(len(key))}

    print(spreads_fees)

    self.spreads_fees = spreads_fees



### Open position function
{
  # # Redirect to the market page
  # if driver.current_url != "https://www.etoro.com/discover/markets/" + market_type:
  #   self.go_to("https://www.etoro.com/discover/markets/" + market_type)

  # # Get the stocks list on that market page
  # if not market_type in self.markets.keys():
  #   markets = [elem.text.lower() for elem in driver.find_elements_by_class_name("symbol")]
  #   self.markets[market_type] = markets

  # # Check the symbol is it on the page
  # try:
  #   index = self.markets[market_type].index(symbol)
  # except:
  #   print("{} unable to open position.".format(symbol.upper()))
  #   return

  # # Open symbol dialog
  # n = 0
  # while n < 2:

  #   # Check got dialog anot
  #   try:
  #     driver.find_element_by_class_name('uidialog-content')
  #     break

  #   except NoSuchElementException:
  #     time.sleep(1)
  #     # Click buy or sell trade button
  #     if buy_or_sell == 'buy':
  #       click_element = driver.find_elements_by_class_name("trade-button-title")[1::2][index] # even - buy
  #     else:
  #       click_element = driver.find_elements_by_class_name("trade-button-title")[::2][index] # odd - sell
  #     driver.execute_script("arguments[0].click();", click_element)

  #     n = n + 1
}
