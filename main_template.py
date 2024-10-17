from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flasgger import Swagger

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)
    
class TickerInfo(Resource):
    def get(self):
        """
        Call Yfinance to retrieve data
        ---
        tags:
        - YFinance
        parameters:
            - name: Tickers
              in: query
              type: string
              required: true
              description: List of Tickers seperated by commas
        responses:
            200:
                description: A successful GET request
                content:
                    application/json:
                      schema:
                        type: object
                        properties:
                            text:
                                type: objects
                                description: list of ticker info
        """
        tickers = str(request.args.get('Tickers'))

        ticker_list = tickers.split(",")
        print(ticker_list)
        data = {'Tickers': []}
        for item in ticker_list:
            item_data = self.get_indicators(item)
            if (type(item_data) != int ):
                data['Tickers'].append(item_data)
            else:
                data['Tickers'].append({"Ticker": "",
                "MACD": 0.0,
                "MACD_Signal": 0.0,
                "RSI": 0.0,
                "STOCH_K": 0.0,
                "B_Low": 0.0,
                "B_Mid": 0.0,
                "B_Upper": 0.0,
                "SMA50": 0.0,
                "SMA200": 0.0,
                "52WeekHigh": 0.0,
                "Open": 0.0,
                "time_elapsed": 0.0})

        return jsonify(data)

    def get_indicators(self,ticker):
        start = time.time()
        try:
            symbol = yf.Ticker(ticker)
            df = symbol.history(interval='1d', period='1y')
            newdf = pd.DataFrame()
            newdf.insert(0,"Ticker", "")
            newdf.ta.macd(close=df["Close"], fast=12, slow=26, signal=9, append=True, col_names=("MACD","MACD_Histogram","MACD_Signal"))
            newdf.ta.rsi(close=df["Close"], length=20, append=True, col_names=("RSI",))
            newdf.ta.stoch(high=df["High"], low=df["Low"], close=df["Close"], append=True, col_names=("STOCH_K", "STOCH_D"))
            newdf.ta.bbands(close=df["Close"], length=20, append=True, col_names=("B_Low", "B_Mid", "B_Upper", "B_Bandwidth", "B_Percent"))
            newdf.ta.sma(close=df["Close"], length=50, append=True, col_names=("SMA50"))
            newdf.ta.sma(close=df["Close"], length=200, append=True, col_names=("SMA200"))
            newdf["52WeekHigh"] = df["Close"].rolling(window=200, min_periods=1).max()

            payload = newdf.tail(1).to_dict('records')[0]
            del payload['MACD_Histogram']
            del payload['STOCH_D']
            del payload['B_Bandwidth']
            del payload['B_Percent']

            payload["Ticker"] = ticker
            payload["Open"] = df.iloc[-1]["Close"]
            end = time.time()
            payload["time_elapsed"] = end-start
            return payload
        except:
            return 0

api.add_resource(TickerInfo, "/tickerinfo")

if __name__ == "__main__":
    app.run(debug=True)