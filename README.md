<br>


# [HANSUNG STOCK] 딥러닝을 이용한 주가 예측 및 주식 매매 자동화 웹 서비스

<br>

<h2>목차</h2>

 - [소개](#소개) 
 - [팀원](#팀원) 
 - [개발 환경](#개발-환경)
 - [사용 기술](#사용-기술)
 - [핵심 기능](#핵심-기능)
    - [Training](#Training)
   - [Auto-buy-sell](#Auto-buy-sell)
   - [Messeging](#Messeging)
 - [Trouble Shooting](#trouble-shooting)


## 소개

**Time Series Analysis**는 Upbit API, Facebook Prophet, python을 이용한 시계열 분석, 보조 지표를 사용해 변동되는 코인의 가격을 예측해 자동으로 매수하는 프로그램이며 완전한 자동화를 위해 Google Cloude에서 코드를 실행하였습니다. <br>

## 팀원

<table>
   <tr>
    <td align="center"><b><a href="https://github.com/kyung412820">이경훈</a></b></td>
  <tr>
    <td align="center"><a href="https://github.com/kyung412820"><img src="https://avatars.githubusercontent.com/u/71320521?v=4" width="100px" /></a></td>
  </tr>
  <tr>
    <td align="center"><b>프로젝트 총괄</b></td>
</table>


## 개발 환경

 - Windows
 - Visual Code
 - GitHub



## 사용 기술 

- Library & Framework : pyupbit, pands, slacker, Facebook Prophet 
- Language : Python





## 핵심 기능

### Training

- 업비트, 바이낸스의 API를 이용, Facebook의 Facebook Prophet을 이용한 시계열 분석을 진행하였습니다. 
  - 변동성 돌파 전략을 통한 매수전략을 사용했습니다.
- 추가적으로 MACD,OBV,ADX,RSI등의 다양한 보조지표를 구현하여 추가적인 판단에 이용했습니다
  - 구현된 보조지표는 MACD,OBV,ADX,RSI,CCI,STOCK_RSI,HAIKIN_ASHI,MA입니다.


### Auto-buy-sell

- 위의 데이터를 기준으로 각 판단기준에 맞을 경우 자동을 매수,매도를 진행합니다.
  - pyupbit.get_ohlcv를 이용해 데이터를 추출, 판단 후 market_dorder를 사용해 매수, 매도를 구현했습니다.

### Messeging

- AI 봇 메신저 slacker를 이용하여 매수, 매도 상황, 오류 발생시 알림을 구현했습니다.
  - slacker의 post_message를 사용해 구현했습니다.


## Trouble Shooting

- 데이터를 처리하는 과정 중 미국의 시간으로 적용되는 시계열 분석을 한국을 기준으로 바꾸었습니다.
  - datetime.datetime.now(KST)를 사용해 조정하였습니다.

- 시계열 분석만으로는 정확한 매수 시점을 파악하기 힘들어 보조 지표를 활용했습니다.
  - 사용한 지표는 ADX,MACD,이동평균선입니다.



