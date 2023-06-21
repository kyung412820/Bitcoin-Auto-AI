from re import S
import time
import pyupbit
import datetime
import pandas as pd
from pandas.tseries.offsets import Day, Hour, Minute, Second
import schedule
#from fbprophet import Prophet
from slacker import Slacker
import datetime as dt
import numpy as np
import requests
import traceback
import pytz
import ta
from time import sleep
KST = datetime.timezone(datetime.timedelta(hours=9))


access = "VniXlnhdMPVIQO96iT8fHQP0PwQlJnHqKY5L2yCc"
secret = "0LyCDz4X2BxBY8sRjGuviepZxveNhs8m9rGwzwil"
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
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=11) #현재시간 10분 단위 30분전 데이터의 고점 저점을 기준으로 계산            *
    current_price = get_current_price(ticker)
    k=0.5
    target_price=[] 
    for i in range(10):
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
    if (rsi_current.iloc[197]<=30): #(rsi_current.iloc[196]<rsi_current.iloc[198])and(rsi_current.iloc[196]>rsi_current.iloc[197])and(rsi_current.iloc[197]<rsi_current.iloc[198]) and 
        rsi="매수"
    else:
        rsi="보류"
    return rsi
    
def CCI (df):
    global cci 
    df['pt']=(df['high'] + df['low'] + df['close']) /3 
    df['sma']=df['pt'].rolling(20).mean() 
    df['mad']=df['pt'].rolling(20).apply(lambda x: pd.Series(x).mad())
    df['CCI']=(df['pt'] - df['sma']) / (0.015 * df['mad']) 
    if(df['CCI'].iloc[199]<100):
        cci="매수"
    elif(df['CCI'].iloc[199]>100):
        cci="매도"
    else:
        cci="보류"
    return cci

def macd(df: pd.DataFrame, macd_short:int=12, macd_long:int=26, macd_signal:int=9):
    global result

    df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
    df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
    df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
    df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9
    df["Indicator"]=df["MACD"]-df["MACD_signal"]

    if ((df["Indicator"][198]>0) and (df["Indicator"][197]<0) and (df["MACD_signal"][197]<0)and (df["MACD"][197]<0)and (df["MACD"][196]<0)):
        result="매수"
    elif ((df["Indicator"][198]<0) and (df["Indicator"][197]>0) and (df["MACD_signal"][198]>0)and (df["MACD_signal"][197]>0)and (df["MACD_signal"][196]>0)):
        result="매도"
    else:
        result="보류"
    return result

def get_ma(df, n1, n2): #이평선 계산 n1(60 이평선)-n2(120 이평선)
    time2=df['close'].rolling(window=n2).mean()#120
    time1=df['close'].rolling(window=n1).mean()#60

    return time1

def get_ma2(df, n1, n2): #이평선 계산 n1(60 이평선)-n2(120 이평선)
    time2=df['close'].rolling(window=n2).mean()#120
    time1=df['close'].rolling(window=n1).mean()#60

    if(time1[198]-time2[198])>(time1[199]-time2[199]):
        return "매수"
    else:
        return "보류"
    
def stock_rsi(df: pd.DataFrame, p1, k1, d1):
        series = pd.Series(df['close'].values)

        period=p1
        smoothK=k1
        smoothD=d1

        delta = series.diff().dropna()
        ups = delta * 0
        downs = ups.copy()
        ups[delta > 0] = delta[delta > 0]
        downs[delta < 0] = -delta[delta < 0]
        ups[ups.index[period-1]] = np.mean( ups[:period] )
        ups = ups.drop(ups.index[:(period-1)])
        downs[downs.index[period-1]] = np.mean( downs[:period] )
        downs = downs.drop(downs.index[:(period-1)])
        rs = ups.ewm(com=period-1,min_periods=0,adjust=False,ignore_na=False).mean() / \
             downs.ewm(com=period-1,min_periods=0,adjust=False,ignore_na=False).mean() 
        rsi = 100 - 100 / (1 + rs)
        stochrsi  = (rsi - rsi.rolling(period).min()) / (rsi.rolling(period).max() - rsi.rolling(period).min())
        stochrsi_K = stochrsi.rolling(smoothK).mean()
        stochrsi_D = stochrsi_K.rolling(smoothD).mean()

        if(df['close'][198]>get_ma(df, 60, 120)[198]):
            if(stochrsi_K[197]<=0.2 and (stochrsi_K[197]<stochrsi_K[198]) and (stochrsi_K[196]>stochrsi_K[197])and get_ma2(df,60,120)!="매수"):
                return "매수"
            elif(stochrsi_K[198]>=0.8 and (stochrsi_K[198]>stochrsi_K[199]) and (stochrsi_K[197]<stochrsi_K[198])):
                return "매도"
            else:
                return "보류"
        elif(df['close'][198]<get_ma(df, 60, 120)[198]):
            if(stochrsi_K[197]<=0.1 and (stochrsi_K[197]<stochrsi_K[198]) and (stochrsi_K[196]>stochrsi_K[197]) and rsi<=30 and get_ma2(df,60,120)!="매수"):
                return "매수"
            elif(stochrsi_K[198]>=0.5 and (stochrsi_K[198]>stochrsi_K[199]) and (stochrsi_K[197]<stochrsi_K[198])):
                return "매도"
            else:
                return "보류"

