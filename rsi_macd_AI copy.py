from re import S
import time
import pyupbit
import datetime
import pandas as pd
import schedule
from fbprophet import Prophet
from slacker import Slacker
import datetime as dt
import requests
import pytz
KST = datetime.timezone(datetime.timedelta(hours=9))

access = "YttVn2BhLicTA5b02xrZc5ydbqYGjvpnhbP9wTdP"
secret = "LtpkDjfN9gNvEtgA6u3AIMqvx86bQ6rBSLzoqJlq"
myToken = "xoxb-3149418271687-3600159322736-3xQHb32Q0LrEf6Yam3Cr1mBb"
T_Token = "xoxb-3149418271687-3582406642517-c0ezQQDHR4kGHm4cYHYQ3EtG"
sell_key=["1",2,3]
def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

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
    #df["convergence"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])>abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])>abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
    #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 수렴하고 있는지 확인
        #df["diffusion"]=(abs(df["MACD"].iloc[197]-df["MACD_signal"].iloc[197])<abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198]))and(abs(df["MACD"].iloc[198]-df["MACD_signal"].iloc[198])<abs(df["MACD"].iloc[199]-df["MACD_signal"].iloc[199]))
        #20분전과 10분전 10분전과 현재를 비교해 macd가 점차 확산하고 있는지 확인

    df["macd_down"]=(df["MACD_signal"].iloc[198]>df["MACD"].iloc[198])and(df["MACD_signal"].iloc[199]>df["MACD"].iloc[199])
    #1단위 전부터 현재까지 macd가 macd_signal보다 작은지
    df["macd_up"]=(df["MACD_signal"].iloc[198]<df["MACD"].iloc[198])and(df["MACD_signal"].iloc[199]<df["MACD"].iloc[199])
    #macd가 macd_signal보다 큰지
    #df["MACD_oscillator"]=df.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
    #df["buy"]=((df["MACD_signal"]-df["MACD"])/df["MACD_signal"])#살 지점 정하기 - 수렴 측정때 사용
    #df["sell"]=((df["MACD"]-df["MACD_signal"])/df["MACD"])#팔 지점 정하기 - 확장 측정때 사용
    df["MACD_sign"]=df.apply(lambda x: ("매수" if x["macd_down"] else ("매도" if x["macd_up"] else "보류")), axis=1) # 구매여부 
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
print("autotrade start")
post_message(myToken,"#bitcoinauto-ai", "autotrade start test")


