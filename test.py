from re import S
import time
import pyupbit
import datetime
import pandas as pd
from pandas.tseries.offsets import Day, Hour, Minute, Second
import schedule
from fbprophet import Prophet
from slacker import Slacker
import datetime as dt
import numpy as np
import requests
import traceback
import pytz
import openpyxl
KST = datetime.timezone(datetime.timedelta(hours=9))

access = "YttVn2BhLicTA5b02xrZc5ydbqYGjvpnhbP9wTdP"
secret = "LtpkDjfN9gNvEtgA6u3AIMqvx86bQ6rBSLzoqJlq"
myToken = "xoxb-3149418271687-3600159322736-3xQHb32Q0LrEf6Yam3Cr1mBb"
T_Token = "xoxb-3149418271687-3582406642517-c0ezQQDHR4kGHm4cYHYQ3EtG"
sell_key=["1",2,3]

def post_message(token, channel, text):
    # time.sleep(0.01)
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=6) #현재시간 10분 단위 30분전 데이터의 고점 저점을 기준으로 계산            *
    current_price = get_current_price(ticker)
    k=0.5
    target_price=[]

    for i in range(5):
        target_price.append(df.iloc[i]['close'] + (df.iloc[i]['high'] - df.iloc[i]['low']) * k) #현재 종가 + 과거 고점-저점*0.k배
    if(current_price>max(target_price)):
        result="매수"
    else:
        result="보류"
    return result

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def time_changer(now_time,time):
    hour_ch=now_time.hour
    minute10= int((now_time.minute//10)*10)+time #                           *
    if minute10>=60: # 분은 0-59까지 나타남으로 60 이상이면 오류가남
        minute10=minute10-60 # 현재 시간에 30분을 더해 60이 넘어가면 시간을 1늘리고 60분을 빼줌
        hour_ch+=1
    if hour_ch>23:
        hour_ch=0
    return hour_ch, minute10

few_minutes_later=datetime.datetime.strptime('2000-05-15 20:05:15','%Y-%m-%d %H:%M:%S').replace(tzinfo=KST)
predicted_close_price = list()


def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=30) #10분 단위 데이터 불러옴                *
    df = df.reset_index()
    df['ds'] = df['index'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['y'] = df['close']
    data = df[['ds','y']]
    data=pd.DataFrame(data)
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq=Minute(10))#freq=Minute(30) #10분 단위의 과거값을 기준으로 미래값 예측                *
    forecast = model.predict(future)
    now=datetime.datetime.now(KST)#서버의 위치가 다른 나라일 경우를 대비해 현재 대한민국 기준 시각 사용
    hour_ch, minute10=time_changer(now,10)#현시각보다 30분 뒤의 시각을 계산
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(minute=minute10, hour=hour_ch)]#현재 시간 보다 30분 뒤의 예측값을 불러옴
    if len(closeDf) == 0: 
        closeDf = forecast[forecast['ds'] == datetime.datetime.strptime(data.iloc[-1]['ds'], '%Y-%m-%d %H:%M:%S').replace(minute=minute10, hour=hour_ch)]
    closeValue = closeDf['yhat'].values[0]
    print(future,forecast,closeDf,closeValue)
    predicted_close_price.append(closeValue)
    
predict_price("KRW-BTC")
schedule.every(10).minutes.do(lambda: predict_price("KRW-BTC"))#.every(10).minutes. 
predict_price("KRW-ETH")
schedule.every(10).minutes.do(lambda: predict_price("KRW-ETH"))
predict_price("KRW-BCH")
schedule.every(10).minutes.do(lambda: predict_price("KRW-BCH"))
predict_price("KRW-ETC")
schedule.every(10).minutes.do(lambda: predict_price("KRW-ETC"))
predict_price("KRW-AAVE")
schedule.every(10).minutes.do(lambda: predict_price("KRW-AAVE"))
predict_price("KRW-NEO")
schedule.every(10).minutes.do(lambda: predict_price("KRW-NEO"))
predict_price("KRW-WAVES")
schedule.every(10).minutes.do(lambda: predict_price("KRW-XRP"))
predict_price("KRW-LSK")
schedule.every(10).minutes.do(lambda: predict_price("KRW-LSK"))
# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
post_message(myToken,"#bitcoinauto-ai", "autotrade start")

