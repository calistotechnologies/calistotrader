from tradingview_ta import TA_Handler, Interval, Exchange
import datetime
import time
from pprint import pprint
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule

def liveUpdate():
    btcusd = TA_Handler(
    symbol="BTCUSD",
    screener="crypto",
    exchange="BINANCEUS",
    interval=Interval.INTERVAL_1_MINUTE,
    timeout=None
)

    timestamp = datetime.datetime.now()
    btcusdOpen = btcusd.get_analysis().indicators['open']
    btcusdClose = btcusd.get_analysis().indicators['close']
    symbol = 'BTCUSD'
    volume = btcusd.get_analysis().indicators['volume']
    emaTwenty = btcusd.get_analysis().indicators['EMA20']

    print(f'Time: {timestamp} | New Data Uploaded to Database')

    #Authorize the API
    scope = ['https://spreadsheets.google.com/feeds', 
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file', 
        'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name("INSERT JSON FILE HERE", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Live Data Python").sheet1

    # Update Info from Live Data to G-sheet
    # sheet.update('A5', f'{timestamp}')
    # sheet.update('B5', f'{symbol}')
    # sheet.update('C5', f'{btcusdOpen}')
    # sheet.update('D5', f'{btcusdClose}')

    sheet.insert_row(values=(f'{timestamp}', f'{symbol}', f'{btcusdOpen}', f'{btcusdClose}', f'{volume}', f'{emaTwenty}'), index=1)

schedule.every(1).minute.do(liveUpdate)

while True:
    try:
        schedule.run_pending()
    except:
        print('++++++MAYBE AN INTERNET PROB OR SOMETHING++++++++++++')
        time.sleep(30)
