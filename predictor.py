import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pandas_datareader as web
import datetime as dt

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM

currency = 'BTC-USD'

# start = dt.datetime(2019,1,1)
# end = dt.datetime(2020,1,1)

# data = web.DataReader(currency, 'yahoo', start, end)
# print(data)

from configparser import ConfigParser
from robot import Robot

config = ConfigParser()
config.read("config/config.ini")
EMAIL = config.get("main", "email")
PASSWORD = config.get("main", "password")

trade = False
period = '15M'

trading_robot = Robot(
  email = EMAIL,
  password = PASSWORD,
  trade = trade,
  mode = 'virtual'
)

instruments_ids = trading_robot.get_instruments_ids(instrument_type='currencies')

historical_candles = trading_robot.grab_historical_candles(instrument_ids=[1], period=period)

stock_frame = trading_robot.create_stock_frame(data=historical_candles)

data = stock_frame._frame

# prepare data
scaler = MinMaxScaler(feature_range=(0,1))
scaled_data = scaler.fit_transform(data['close'].values.reshape(-1,1))

prediction_days = 160

x_train = []
y_train = []

for x in range(prediction_days, len(scaled_data)):
  x_train.append(scaled_data[x-prediction_days:x, 0])
  y_train.append(scaled_data[x, 0])

x_train, y_train = np.array(x_train), np.array(y_train)
x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

# build model
model = Sequential()

model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
model.add(Dropout(0.2))
model.add(LSTM(units=50, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(units=50))
model.add(Dropout(0.2))
model.add(Dense(units=1)) # Prediction of the next closing

model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(x_train, y_train, epochs=25, batch_size=32)

# Test the model accuracy on existing data
test_start = dt.datetime(2020,1,1)
test_end = dt.datetime.now()

# test_data = web.DataReader(currency, 'yahoo', test_start, test_end)
test_data = data
actual_prices = test_data['close'].values

total_dataset = pd.concat((data['close'], test_data['close']), axis=0)

model_inputs = total_dataset[len(total_dataset) - len(test_data) - prediction_days:].values
model_inputs = model_inputs.reshape(-1, 1)
model_inputs = scaler.transform(model_inputs)

# make prediction on test data
x_test = []

for x in range(prediction_days, len(model_inputs)):
  x_test.append(model_inputs[x-prediction_days:x, 0])

x_test = np.array(x_test)
x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

predicted_prices = model.predict(x_test)
predicted_prices = scaler.inverse_transform(predicted_prices)

# plot the test predictions
plt.plot(actual_prices, color='black', label=f"Actual {currency} Price")
plt.plot(predicted_prices, color='green', label=f"Predicted {currency} Price")
plt.title(f"{currency} Share Price")
plt.xlabel('Time')
plt.ylabel(f"{currency} Share Price")
plt.legend()
plt.show()

# predict the next close price
real_data = [model_inputs[len(model_inputs) + 1 - prediction_days:len(model_inputs+1), 0]]
real_data = np.array(real_data)
real_data = np.reshape(real_data, (real_data.shape[0], real_data.shape[1], 1))

prediction = model.predict(real_data)
prediction = scaler.inverse_transform(prediction)
print(f"Prediction: {prediction}")