def rsi(ohlc: pd.DataFrame, period: int = 14):
    ohlc["close"] = ohlc["close"]
    delta = ohlc["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
        
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        
    RS = _gain / _loss
    rsi_current=pd.Series(_gain/(_gain+_loss)*100, name="RSI")
    if ((rsi_current.iloc[199] >rsi_current.iloc[195])): #(rsi_current.iloc[196]<rsi_current.iloc[198])and(rsi_current.iloc[196]>rsi_current.iloc[197])and(rsi_current.iloc[197]<rsi_current.iloc[198]) and 
         rsi="매수"
    elif (rsi_current.iloc[196]<rsi_current.iloc[197])and(rsi_current.iloc[197]>rsi_current.iloc[198]):
        rsi="매도"
    else:
        rsi="보류"
    return rsi

def macd(df: pd.DataFrame, macd_short:int=12, macd_long:int=26, macd_signal:int=9):
    df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
    df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
    df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
    df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9
        #df["vertex_Gap_20"]=(abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196])<abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197]))and(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #30분전~현재를 비교해 macd가 꼭짓점인지 확인--0+
        #df["vertex_Gap_10"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #20분전~현재를 비교해 macd가 꼭짓점인지 확인-0+
        #df["vertex_Gap"]=(abs(df["MACD"].iloc[195]-df["MACD_signal"].iloc[195])<abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196]))and(abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196])<abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197]))and(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
    
    #df["vertex_buy"]=(df["MACD"].iloc[196]>df["MACD"].iloc[197])and(df["MACD"].iloc[197]<df["MACD"].iloc[198])
    #df["vertex_sell"]=(df["MACD"].iloc[196]<df["MACD"].iloc[197])and(df["MACD"].iloc[197]>df["MACD"].iloc[198])
    #macd가 꼭짓점인지 확인--0++
    df["convergence"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])<abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 수렴하고 있는지 확인
        #df["diffusion"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])<abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 확산하고 있는지 확인

    df["macd_down"]=(df["MACD_signal"].iloc[199]>df["MACD"].iloc[199])and(df["MACD_signal"].iloc[198]>df["MACD"].iloc[198])and(df["MACD_signal"].iloc[197]>df["MACD"].iloc[197])
    #1단위 전부터 현재까지 macd가 macd_signal보다 작은지
    df["macd_up"]=(df["MACD_signal"].iloc[198]<df["MACD"].iloc[198])and(df["MACD_signal"].iloc[199]<df["MACD"].iloc[199])and(df["MACD_signal"].iloc[197]<df["MACD"].iloc[197])
    #macd가 macd_signal보다 큰지
    #df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
    #df["buy"]=((df["MACD_signal"]-df["MACD"])/df["MACD_signal"])#살 지점 정하기 - 수렴 측정때 사용
    #df["sell"]=((df["MACD"]-df["MACD_signal"])/df["MACD"])#팔 지점 정하기 - 확장 측정때 사용
    df["MACD_sign"]=df.apply(lambda x: ("매수" if x["convergence"] and x["macd_up"] else ("매도" if x["macd_down"] else "보류")), axis=1) # 구매여부 
    return df["MACD_sign"]

def AI(target, name, set_time, i):
    global few_minutes_later
    schedule.run_pending()
    df = pyupbit.get_ohlcv(target, interval="minute10")
    rsi_current = rsi(df, 14)
    price = pyupbit.get_current_price(target)
    target_price = get_target_price(target)#이걸 변경하면 구매전략 변경됨, 변동성 돌파전략을 이용한 목표가 설정
    current_price = get_current_price(target)
    macd_current = macd(df,12,26,9).iloc[-1]
    # print(target,target_price,current_price,predicted_close_price[i],target_price < current_price and current_price < predicted_close_price[i])
    if (rsi_current=="매수" and target_price=="매수" and macd_current=="매수" and current_price < predicted_close_price[i]):
        krw = get_balance("KRW")
        if krw > 5000:
            post_message(myToken,"#bitcoinauto-ai", "Coin buy : " +target+"  "+str(krw)+"  "+str(current_price))
            buy_result = upbit.buy_market_order(target, krw*0.9995)#돌파하면 구매
            sell_key[0]=target
            sell_key[1]=current_price
            sell_key[2]=rsi_current
            hour_ch, minute10=time_changer(now,40)
            few_minutes_later = now.replace(minute=minute10, hour=hour_ch)#30분 후----------------------------------- 
            post_message(myToken, "#bitcoinauto-ai", few_minutes_later)   
    elif (now >= few_minutes_later and current_price>sell_key[1]):
        btc = get_balance(name)
        if btc > (5000/price):
            sell_result = upbit.sell_market_order(target, btc*0.9995)
            krw = get_balance("KRW")
            post_message(myToken,"#bitcoinauto-ai", "Coin sell : " +target+"  "+str(krw)+"  "+str(current_price))
            sell_key[0]=1.0
            sell_key[1]=1.0
            sell_key[2]=1.0
            print("")
    time.sleep(1)

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now(KST)#서버의 위치가 다른 나라일 경우를 대비해 현재 대한민국 기준 시각 사용
        AI("KRW-BTC","BTC",now,0)

        
        if(now.minute==0 and now.second<=5):#정시 마다 프로세스 확인
            post_message(T_Token,"#bitcoinauto-ai", "프로세스가 돌아가고 있습니다 ")

    except Exception as e:
        # print(e)
        # print(traceback.format_exc())
        post_message(myToken,"#bitcoinauto-ai",traceback.format_exc())
        post_message(myToken,"#bitcoinauto-ai", e)
        time.sleep(1)