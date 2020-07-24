from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import numpy as np
import pandas as pd

import requests
import json
from datetime import datetime, timedelta
import pytz

# Shopify API Version
API_VERSION = '2020-04'

# Shopify Store Credentials
# You may want to store these as environment variables to avoid compromising
# your API keys if you fork then commit to your own repository
API_KEY = # Your API Key as a string
API_TOKEN = # API token as a string
SHOP_ORDERS_URL = f'https://storename.myshopify.com/admin/api/{API_VERSION}/orders.json' #modify your storename to match

## Google Sheet ID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Google Sheet ID
SPREADSHEET_ID = # SpreaksheetID as a string
SPREADSHEET_RANGE = # Sheet name as a string

## Using PYTZ to set the "start-date"
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
PST = pytz.timezone('America/Vancouver') #modify your datetime timezone as needed
yesterday = datetime.now() - timedelta(1)
local_time = PST.localize(yesterday)
yesterday_timestamp = local_time.strftime(TIME_FORMAT)


## Modify the fields based on Shopify's Order API and your needs

limit = '250'
fields = 'id, \
          customer, \
          currency, \
          created_at, \
          processed_at, \
          total_line_items_price, \
          total_discounts, sub_total_price, \
          total_tax, \
          total_price, \
          shipping_lines, \
          refunds, \
          line_items'
REQUEST_PARAMATERS = {'limit':limit, \
                        'processed_at_min': '2020-06-09T00:00:00-7:00', \
                        'processed_at_max': '2020-06-10T00:00:00-7:00', \
                        'status':'any', \
                        'fields': fields}

### Functions Here

def get_order_data(parameters):
    # Function Returns JSON API Object with order data
    all_orders = []
    request_url = SHOP_ORDERS_URL
    next_page_exists = True
    page = 1
    while next_page_exists:
        response = requests.get(request_url, auth=(API_KEY,API_TOKEN), params=parameters)
        orders = json.loads(response.text)
        all_orders += orders['orders']
        next_page_exists = ('next' in response.links)
        print(f'Reading Page {page}', end = '\r')
        if next_page_exists:
            request_url = response.links['next']['url']
            parameters = {'limit':'250'}
            page += 1
        else:
            break

    return all_orders

def authorizer():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def check_sheet_status(credentials):
    # Call the Sheets API
    service = build('sheets', 'v4', credentials=credentials)
    #instantiate the sheet
    sheet = service.spreadsheets()
    #read the results
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SPREADSHEET_RANGE).execute()
    update = result.get('values',[])

    if update:
        status = True
    else:
        status = False
    return status

def write_data(credentials, sheet_status, keys, values):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    VALUE_INPUT_OPTION = 'USER_ENTERED'

    body = {
        'values': values
    }


    if sheet_status == False:
        body_header = {
            'values': [keys]
        }
        write_header = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                                    range=SPREADSHEET_RANGE,
                                    valueInputOption=VALUE_INPUT_OPTION,
                                    body=body_header).execute()
        write_body = sheet.values().append(spreadsheetId=SPREADSHEET_ID,
                                    range=SPREADSHEET_RANGE,
                                    valueInputOption=VALUE_INPUT_OPTION,
                                    body=body).execute()
    else:
        write = sheet.values().append(spreadsheetId=SPREADSHEET_ID,
                                    range=SPREADSHEET_RANGE,
                                    valueInputOption=VALUE_INPUT_OPTION,
                                    body=body).execute()


    #read the results
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SPREADSHEET_RANGE).execute()
    update = result.get('values',[])

    # now to check if the update worked
    if not update:
        print('No data found.')
    else:
        print('GSheet Updated')



orderdata = get_order_data(REQUEST_PARAMATERS)

### Use Pandas to perform your desired data transformations e.g. Apply-Split-Combines here
### Data cleaning/manipulation will be performed in memory

orderdatadf = pd.DataFrame(orderdata)
num_orders = len(orderdatadf)
orderdatadf['total_price'] = orderdatadf['total_price'].astype(float)
orderdatadf['total_tax'] = orderdatadf['total_tax'].astype(float)
orderdatadf['total_discounts'] = orderdatadf['total_discounts'].astype(float)
orderdatadf['total_line_items_price'] = orderdatadf['total_line_items_price'].astype(float)
refund = []
for i in orderdatadf['refunds']:
    if len(i)==0:
        refund.append(0)
    if len(i)==1:
        if len(i[0]['transactions'])==1:
            refund.append(i[0]['transactions'][0].get('receipt').get('amount'))
        else:
            refund.append(0)
orderdatadf['refund'] = refund
orderdatadf['refund'] = orderdatadf['refund']/100
orderdatadf['date'] = pd.to_datetime(orderdatadf['processed_at'], utc = True).dt.date
orderdatadf['customer_type'] = [orderdatadf['customer'][i]['orders_count']==1 for i in range(len(orderdatadf))]
orderdatadf['customer_type'] = np.where(orderdatadf['customer_type']==True, 'First-Time','Returning')
orderdatadf['units_sold'] = [len(orderdatadf['line_items'][i]) for i in range(num_orders)]
orderdatadf['shipping'] = [orderdatadf['shipping_lines'][i][0]['price'] if orderdatadf['shipping_lines'][i] else '0.00' for i in range(num_orders)]
orderdatadf['shipping'] = orderdatadf['shipping'].astype(float)
orderdatadf.drop(['id','customer','created_at','processed_at','line_items','shipping_lines'], axis=1, inplace=True)
orderdatadf = orderdatadf.groupby(['date','customer_type']).sum().reset_index()
orderdatadf['date'] = orderdatadf['date'].astype(str)
orderdatadf = orderdatadf.fillna(0)
orderdatadf.to_csv('test.csv')
print(orderdatadf)

# Prep data to be written to Gsheet
keys = orderdatadf.columns.tolist()
values = orderdatadf.values.tolist()

credentials = authorizer()

sheet_status = check_sheet_status(credentials)

write_data(credentials, sheet_status, keys, values)
