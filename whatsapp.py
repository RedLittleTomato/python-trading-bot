from pyrobot.twilio_whatsapp import WhatsApp
from configparser import ConfigParser

# account_sid = 'ACf9f9c5347bf9b0fb1b493e35f1eb1caf'
# auth_token = '55585d50f7ffdf599deca9bd00de2fd6'

# client = Client(account_sid, auth_token)

# from_whatsapp_number = 'whatsapp:+14155238886'
# to_whatsapp_number = 'whatsapp:+60194437719'

# client.messages.create(
#   body='hello\nds',
#   from_=from_whatsapp_number,
#   to=to_whatsapp_number
# )

# Grab configuration values.
config = ConfigParser()
config.read("config/config.ini")

account_sid = config.get("twilio_whastapp", "account_sid")
auth_token = config.get("twilio_whastapp", "auth_token")
to_whatsapp_number = config.get("twilio_whastapp", "to_whatsapp_number")

client = WhatsApp(account_sid=account_sid, auth_token=auth_token, to_whatsapp_numbers=[to_whatsapp_number])

signal = '🔴 SELL'
symbol = 'GOLD'
open = 1278.21
stop_loss   = 1278.21
take_profit =  1278.21

message = []
separator = '\n'

message.append(f"*{signal} {symbol}*   ```OPEN({open})```")
# message.append(f"OPEN {open}")
# message.append(f"")

if stop_loss != '':
  message.append(f"```SL {stop_loss}```")

if take_profit != '':
  message.append(f"```TP {take_profit}```")

message = separator.join(message)

client.send_signal_message(message)