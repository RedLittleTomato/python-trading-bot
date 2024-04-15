import json
import http.client

from configparser import ConfigParser

# Grab configuration values.
config = ConfigParser()
config.read("config/config.ini")

SUBSCRIPTION_KEY = config.get("main", "subscription_key")

class RESTAPIs():

  def __init__(self):
    self.subscription_key = SUBSCRIPTION_KEY

  def request(self, method: str, url: str, query_params=None, headers={}, body=None):

    # check request method
    method = method.upper()
    assert method in ['GET', 'POST', 'PUT', 'DELETE']

    headers = {
      'Ocp-Apim-Subscription-Key': self.subscription_key,
    }

    params = json.dumps(query_params)

    try:
      conn = http.client.HTTPSConnection('api.etoro.com')
      conn.request(method, "{url}?%s" % params, "{body}", headers)
      response = conn.getresponse()
      conn.close()
    except Exception as e:
      print("[Errno {0}] {1}".format(e.errno, e.strerror))
      response = e.strerror
    
    return response

  def GET(self, url, headers=None, query_params=None):
    return self.request(
      method="GET", 
      url=url,
      query_params=query_params,
      headers=headers,
    )
  
  def POST(self, url, headers=None, query_params=None, body=None):
    return self.request(
      method="POST", 
      url=url,
      query_params=query_params,
      body=body,
      headers=headers,
  )

  def PUT(self, url, headers=None, query_params=None, body=None):
    return self.request(
      method="PUT", 
      url=url,
      query_params=query_params,
      body=body,
      headers=headers,
  )

  def DELETE(self, url, headers=None, query_params=None, body=None):
    return self.request(
      method="DELETE", 
      url=url,
      query_params=query_params,
      body=body,
      headers=headers,
  )