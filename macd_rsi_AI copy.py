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
    if ((rsi_current.iloc[199] >rsi_current.iloc[195])): #(rsi_current.iloc[196]<rsi_current.iloc[198])and(rsi_current.iloc[196]>rsi_current.iloc[197])and(rsi_current.iloc[197]<rsi_current.iloc[198]) and 
        rsi="매수"
    elif (rsi_current.iloc[196]<rsi_current.iloc[197])and(rsi_current.iloc[197]>rsi_current.iloc[198]):
        rsi="매도"
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
    df["MACD_12"]=df["close"].ewm(span=macd_short, adjust=False).mean()
    df["MACD_26"]=df["close"].ewm(span=macd_long, adjust=False).mean()
    df["MACD"]=df["MACD_12"]-df["MACD_26"] #12, 26
    df["MACD_signal"]=df["MACD"].ewm(span=macd_signal, adjust=False).mean()  # 9
    df["Indicator"]=df["MACD"]-df["MACD_signal"]
    macd_cross_buy_price5=0
    macd_cross_buy_price3=0
    macd_cross_buy_price1=0
    macd_up_buy_price=[]
    sell_price=[100000000000]

    # for a in range(169,200):
    #     macd_cross_buy_price5+=float(df["MACD_signal"].iloc[a]-df["MACD_signal"].iloc[a-1])
    # for b in range(181,200):
    #     macd_cross_buy_price3+=float(df["MACD_signal"].iloc[b]-df["MACD_signal"].iloc[b-1])
    for c in range(193,200):
        macd_cross_buy_price1+=float(df["MACD_signal"].iloc[c]-df["MACD_signal"].iloc[c-1])
 
        #df["vertex_Gap_20"]=(abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196])<abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197]))and(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #30분전~현재를 비교해 macd가 꼭짓점인지 확인--0+
        #df["vertex_Gap_10"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #20분전~현재를 비교해 macd가 꼭짓점인지 확인-0+
        #df["vertex_Gap"]=(abs(df["MACD"].iloc[195]-df["MACD_signal"].iloc[195])<abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196]))and(abs(df["MACD"].iloc[196]-df["MACD_signal"].iloc[196])<abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197]))and(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
    
    #df["vertex_buy"]=(df["MACD"].iloc[196]>df["MACD"].iloc[197])and(df["MACD"].iloc[197]<df["MACD"].iloc[198])
    #df["vertex_sell"]=(df["MACD"].iloc[196]<df["MACD"].iloc[197])and(df["MACD"].iloc[197]>df["MACD"].iloc[198])
    #macd가 꼭짓점인지 확인--0++
    df["diffusion"]=(df["Indicator"].iloc[198]>df["Indicator"].iloc[197])
    df["convergence"]=(df["Indicator"].iloc[199]<df["Indicator"].iloc[198])and(df["Indicator"].iloc[198]<df["Indicator"].iloc[197])
    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 수렴하고 있는지 확인
    #df["diffusion"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])<abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 확산하고 있는지 확인
    #df["macd_down"]=(df["Indicator"].iloc[199]<df["Indicator"].iloc[198])and df["Indicator"].iloc[199]>0 and df["Indicator"].iloc[198]>0
    df["macd_down"]=df["Indicator"].iloc[198]>df["Indicator"].iloc[199]
    df["macd_sell"]=df["Indicator"].iloc[199]<0
    #1단위 전부터 현재까지 macd가 macd_signal보다 작은지
    df["macd_cross"]=df["Indicator"].iloc[198]>0 and df["Indicator"].iloc[197]<0 and df["MACD_signal"].iloc[199]>df["MACD_signal"].iloc[198] 
    # df["macd_up1"]=(df["Indicator"].iloc[195]<df["Indicator"].iloc[196])and(df["Indicator"].iloc[196]>df["Indicator"].iloc[197])and(df["Indicator"].iloc[197]<df["Indicator"].iloc[198])and df["Indicator"].iloc[198]>0 and df["Indicator"].iloc[199]>0
    # df["macd_up2"]=(df["Indicator"].iloc[194]<df["Indicator"].iloc[195])and(df["Indicator"].iloc[195]>df["Indicator"].iloc[196])and(df["Indicator"].iloc[196]>df["Indicator"].iloc[197])and(df["Indicator"].iloc[197]<df["Indicator"].iloc[198])and df["Indicator"].iloc[198]>0 and df["Indicator"].iloc[199]>0
    # df["macd_up3"]=(df["Indicator"].iloc[193]<df["Indicator"].iloc[194])and(df["Indicator"].iloc[194]>df["Indicator"].iloc[195])and(df["Indicator"].iloc[195]>df["Indicator"].iloc[196])and(df["Indicator"].iloc[196]>df["Indicator"].iloc[197])and(df["Indicator"].iloc[197]<df["Indicator"].iloc[198])and df["Indicator"].iloc[198]>0 and df["Indicator"].iloc[199]>0
    # # #macd가 macd_signal보다 큰지
    #df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
    #df["buy"]=((df["MACD_signal"]-df["MACD"])/df["MACD_signal"])#살 지점 정하기 - 수렴 측정때 사용+
    #df["sell"]=((df["MACD"]-df["MACD_signal"])/df["MACD"])#팔 지점 정하기 - 확장 측정때 사용
    df["MACD_sign"]=df.apply(lambda x: ("매수" if x["macd_cross"] else ("총매도" if x["macd_sell"] else ("매도" if x["macd_down"] else "보류"))), axis=1) # 구매여부 
    return df["MACD_sign"]

