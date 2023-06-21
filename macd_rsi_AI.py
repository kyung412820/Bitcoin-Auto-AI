from re import S
import time
import pyupbit
import datetime
import pandas as pd
import schedule
from fbprophet import Prophet
from slacker import Slacker
import datetime as dt
import numpy as np
import requests
import traceback
import pytz
KST = pytz.timezone('Asia/Seoul')

access = "YttVn2BhLicTA5b02xrZc5ydbqYGjvpnhbP9wTdP"
secret = "LtpkDjfN9gNvEtgA6u3AIMqvx86bQ6rBSLzoqJlq"
myToken = "xoxb-3149418271687-3600159322736-3xQHb32Q0LrEf6Yam3Cr1mBb"
T_Token = "xoxb-3149418271687-3582406642517-c0ezQQDHR4kGHm4cYHYQ3EtG"
sell_key=["",1.0,1.0]

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=5) #현재시간 10분 단위 30분전 데이터의 고점 저점을 기준으로 계산            *
    k=get_ror(ticker)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k #현재 종가 + 과거 고점-저점*0.k배
    # print(df)
    return target_price

def get_ror(target):#최고의 수익률을 기대할 수 있는 최적의 변동값 계산
    max_ror=0
    max_k=0
    df = pyupbit.get_ohlcv(target,interval="minute10", count=5)#count = 최근 몇일  interval = 시간 단위           *
    for k in np.arange(0.1, 1.0, 0.1):
        df['range'] = (df['high'] - df['low']) * k
        df['target'] = df['open'] + df['range'].shift(1)
        fee = 0.005
        df['ror'] = np.where(df['high'] > df['target'],
                            df['close'] / df['target'] - fee,
                            1)

        ror = df['ror'].cumprod()[-2]
        if(ror>max_ror):
            max_ror=ror
            max_k=k
    return max_k

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
    
    df["vertex_buy"]=((df["MACD"].iloc[197]-df["MACD"].iloc[196])>(df["MACD"].iloc[198]-df["MACD"].iloc[197])) or((df["MACD"].iloc[196]>df["MACD"].iloc[197])and(df["MACD"].iloc[197]<df["MACD"].iloc[198]))
    df["vertex_sell"]=((df["MACD"].iloc[198]-df["MACD"].iloc[197])>(df["MACD"].iloc[199]-df["MACD"].iloc[198])) or((df["MACD"].iloc[197]<df["MACD"].iloc[198])and(df["MACD"].iloc[198]>df["MACD"].iloc[199]))
    #macd가 꼭짓점인지 확인--0++
    #df["convergence"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 수렴하고 있는지 확인
        #df["diffusion"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])<abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 확산하고 있는지 확인

    df["macd_down"]=(df["MACD_signal"].iloc[198]>df["MACD"].iloc[198])
    #1단위 전부터 현재까지 macd가 macd_signal보다 작은지
    df["macd_up"]=(df["MACD_signal"].iloc[198]<df["MACD"].iloc[198])
    #macd가 macd_signal보다 큰지
    #df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
    #df["buy"]=((df["MACD_signal"]-df["MACD"])/df["MACD_signal"])#살 지점 정하기 - 수렴 측정때 사용
    #df["sell"]=((df["MACD"]-df["MACD_signal"])/df["MACD"])#팔 지점 정하기 - 확장 측정때 사용
    df["MACD_sign"]=df.apply(lambda x: ("매수" if x["macd_down"] and x["vertex_buy"] else ("매도" if  x["macd_up"] and x["vertex_sell"] else "보류")), axis=1) # 구매여부 
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
    rsi=pd.Series(_gain/(_gain+_loss)*100, name="RSI")
    return rsi
                   
# 로그인
upbit = pyupbit.Upbit(access, secret)
print("macd_rsi autotrade start")
post_message(myToken,"#bitcoinauto-ai", "macd_rsi autotrade start")


def AI(target, name, set_time):
    df = pyupbit.get_ohlcv(target, interval="minute10")
    rsi_current = rsi(df, 14)
    macd_current = macd(df,12,26,9).iloc[-1]
    target_price = get_target_price(target)
    schedule.run_pending()
    if rsi_current.iloc[197]<=30 and((rsi_current.iloc[197]-rsi_current.iloc[198])<=(rsi_current.iloc[199]-rsi_current.iloc[198])):
        rsi_result="매수"
    elif (rsi_current.iloc[198]>=50): #(rsi_current.iloc[196]<rsi_current.iloc[197])and(rsi_current.iloc[197]>rsi_current.iloc[198])and 
        rsi_result="매도"
    else:
        rsi_result="보류"
    #target_price = get_target_price(target)#이걸 변경하면 구매전략 변경됨, 변동성 돌파전략을 이용한 목표가 설정
    current_price = get_current_price(target)
    #print(df,current_price)
    print(current_price>sell_key[1],current_price,sell_key[1], target==sell_key[0])
    print(macd_current=="매수" and rsi_result=="매수"and current_price>sell_key[1],macd_current,rsi_result, target, now)
    if target_price<current_price and rsi_current.iloc[199]<40:
        krw = get_balance("KRW")
        if krw > 5000:
            sell_key[0]=target
            sell_key[1]=df['close'].iloc[198]
            sell_key[2]=rsi_current.iloc[199]
            post_message(myToken,"#bitcoinauto-ai",  "BUY : "+target+"  "+str(krw*0.9995))
            buy_result = upbit.buy_market_order(target, krw*0.9995)#돌파하면 구매
    elif (rsi_current.iloc[199]>=(sell_key[2]+10) and target==sell_key[0]): #(sell_key[1]*0.98>current_price)
        btc = get_balance(name)#담날 오전 8시50분에 전량 매도
        if btc > (5000/current_price):#수정
            krw = get_balance("KRW")
            post_message(myToken,"#bitcoinauto-ai", "SELL : "+target+"  "+str(current_price)+"  "+str(krw))
            sell_result = upbit.sell_market_order(target, btc*0.9995)
            sell_key[0]=""
            sell_key[1]=1.0
            sell_key[2]=1.0
    time.sleep(1)

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        now = now.replace(tzinfo=KST)
        AI("KRW-BTC","BTC",now)
        AI("KRW-ETH","ETH",now)
        AI("KRW-BCH","BCH",now)
        AI("KRW-NEO","NEO",now)
        AI("KRW-AAVE","AAVE",now)
        AI("KRW-MTL","MTL",now)
        AI("KRW-ETC","ETC",now)
        AI("KRW-OMG","OMG",now)
        AI("KRW-XRP","WAVES",now)
        AI("KRW-STORJ","STORJ",now)
        AI("KRW-ADA","ADA",now)
        AI("KRW-BTG","BTG",now)
        AI("KRW-ICX","ICX",now)
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
        print(traceback.format_exc(),e)
        post_message(myToken,"#bitcoinauto-ai", e)
        time.sleep(1)