def AI(target, name, set_time):
    df = pyupbit.get_ohlcv(target, interval="minute10")
    rsi_current = rsi(df, 14)
    if ((rsi_current.iloc[196]>rsi_current.iloc[197])and(rsi_current.iloc[197]<rsi_current.iloc[198]) and rsi_current.iloc[197]<=35):
        rsi_result="매수"
    elif (rsi_current.iloc[196]<rsi_current.iloc[197])and(rsi_current.iloc[197]>rsi_current.iloc[198]):
        rsi_result="매도"
    else:
        rsi_result="보류"
    rsi_vertex = rsi_current
    macd_current = macd(df,12,26,9).iloc[-1]
    start_time = get_start_time(target) #코인은 장이 24시간이라 하루의 시작을 오전 9시로 적용
    end_time = start_time + datetime.timedelta(days=1) # 담날 9시까지
    schedule.run_pending()
    price = pyupbit.get_current_price(target)
    #print(rsi_current <=40 and macd_current=="매수",rsi_current,macd_current, target, now)
    if rsi_result=="매수" and macd_current=="매수":
        krw = get_balance("KRW")
        if krw > 5000:
            buy_result = upbit.buy_market_order(target, krw*0.9995)#돌파하면 구매
            post_message(myToken,"#bitcoinauto-ai", "BTC buy : " +str(buy_result))
            print(sell_key)
            sell_key[0]=target
            sell_key[1]=rsi_current.iloc[197]
            sell_key[2]=rsi_current.iloc[199]
            print(sell_key)
    elif (macd_current=="매도" and sell_key[0]==target and (rsi_current[-1]-sell_key[1]>=20)) or ((sell_key[2]-rsi_current.iloc[199])/sell_key[2]*100)>0.01:
        btc = get_balance(name)#담날 오전 8시50분에 전량 매도
        if btc > (5000/price):#수정
            sell_result = upbit.sell_market_order(target, btc*0.9995)
            post_message(myToken,"#bitcoinauto-ai", "BTC buy : " +str(sell_result))
            sell_key[0]=0
            sell_key[1]=0
            sell_key[2]=0
            print(sell_key)
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
        AI("KRW-LTC","LTC",now)
        AI("KRW-XRP","XRP",now)
        AI("KRW-ETC","ETC",now)
        AI("KRW-OMG","OMG",now)
        AI("KRW-SNT","SNT",now)
        AI("KRW-XRP","WAVES",now)
        AI("KRW-ETC","XEM",now)
        AI("KRW-OMG","QTUM",now)
        AI("KRW-LSK","LSK",now)

        AI("KRW-STEEM","STEEM",now)
        AI("KRW-XLM","XLM",now)
        AI("KRW-ARDR","ARDR",now)
        AI("KRW-ARK","ARK",now)
        AI("KRW-STORJ","STORJ",now)
        AI("KRW-GRS","GRS",now)
        AI("KRW-REP","REP",now)
        AI("KRW-ADA","ADA",now)
        AI("KRW-SBD","SBD",now)
        AI("KRW-POWR","POWR",now)
        AI("KRW-BTG","BTG",now)
        AI("KRW-ICX","ICX",now)
        AI("KRW-EOS","EOS",now)
        AI("KRW-TRX","TRX",now)
        AI("KRW-SC","SC",now)

        AI("KRW-ONT","ONT",now)
        AI("KRW-ZIL","ZIL",now)
        AI("KRW-POLY","POLY",now)
        AI("KRW-ZRX","ZRX",now)
        AI("KRW-LOOM","LOOM",now)
        AI("KRW-BCH","BCH",now)
        AI("KRW-BAT","BAT",now)
        AI("KRW-IOST","IOST",now)
        AI("KRW-RFR","RFR",now)
        AI("KRW-CVC","CVC",now)
        AI("KRW-IQ","IQ",now)
        AI("KRW-IOTA","IOTA",now)
        AI("KRW-MFT","MFT",now)
        AI("KRW-ONG","ONG",now)
        AI("KRW-GAS","GAS",now)

        AI("KRW-UPP","UPP",now)
        AI("KRW-ELF","ELF",now)
        AI("KRW-KNC","KNC",now)
        AI("KRW-BSV","BSV",now)
        AI("KRW-THETA","THETA",now)
        AI("KRW-QKC","QKC",now)
        AI("KRW-BTT","BTT",now)
        AI("KRW-MOC","MOC",now)
        AI("KRW-ENJ","ENJ",now)
        AI("KRW-TFUEL","TFUEL",now)
        AI("KRW-MANA","MANA",now)
        AI("KRW-ANKR","ANKR",now)
        AI("KRW-AERGO","AERGO",now)
        AI("KRW-ATOM","ATOM",now)
        AI("KRW-TT","TT",now) 

        AI("KRW-CRE","CRE",now)
        AI("KRW-MBL","MBL",now)
        AI("KRW-WAXP","WAXP",now)
        AI("KRW-HBAR","HBAR",now)
        AI("KRW-MED","MED",now)
        AI("KRW-MLK","MLK",now)
        AI("KRW-STPT","STPT",now)
        AI("KRW-ORBS","ORBS",now)
        AI("KRW-VET","VET",now)
        AI("KRW-CHZ","CHZ",now)
        AI("KRW-STMX","STMX",now)
        AI("KRW-DKA","DKA",now)
        AI("KRW-HIVE","HIVE",now)
        AI("KRW-KAVA","KAVA",now)
        AI("KRW-AHT","AHT",now)

        AI("KRW-LINK","LINK",now)
        AI("KRW-XTZ","XTZ",now)
        AI("KRW-BORA","BORA",now)
        AI("KRW-JST","JST",now)
        AI("KRW-CRO","CRO",now)
        AI("KRW-TON","TON",now)
        AI("KRW-SXP","SXP",now)
        AI("KRW-HUNT","HUNT",now)
        AI("KRW-PLA","PLA",now)
        AI("KRW-DOT","DOT",now)
        AI("KRW-SRM","SRM",now)
        AI("KRW-MVL","MVL",now)
        AI("KRW-STRAX","STRAX",now)
        AI("KRW-AQT","AQT",now)
        if(now.minute==0 and now.second<=5):#정시 마다 프로세스 확인
            post_message(T_Token,"#bitcoinauto-ai", "프로세스가 돌아가고 있습니다 ")

    except Exception as e:
        print(e)
        post_message(myToken,"#bitcoinauto-ai", e)
        time.sleep(1)