def ADX(df: pd.DataFrame):
    high_prices = df['high']
    low_prices = df['low']
    close_prices = df['close']

    # ADX 값 계산
    adx = ta.trend.adx(high_prices, low_prices, close_prices, 14) #해당 코드들은 ta 라이브러리 참조
    adx_neg = ta.trend.adx_neg(high_prices, low_prices, close_prices, 14)
    adx_pos = ta.trend.adx_pos(high_prices, low_prices, close_prices, 14)
    if(adx[198]>21 and adx_pos[198]>adx_neg[198]):
         return "매수"
    else:
        return "보류"

def OBV(df: pd.DataFrame):
    Volume_prices = df['volume']
    close_prices = df['close']

    # ADX 값 계산
    obv = ta.volume.on_balance_volume(close_prices,Volume_prices)

def Haikin_Ashi(df: pd.DataFrame):
    df_ha=df.copy()[['open','high','low','close']]
    df_ha['close']=((df['open']+df['high']+df['low']+df['close'])/4)

    for i in range(len(df)):
        if i == 0:
            df_ha.iat[0,0]=((df['open'].iloc[0]+df['close'].iloc[0])/2)
        else:
            df_ha.iat[i,0]=((df_ha.iat[i-1,0]+df_ha.iat[i-1,3])/2)
    
    df_ha['high']=df_ha.loc[:,['open','close']].join(df['high']).max(axis=1)
    df_ha['low']=df_ha.loc[:,['open','close']].join(df['low']).max(axis=1)

    return df_ha

def AI(target, name, set_time):
    global few_minutes_later
    schedule.run_pending()
    df = pyupbit.get_ohlcv(target, interval="minute10")
    #Haikin_Ashi_result=Haikin_Ashi(df)

    #cci_current=CCI(df)
    #rsi_current = rsi(df, 14)
    #target_price = get_target_price(target)#이걸 변경하면 구매전략 변경됨, 변동성 돌파전략을 이용한 목표가 설정
    current_price = get_current_price(target)
    stock_rsi_result=stock_rsi(df,14,3,3)
    #macd_current = macd(df,12,26,9)
    #ADX_result=ADX(df)
    #OBV_result=OBV(df)
    # print(target,target_price,current_price,predicted_close_price[i],target_price < current_price and current_price < predicted_close_price[i])
    if (stock_rsi_result=="매수"): #get_ma = 이평선 120, 60의 계산값
        krw = get_balance("KRW")
        if krw > 5000:
            post_message(myToken,"#bitcoinauto-ai", "Coin buy : " +target+"  "+str(krw)+"  "+str(current_price))
            upbit.buy_market_order(target, krw*0.9995) #돌파하면 구매
            sell_key[0]=target
            sell_key[1]=current_price
            hour_ch, minute10=time_changer(now,20)
            few_minutes_later = now.replace(minute=minute10, hour=hour_ch)#30분 후-----------------------------------   
    elif (stock_rsi_result=="매도"):
        btc = get_balance(name)
        if btc > (5000/current_price):
            upbit.sell_market_order(target, btc*0.9995)
            krw = get_balance("KRW")
            post_message(myToken,"#bitcoinauto-ai", "Coin sell : " +target+"  "+str(krw)+"  "+str(current_price)+"  "+str(sell_key[1]))
            sell_key[0]=1.0
            sell_key[1]=1.0
            sell_key[2]=1.0
            print("")
    sleep(0.1) #너무 빠른 속도로 api에 연속으로 데이터를 요청하면 뻑난다. 적당히 텀을 둬가면서 요청하자

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now(KST)#서버의 위치가 다른 나라일 경우를 대비해 현재 대한민국 기준 시각 사용
        AI("KRW-BTC","BTC",now)
        AI("KRW-ETH","ETH",now)
        AI("KRW-BCH","BCH",now)
        AI("KRW-AAVE","AAVE",now)        
        AI("KRW-BSV","BSV",now)
        AI("KRW-ETC","ETC",now)
        AI("KRW-SOL","SOL",now)
        AI("KRW-AVAX","AVAX",now)
        AI("KRW-BTG","BTG",now)
        AI("KRW-STRK","STRK",now)
        AI("KRW-NEO","NEO",now)
        AI("KRW-ATOM","ATOM",now)
        AI("KRW-APT","APT",now)
        AI("KRW-AXS","AXS",now)
        AI("KRW-LINK","LINK",now)
        AI("KRW-DOT","DOT",now)
        AI("KRW-MASK","MASK",now)
        AI("KRW-GAS","GAS",now)
        AI("KRW-QTUM","QTUM",now)
        AI("KRW-SBD","SBD",now)
        AI("KRW-NEAR","NEAR",now)
        AI("KRW-TON","TON",now)
        AI("KRW-OMG","OMG",now)
        AI("KRW-MTL","MTL",now)
        AI("KRW-AQT","AQT",now)

        if(now.minute==0 and now.second<=5):#정시 마다 프로세스 확인
            post_message(T_Token,"#bitcoinauto-ai", "프로세스가 돌아가고 있습니다 ")

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        post_message(myToken,"#bitcoinauto-ai",traceback.format_exc())
        post_message(myToken,"#bitcoinauto-ai", e)
        time.sleep(1)