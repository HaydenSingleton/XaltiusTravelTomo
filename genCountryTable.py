import os
# from datetime import datetime
import pandas as pd
from pandas import DataFrame

url = "https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements"

try:
    os.mkdir("data")
except Exception:  # Generic OS Error
    pass
os.chdir("data")

# Get country data/list from the third table on the page
df = pd.read_html(url)[2]

# Fix column titles
df.columns = list(df.iloc[0,:])
df.drop(df.index[2])
df.drop(df.index[0], inplace=True) # df = df[1:]

# Delete extra columns
df.drop(df.columns[2:], axis=1, inplace=True)

df.set_index('Code', inplace=True)

filename = "countries.csv"
filepath = os.path.join(os.getcwd(), filename)
df.to_csv(path_or_buf=filepath)


print(df.head())