def get_ma(df, n1, n2): #이평선 계산 n1(60 이평선)-n2(120 이평선)
    time2=df['close'].rolling(window=n2).mean()
    time1=df['close'].rolling(window=n1).mean()
    if ((time1[199]-time2[199])>(time1[196]-time2[196]))and(time1[196]-time2[196]>0)and(time1[199]-time2[199]>0): #60이평선 - 120이평선의 값이 계속 증가하고 이평선60이 120보다 높을 경우라면
        return "up"
    else:
        return "down"
    
def stock_rsi(symbol, p1, k1, d1):
        data=pyupbit.get_ohlcv(symbol, interval="minute10", count=100)
        
        df = pd.DataFrame(data)
    
        
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

        if(stochrsi_K[197]<=30 and (stochrsi_K[197]-stochrsi_D[197])<0 and (stochrsi_K[198]-stochrsi_D[198])>0):
            return "매수"
        elif(stochrsi_K[197]>=70 and (stochrsi_K[197]-stochrsi_D[197])>0 and (stochrsi_K[198]-stochrsi_D[198])<0):
            return "매도"
        else:
            return "noting"

def AI(target, name, set_time):
    global few_minutes_later
    schedule.run_pending()
    df = pyupbit.get_ohlcv(target, interval="minute10")
    #cci_current=CCI(df)
    rsi_current = rsi(df, 14)
    price = pyupbit.get_current_price(target)
    target_price = get_target_price(target)#이걸 변경하면 구매전략 변경됨, 변동성 돌파전략을 이용한 목표가 설정
    current_price = get_current_price(target)
    macd_current = macd(df,12,26,9).iloc[-1]
    stock_rsi=stock_rsi(name,14,3,3)
    # print(target,target_price,current_price,predicted_close_price[i],target_price < current_price and current_price < predicted_close_price[i])
    if (macd_current=="매수"and target_price=="매수" and get_ma(df, 60, 120)=="up"):
        krw = get_balance("KRW")
        if krw > 5000:
            post_message(myToken,"#bitcoinauto-ai", "Coin buy : " +target+"  "+str(krw)+"  "+str(current_price))
            buy_result = upbit.buy_market_order(target, krw*0.9995)#돌파하면 구매
            sell_key[0]=target
            sell_key[1]=current_price
            sell_key[2]=rsi_current
            hour_ch, minute10=time_changer(now,20)
            few_minutes_later = now.replace(minute=minute10, hour=hour_ch)#30분 후-----------------------------------   
    elif ((macd_current=="매도" and current_price>sell_key[1]) or macd_current=="총매도"):
        print(get_balance(name))
        btc = get_balance(name)
        print(btc)
        if btc > (5000/price):
            sell_result = upbit.sell_market_order(target)
            krw = get_balance("KRW")
            post_message(myToken,"#bitcoinauto-ai", "Coin sell : " +target+"  "+str(krw)+"  "+str(current_price)+"  "+str(sell_key[1]))
            sell_key[0]=1.0
            sell_key[1]=1.0
            sell_key[2]=1.0
            print("")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now(KST)#서버의 위치가 다른 나라일 경우를 대비해 현재 대한민국 기준 시각 사용
        AI("KRW-BTC","BTC",now)
        AI("KRW-ETH","ETH",now)
        AI("KRW-BCH","BCH",now)
        AI("KRW-NEO","NEO",now)
        AI("KRW-AAVE","AAVE",now)
        AI("KRW-ETC","ETC",now)
        AI("KRW-OMG","OMG",now)
        AI("KRW-WAVES","WAVES",now)
        AI("KRW-STORJ","STORJ",now)
        AI("KRW-ADA","ADA",now)
        AI("KRW-BTG","BTG",now)
        AI("KRW-SC","SC",now)
        AI("KRW-ONT","ONT",now)
        AI("KRW-BCH","BCH",now)
        AI("KRW-BAT","BAT",now)
        AI("KRW-IQ","IQ",now)
        AI("KRW-THETA","THETA",now)
        AI("KRW-ATOM","ATOM",now)
        AI("KRW-KAVA","KAVA",now)
        AI("KRW-LINK","LINK",now)
        AI("KRW-AXS","AXS",now)
        AI("KRW-ALGO","ALGO",now)
        AI("KRW-AVAX","AVAX",now)
        
        if(now.minute==0 and now.second<=5):#정시 마다 프로세스 확인
            post_message(T_Token,"#bitcoinauto-ai", "프로세스가 돌아가고 있습니다 ")

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        post_message(myToken,"#bitcoinauto-ai",traceback.format_exc())
        post_message(myToken,"#bitcoinauto-ai", e)
        time.sleep(1)