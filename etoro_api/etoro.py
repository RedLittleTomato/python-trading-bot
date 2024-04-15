import os
import ast
import time
import json
import pprint
import requests

from datetime import datetime
from selenium import webdriver
from configparser import ConfigParser
from typing import List
from typing import Dict
from dataclasses import dataclass

# Grab configuration values.
config = ConfigParser()
config.read("config/config.ini")

BASE_URL = config.get("main", "base_url")
EMAIL = config.get("main", "email")
PASSWORD = config.get("main", "password")

@dataclass
class ViewContext():
  ClientViewRate: float

@dataclass
class EtoroPosition():
  PositionID: str
  InstrumentID: str
  IsBuy: bool
  Leverage: int
  StopLossRate: float 
  TakeProfitRate: float 
  IsTslEnabled: bool
  View_MaxPositionUnits: int
  View_Units: float 
  View_openByUnits: bool
  Amount: float
  ViewRateContext: ViewContext
  OpenDateTime: str
  IsDiscounted: bool
  OpenRate: float
  CloseRate: float
  NetProfit: float
  CloseDateTime: str

@dataclass
class EtoroPositionForOpen():
  PositionID: str
  InstrumentID: str
  IsBuy: bool
  Leverage: int
  StopLossRate: float
  TakeProfitRate: float
  IsTslEnabled: bool
  View_MaxPositionUnits: int
  View_Units: float
  View_openByUnits: bool
  Amount: float
  ViewRateContext: ViewContext
  OpenDateTime: str
  IsDiscounted: bool

@dataclass
class AssetInfoRequest():
  instrumentIds: List

@dataclass
class RequestHeaders():
  instrumentIds: List


class Etoro():

  def __init__(self):

    self.token = None
    self.cookies = None
    self.expiration_time = None
    self.positions = {}
    self.instruments_metadata = self._instruments_metadata()
    self.instrument_ids = []

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

    # self.driver = webdriver.Chrome(options=options, executable_path=chromedriver)
  
  def login(self):
    driver = self.driver
    driver.get(BASE_URL + "/login")

    driver.find_element_by_id("username").send_keys(EMAIL)
    driver.find_element_by_id("password").send_keys(PASSWORD)
    driver.find_element_by_class_name("blue-btn").click()

    login_data = None
    seconds = 0

    while True:
      try:
        # get token from local storage by execute Javascript
        login_data = driver.execute_script("return window.atob(window.localStorage.loginData);")
        
        if login_data is not None:
          print("Login data retrieved after {} seconds".format(seconds))
          break

      except Exception as e:
        print(e)
        if seconds > 5:
          print("Timeout")
          break

        time.sleep(1) # sleep one second
        seconds += 1
    
    # convert string to json format return dict
    login_data = json.loads(login_data) 

    token = login_data["stsData_app_1"]["accessToken"]
    expiration_time_ms =  login_data["stsData_app_1"]["expirationUnixTimeMs"]
    expiration_time = datetime.fromtimestamp(expiration_time_ms / 1000.0) # the unix timestamp is in ms format

    print("Token: " + token)
    print("Expires at: {}".format(expiration_time))

    self.token = token
    self.expiration_time = expiration_time

    cookiesSet = driver.get_cookies()
    cookies = "; ".join([str(element) for element in cookiesSet])
    print(cookies)

    driver.quit()

  def get_metadata(self) -> Dict:
    current_time = datetime.now()

    if self.expiration_time is None or current_time > self.expiration_time:
      self.login()
    
    return {
      "cookies": self.cookies,
      "token": self.token,
      "lsPassword": """{"UserAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36","ApplicationVersion":"213.0.2","ApplicationName":"ReToro","AccountType":"Demo","ApplicationIdentifier":"ReToro"}""",
      "baseUrl": "https://www.etoro.com",
      "domain": "www.etoro.com"
    }
  
  # def open_position(self) -> self.EtoroPositionForOpen:
  #   buy_or_sell = "buy"

  def _instruments_metadata(self) -> List[Dict]:

    instrument_type_id = {
      1: 'currencies',
      2: 'commodities',
      4: 'indices',
      5: 'stock',
      6: 'etf',
      10: 'cryptocurrencies'
    }

    url = "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"
    res = requests.get(url)
    instruments_metadata = json.loads(res.text.lower())["instrumentdisplaydatas"]

    for instrument in instruments_metadata:
      # remove images
      instrument.pop("images")

    return instruments_metadata

  def grab_historical_candles(self, instrument_ids: List[int], period: str) -> List[dict]:
    
    self.instrument_ids = instrument_ids

    period_list = {
      '1M': 'oneminute',
      '5M': 'fiveminutes',
      '10M': 'tenminutes',
      '15M': 'fifteenminutes',
      '1H': 'onehour',
      '4H': 'fourhours',
      '1D': 'oneday',
      '1W': 'oneweek',
    }

    if period not in period_list:
      raise Exception("Period allowed: 1M, 5M, 10M, 15M, 1H, 4H, 1D, 1W")

    historical_candles = []

    for instrument_id in instrument_ids:

      url = "https://candle.etoro.com/candles/asc.json/{period}/500/{instrument_id}".format(
        period = period_list.get(period),
        instrument_id = instrument_id
      )
      res = requests.get(url)

      candles = json.loads(res.text.lower())["candles"][0]["candles"]

      # get symbol by the instrument id
      symbol = next((item for item in self.instruments_metadata if item["instrumentid"] == instrument_id), None)["instrumentdisplayname"]

      # replace the instrument ID to symbol
      # for candle in candles:
      #   # candle.pop("instrumentid")
      #   candle["instrumentid"] = str(candle["instrumentid"]) + ' - ' + symbol

      historical_candles.extend(candles)
      
    return historical_candles
