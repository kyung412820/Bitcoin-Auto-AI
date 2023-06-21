import requests
import pandas as pd
import time
import webbrowser
import pyupbit
import datetime

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

myToken = "xoxb-3149418271687-3570845581063-phA6FSWjs0qG3sd2sAVP0Cql"

tickers = pyupbit.get_tickers(fiat="KRW")

print('Upbit 10 minute RSI')

while True:
    try:
        def rsiindex(symbol):
            now = datetime.datetime.now()
            url = "https://api.upbit.com/v1/candles/minutes/10"

            querystring = {"market":symbol,"count":"500"}
        
            response = requests.request("GET", url, params=querystring)
            data = response.json()
            df = pd.DataFrame(data)
            df=df.reindex(index=df.index[::-1]).reset_index()
        
            df['close']=df["trade_price"]
            '''
            def macd(df: pd.DataFrame, macd_short:int=12, macd_long:int=26, macd_signal:int=9):
                df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
                df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
                df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
                df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9
                df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
                df["MACD_sign"]=df.apply(lambda x: ("매수" if x["MACD"]>x["MACD_signal"] else "매도"), axis=1) # 구매여부
                return df["MACD_sign"]'''

            def macd(df: pd.DataFrame, macd_short:int=12, macd_long:int=26, macd_signal:int=9):
                df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
                df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
                df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
                df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9
                df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
                df["MACD_sign"]=df.apply(lambda x: ("매수" if (x["MACD"]<x["MACD_signal"] and (x["MACD_signal"]-x["MACD"])< 2) else ("매도" if x["MACD"]>x["MACD_signal"] and x["MACD"]-x["MACD_signal"]>10  else "보류")), axis=1) # 구매여부
                return df["MACD_sign"]
        
            def rsi(ohlc: pd.DataFrame, period: int = 14):
                ohlc["close"] = ohlc["close"]
                delta = ohlc["close"].diff()
                up, down = delta.copy(), delta.copy()
                up[up < 0] = 0
                down[down > 0] = 0
        
                _gain = up.ewm(com=(period - 1), min_periods=period).mean()
                _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        
                RS = _gain / _loss
                return pd.Series(_gain/(_gain+_loss)*100, name="RSI")
        
            rsi = rsi(df, 14).iloc[-1]
            macd=macd(df,12,26,9).iloc[-1]
            #print(rsi,macd,symbol)

            if rsi <= 20 and macd =="매수":
                post_message(myToken,"#auxiliary-indicator", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★★★★ < 20 >')
            elif rsi <=25 and macd=="매수":
                post_message(myToken,"#auxiliary-indicator", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★★★ < 25 >')
            elif rsi <=30 and macd=="매수":
                post_message(myToken,"#auxiliary-indicator", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★★ < 30 >')
            elif rsi <=35 and macd=="매수":
                post_message(myToken,"#auxiliary-indicator", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★ < 35 >')
            # elif rsi <=40 and macd=="매수"and now.minute<15:
            #     post_message(myToken,"#auxiliary-indicator", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★ < 40 >')
            time.sleep(1)
        for ticker in tickers:
            #if now.minute<10:
                rsiindex(ticker)

    except Exception as e:
        print(e)
        post_message(myToken,"#auxiliary-indicator", e)
        time.sleep(1)