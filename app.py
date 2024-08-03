import os
from SmartApi import SmartConnect
import requests
import json
from pyotp import TOTP
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import datetime
import pandas as pd
import time

# Load environment variables from .env file
load_dotenv()

def setup_angel_one_connection():
    try:
        key_path = "/Users/sudhanshugautam/Desktop/stock_info_query_app/key.txt"
        with open(key_path, "r") as file:
            key_secret = file.read().split()

        api_key = key_secret[0]
        client_code = key_secret[2]
        password = key_secret[3]
        totp_key = key_secret[4]

        smart_connect = SmartConnect(api_key=api_key)
        totp = TOTP(totp_key).now()
        data = smart_connect.generateSession(client_code, password, totp)
        
        if data['status']:
            print("Login successful")
            return smart_connect
        else:
            print("Login failed")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def fetch_instrument_list():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    response = requests.get(url)
    return json.loads(response.text)

def token_lookup(ticker, instrument_list, exchange="BSE"):
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange and instrument["symbol"].split('-')[-1] == "EQ":
            return instrument["token"]
    return None

def hist_data_extended(smart_connect, ticker, duration, interval, instrument_list, exchange="BSE"):
    st_date = datetime.date.today() - datetime.timedelta(duration)
    end_date = datetime.date.today()
    st_date = datetime.datetime(st_date.year, st_date.month, st_date.day, 9, 15)
    end_date = datetime.datetime(end_date.year, end_date.month, end_date.day)
    df_data = pd.DataFrame(columns=["date","open","high","low","close","volume"])
    
    while st_date < end_date:
        time.sleep(0.4)  # avoiding throttling rate limit
        params = {
            "exchange": exchange,
            "symboltoken": token_lookup(ticker, instrument_list, exchange),
            "interval": interval,
            "fromdate": st_date.strftime('%Y-%m-%d %H:%M'),
            "todate": end_date.strftime('%Y-%m-%d %H:%M') 
        }
        hist_data = smart_connect.getCandleData(params)
        if hist_data['status'] and 'data' in hist_data:
            temp = pd.DataFrame(hist_data["data"],
                                columns = ["date","open","high","low","close","volume"])
            df_data = pd.concat([temp, df_data], ignore_index=True)
            end_date = datetime.datetime.strptime(temp['date'].iloc[0][:16], "%Y-%m-%dT%H:%M")
            if len(temp) <= 1:  # this takes care of the edge case where start date and end date become same
                break
        else:
            print(f"Failed to fetch data: {hist_data.get('message', 'Unknown error')}")
            break

    df_data.set_index("date", inplace=True)
    df_data.index = pd.to_datetime(df_data.index)
    df_data.index = df_data.index.tz_localize(None)
    df_data.drop_duplicates(keep="first", inplace=True)    
    return df_data

def get_stock_info(smart_connect, instrument_list, ticker, exchange="NSE"):
    try:
        token = token_lookup(ticker, instrument_list, exchange)
        if token is None:
            print(f"Could not find token for {ticker} ({exchange})")
            return None
        
        # Fetch current data
        current_data = smart_connect.ltpData(exchange, ticker, token)
        
        # Fetch historical data (1 week)
        historical_data = hist_data_extended(smart_connect, ticker, 7, "ONE_DAY", instrument_list, exchange)
        
        return {
            "current": current_data["data"],
            "historical": historical_data
        }
    except Exception as e:
        print(f"Could not fetch data for {ticker} ({exchange}). Error: {e}")
        return None

def calculate_growth(stock_info):
    if stock_info is None or stock_info["historical"].empty:
        return None
    
    oldest_price = stock_info["historical"]["close"].iloc[-1]
    current_price = stock_info["current"]["ltp"]
    growth = ((current_price - oldest_price) / oldest_price) * 100
    return round(growth, 2)

def interpret_query(query):
    llm = ChatOpenAI(
        model_name="gpt-4o-mini", 
        temperature=0.7,
        openai_api_base=os.getenv("OPENAI_API_BASE")
    )
    prompt = ChatPromptTemplate.from_template(
        "Interpret the following stock market query and extract the stock symbol and the information requested:\n\nQuery: {query}\n\nStock Symbol: \nRequested Information:"
    )
    chain = prompt | llm
    response = chain.invoke({"query": query})
    return response.content

def main():
    print("Stock Info Query App")
    
    smart_connect = setup_angel_one_connection()
    
    if smart_connect:
        print("Connected to AngelOne API")
        
        instrument_list = fetch_instrument_list()
        print("Fetched instrument list")
        
        while True:
            query = input("Enter your stock query (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
            
            interpretation = interpret_query(query)
            print("Query Interpretation:")
            print(interpretation)
            
            stock_symbol = interpretation.split("Stock Symbol:")[1].split("\n")[0].strip()
            
            if stock_symbol:
                stock_info = get_stock_info(smart_connect, instrument_list, stock_symbol, "NSE")
                if stock_info:
                    print(f"Last Traded Price for {stock_symbol}: {stock_info['current']['ltp']}")
                    growth = calculate_growth(stock_info)
                    if growth is not None:
                        print(f"Growth in the past week: {growth}%")
                    else:
                        print("Couldn't calculate growth due to insufficient data")
                    
                    # Print additional historical data
                    print("\nHistorical Data (Last 7 days):")
                    print(stock_info['historical'].tail())
                else:
                    print(f"Failed to fetch data for {stock_symbol}")
            else:
                print("Could not determine the stock symbol from the query.")
            
            print("\n")

    else:
        print("Failed to connect to AngelOne API")

if __name__ == "__main__":
    main()