import time as time_true

from twilio.rest import Client
from typing import List

class WhatsApp():

  def __init__(self, account_sid: str, auth_token: str, to_whatsapp_numbers: List[str]) -> None:

    self._client = Client(account_sid, auth_token)
    self._from_whatsapp_number = 'whatsapp:+14155238886'
    self._to_whatsapp_number = to_whatsapp_numbers[0]

  def send_signal_message(self, message: str) -> None:

    self._client.messages.create(
      # body='🔴🟠 *BUY GOLD* \n SL: 1830.00',
      body=message,
      from_=self._from_whatsapp_number,
      to=self._to_whatsapp_number
    )

    time_true.sleep(1)
  
  def send_multiple_message(self, messages: List[str]) -> None:

    for message in messages:

      self.send_signal_message(message)