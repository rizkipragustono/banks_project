import requests
from bs4 import BeautifulSoup
import pandas as pd 
import sqlite3
import numpy as np 
from datetime import datetime 

def log_progress(message):
    timestamp_format = '%Y-%h-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timestamp_format)
    with open("./code_log.txt","a") as f:
        f.write(timestamp + ' : ' + message + '\n')

def extract(url, table_attribs):
    page = requests.get(url).text
    data = BeautifulSoup(page,'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col)!= 0:
            data_dict = {table_attribs[0]: col[1].find_all('a')[-1].contents[0],
                         table_attribs[1]: float(col[2].contents[0].strip())}
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df,df1], ignore_index=True)
    return df

def transform(df, csv_path):
    er = pd.read_csv(csv_path).set_index('Currency').to_dict()['Rate']

    df['MC_GBP_Billion'] = [np.round(x*er['GBP'],2)
                            for x in df['MC_USD_Billion']]  

    df['MC_EUR_Billion'] = [np.round(x*er['EUR'],2)
                            for x in df['MC_USD_Billion']] 
    
    df['MC_INR_Billion'] = [np.round(x*er['INR'],2)
                            for x in df['MC_USD_Billion']]      
    return df

def load_to_csv(df, output_path):
    df.to_csv(output_path)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ['Name', 'MC_USD_Billion'] 
db_name = 'Banks.db'
table_name = 'Largest_banks'
csv_path = './Largest_banks_data.csv'

log_progress('Preliminaries complete. Initiating ETL process')

df = extract(url, table_attribs)

log_progress('Data extraction complete. Initiating Transformation process')

df = transform(df, './exchange_rate.csv')

log_progress('Data transformation complete. Initiating Loading process')

load_to_csv(df,output_path=csv_path)

log_progress('Data saved to CSV file')

sql_connection = sqlite3.connect('Banks.db')

log_progress('SQL Connection initiated')

load_to_db(df, sql_connection, table_name)

log_progress('Data loaded to Database as a table, Executing queries')

query_statement = f"SELECT * from {table_name}"
run_query(query_statement,sql_connection)
query_statement = f"SELECT AVG(MC_GBP_Billion) FROM {table_name}"
run_query(query_statement,sql_connection)
query_statement = f"SELECT Name from {table_name} LIMIT 5"
run_query(query_statement,sql_connection)

log_progress('Process Complete')

log_progress('Server Connection closed')