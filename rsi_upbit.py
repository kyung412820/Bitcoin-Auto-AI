import requests
import pandas as pd
import time
import webbrowser
import pyupbit
import datetime
KST = datetime.timezone(datetime.timedelta(hours=9))

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

myToken = "xoxb-3149418271687-3570845581063-phA6FSWjs0qG3sd2sAVP0Cql"

tickers = pyupbit.get_tickers(fiat="KRW")

post_message(myToken,"#macd_rsi_30min",'Upbit 30 minute MACD_RSI_IM Start')

while True:
    try:
        def rsiindex(symbol):
            now = datetime.datetime.now()
            now = now.replace(tzinfo=KST)
            url = "https://api.upbit.com/v1/candles/minutes/10"

            querystring = {"market":symbol,"count":"500"}
            response = requests.request("GET", url, params=querystring)
            data = response.json()
            df = pd.DataFrame(data) #10분단위로 format값을 다 들고옴
            df=df.reindex(index=df.index[::-1]).reset_index()
        
            df['close']=df["trade_price"]
            '''
            def macd(df: pd.DataFrame, macd_short:int=12, macd_long:int=26, macd_signal:int=9):
                df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
                df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
                df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
                df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9
                df["upperdown"]=((df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and((df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
                #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 수렴하고 있는지 확인
                df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
                # print(df["MACD"].iloc[198],df["MACD_signal"].iloc[198],df["MACD"].iloc[199],df["MACD_signal"].iloc[199],df["upperdown"])
                print(df["MACD"].iloc[-1],df["MACD_signal"].iloc[-1])
                print((df["MACD_signal"].iloc[-1]-df["MACD"].iloc[-1])/df["MACD_signal"].iloc[-1],(df["MACD"].iloc[-1]-df["MACD_signal"].iloc[-1])/df["MACD"].iloc[-1],df["upperdown"].iloc[-1])
                df["MACD_sign"]=df.apply(lambda x: ("매수" if (x["MACD"]<x["MACD_signal"] and ((x["MACD_signal"]-x["MACD"])/x["MACD_signal"]) < 0.1 and x["upperdown"]==True) else ("매도" if x["MACD"]>x["MACD_signal"] and ((x["MACD"]-x["MACD_signal"])/x["MACD"])>1 and x["upperdown"]==False else "보류")), axis=1) # 구매여부
                return df["MACD_sign"]'''

            def macd(df: pd.DataFrame, macd_short:int=12, macd_long:int=26, macd_signal:int=9):
                df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
                df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
                df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
                df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9

                df["vertex_20"]=(abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196])<abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197]))and(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
                #30분전~현재를 비교해 macd가 꼭짓점인지 확인--0+
                df["vertex_10"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
                #20분전~현재를 비교해 macd가 꼭짓점인지 확인-0+

                df["vertex"]=(abs(df["MACD"].iloc[195]-df["MACD_signal"].iloc[195])<abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196]))and(abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196])<abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197]))and(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
                #macd가 꼭짓점인지 확인--0++

                    #df["convergence"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
                    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 수렴하고 있는지 확인
                    #df["diffusion"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])<abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
                    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 확산하고 있는지 확인

                df["macd_down"]=(df["MACD_signal"].iloc[198]>df["MACD"].iloc[198])and(df["MACD_signal"].iloc[199]>df["MACD"].iloc[199])
                #1단위 전부터 현재까지 macd가 macd_signal보다 작은지
                df["macd_up"]=(df["MACD_signal"].iloc[198]<df["MACD"].iloc[198])and(df["MACD_signal"].iloc[199]<df["MACD"].iloc[199])
                #macd가 macd_signal보다 큰지
                df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
                #df["buy"]=((df["MACD_signal"]-df["MACD"])/df["MACD_signal"])#살 지점 정하기 - 수렴 측정때 사용
                #df["sell"]=((df["MACD"]-df["MACD_signal"])/df["MACD"])#팔 지점 정하기 - 확장 측정때 사용
                df["MACD_sign"]=df.apply(lambda x: ("매수" if (x["macd_down"] and x["vertex_20"]==True) else ("매도" if (x["macd_up"] and x["vertex"]==True) else "보류")), axis=1) # 구매여부 
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
            
            print(rsi,macd,symbol, now)
        
            if rsi <= 20 and macd =="매수":
                post_message(myToken,"#macd_rsi_30min", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★★★★ < 20 >')
            elif rsi <=25 and macd=="매수":
                post_message(myToken,"#macd_rsi_30min", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★★★ < 25 >')
            elif rsi <=30 and macd=="매수":
                post_message(myToken,"#macd_rsi_30min", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★★ < 30 >')
            # elif rsi <=35 and macd=="매수":
            #     post_message(myToken,"#macd_rsi_30min", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★★ < 35 >')
            # elif rsi <=40 and macd=="매수":
            #     post_message(myToken,"#macd_rsi_30min", 'RSI : '+str(rsi)+'\t'+symbol+'\t'+'★ < 40 >')
            # elif macd=="매수" and now.minute<5:
            #     post_message(myToken,"#macd_rsi_30min", 'RSI : '+str(rsi)+'\t'+symbol)
            time.sleep(1)
        for ticker in tickers:
            #if now.minute<10:
                rsiindex(ticker)

    except Exception as e:
        print(e)
        post_message(myToken,"#macd_rsi_30min", e)
        time.sleep(1)