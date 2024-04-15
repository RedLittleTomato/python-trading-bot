from etoro_api.rest_api import RESTAPIs

class Metadata():
  """The metadata API provides basic meta data for the eToro system. The metadata is comprised of reference tables for all the other end-points in this API"""

  def __init__(self):
    self.call_api = RESTAPIs()
  
  def get_asset_classes(self) -> List[dict]:  
    """Returns the asset classes of the system

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [
      {
          assetClassId: 1,
          name: "Forex"
      },
      {
          assetClassId: 2,
          name: "Commodity"
      }
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/AssetClasses",
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data

  def get_candle_periods(self) -> List[dict]:  
    """Returns the intervals in which you may retrieve historical price candles

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [
      {
          candlePeriodId: 1,
          name: "OneMinute"
      },
      {
          candlePeriodId: 2,
          name: "FiveMinutes"
      }
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/CandlePeriod",
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data

  def get_countries(self) -> List[dict]:  
    """Returns a vector of all countries recognized in the system. Each member contains an internal country id, it's name and its abbreviation

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [
      {
        "countryId": 1,
        "name": "Afghanistan",
        "abbreviation": "AF"
      },
      {
        "countryId": 2,
        "name": "Albania",
        "abbreviation": "AL"
      },
      {
        "countryId": 3,
        "name": "Algeria",
        "abbreviation": "DZ"
      }
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/Countries",
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data

  def get_exchanges(self) -> List[dict]:  
    """Returns a vector of all the exchanges defined in the system.

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [
      {
          exchangeId: 1,
          name: "FX"
        },
        {
          exchangeId: 5,
          name: "NYSE"
        },
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/Exchanges",
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data

  def get_instruments(self, InstrumentIds: str=None) -> List[dict]:  
    """Returns the instruments which are defined in the system.

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [   
      {      
        instrumentId: 1001,      
        name: "Apple",      
        assetClassId: 5,      
        exchangeId: 4,      
        sectorId: 3,      
        ticker: "AAPL",      
        percision: 2,      
        media: [         
          {            
            width: 35,            
            height: 35,            
            uri: "https://etoro-cdn.etorostatic.com/market-avatars/aapl/35x35.png"         
          },       
          {           
            width: 50,           
            height: 50,           
            uri: "https://etoro-cdn.etorostatic.com/market-avatars/aapl/50x50.png"        
          }      
        ]
      }
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/Instruments",
      query_params=InstrumentIds
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data

  def get_sectors(self) -> List[dict]:  
    """Returns a vector of all the stock sectors in the system

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [
      {
          sectorId: 1,
          name: "Basic Materials"
      },
      {
          sectorId: 2,
          name: "Conglomerates"
      },
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/Sectors",
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data

  def get_stats_periods(self) -> List[dict]:  
    """Returns the predefined periods used for aggregate data

    Returns:
    ----
    Response 200 --> 
    List[dict]:
    [
      {
          period: "CurrMonth",
          minDate: "2016-07-01T00:00:00Z"
      },
      {
          period: "CurrQuarter",
          minDate: "2016-07-01T00:00:00Z"
      }
    ]
    """

    res = self.call_api.GET(
      url="/Metadata/V1/StatsPeriods",
    )

    if res.status == 200:
      data = res.read()
    else:
      raise SystemExit(res.reason)

    return data