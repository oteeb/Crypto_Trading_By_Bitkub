import hashlib
import hmac
import json
import requests
import pandas as pd
import ccxt
import requests

while True:
    # API info
    API_HOST = 'https://api.bitkub.com'
    API_KEY = 'API_KEY'
    API_SECRET = b'API_SECRET'
    #line
    url = 'https://notify-api.line.me/api/notify'
    token = 'token line'
    headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token}
    

    def json_encode(data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)

    def sign(data):
        j = json_encode(data)
        print('Signing payload: ' + j)
        h = hmac.new(API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
        return h.hexdigest()

    # check server time
    response = requests.get(API_HOST + '/api/servertime')
    ts = int(response.text)
    print('Server time: ' + response.text)

    # check balances
    header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-BTK-APIKEY': API_KEY,
    }
    data = {
        'ts': ts,
    }
    signature = sign(data)
    data['sig'] = signature

    #print('Payload with signature: ' + json_encode(data))
    
    responsebalances = requests.post(API_HOST + '/api/market/balances', headers=header, data=json_encode(data))
    responseticker = requests.get(API_HOST + '/api/market/ticker') 

    #จำนวนเหรียญที่ถืออยู่
    balances_dict = json.loads(responsebalances.text)
    #print(type(balances_dict))
    bl_ETH = balances_dict['result']['ETH']['available']
    bl_THB = balances_dict['result']['THB']['available']
    print('balances_ETH = ',bl_ETH)
    print('balances_THB = ',bl_THB)

    #price
    ticker_dict = json.loads(responseticker.text)
    #print(type(ticker_dict))
    #print(ticker_dict['THB_ETH'])
    tk=ticker_dict['THB_ETH']
    average_price =  (tk['highestBid'] + tk['lowestAsk']) / 2
    #print("Average_price = " ,average_price)

    # มูลค่า ของ Asset
    Asset_01_Value = bl_ETH * average_price
    Asset_02_Value = bl_THB * 1
    print("มูลค่า ของ THB_ETH =",Asset_01_Value)

    # เปรัียบเทียบ และ ตัดสินใจเทรด
    # Rebalance_mark = ((1943           + 1937)            / 2) = 1939
    Rebalance_mark   = ((Asset_01_Value + Asset_02_Value) / 2)
    Rebalance_percent = 1
    print("มูลค่าทั้งหมด THB+ETH /2 =",Rebalance_mark)
    print("จำนวนที่ต้องชื้อขาย =",Asset_01_Value - Rebalance_mark)

    #    Asset_01_Value > (1939           + (1939          *   1             /1939) ) :      
    if   Asset_01_Value > (Rebalance_mark + (Rebalance_mark*Rebalance_percent/100) ) :
        print("ราคาส่วนต่าง = ",Asset_01_Value ,">", (Rebalance_mark + (Rebalance_mark*Rebalance_percent/100) ))
        print("SELL")
        diff_sell  = (Asset_01_Value - Rebalance_mark)/average_price
        print(diff_sell)
        def sell ():
            data_sell = {
            'sym': 'THB_ETH',# เหรียญที่จะขาย
            'amt': diff_sell, # จำนวนเหรียญที่จะขาย
            'rat': 0,# ราคาที่จะขาย
            'typ': 'market',
            'ts': ts,
            }
            signature = sign(data_sell)
            data_sell['sig'] = signature
            response = requests.post(API_HOST + '/api/market/place-ask', headers=header, data=json_encode(data_sell))
            #print(response.text)
        sell()
        msg = ('ทำการขาย ETH จำนวน = ',diff_sell)
        r = requests.post(url, headers=headers, data = {'message':msg})
        print (r.text)


    elif Asset_01_Value < (Rebalance_mark - (Rebalance_mark*Rebalance_percent/100) ) :
        print("ราคาส่วนต่าง = ",Asset_01_Value ,"<", (Rebalance_mark - (Rebalance_mark*Rebalance_percent/100) ))
        print("Buy")
        diff_buy  = Rebalance_mark - Asset_01_Value
        print(diff_buy)
        def buy ():
            data_buy = {
            'sym': 'THB_ETH',# เหรียญที่จะชื้อ
            'amt': diff_buy, # จำนวนเงินที่จะชื้อ
            'rat': 0,# ราคาที่จะชื้อ
            'typ': 'market',# ประเภทการชื้อขาย
            'ts': ts,
            }
            signature = sign(data_buy)
            data_buy['sig'] = signature
            response = requests.post(API_HOST + '/api/market/place-bid', headers=header, data=json_encode(data_buy))
            #print(response.text)
        buy()
        msg = ('ทำการชื้อ ETH จำนวน = ',diff_buy)
        r = requests.post(url, headers=headers, data = {'message':msg})
        print (r.text)

    else :
        print("None Trade")


    import time
    sleep = 30
    print("Sleep",sleep,"sec.")
    time.sleep(sleep) # Delay for 1 minute (60 seconds).  