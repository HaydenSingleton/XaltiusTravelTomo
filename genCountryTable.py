import os
import pandas as pd
# Source for 2 digit ISO codes for countries
url = "https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2"

try:
    os.mkdir("data")
except Exception:
    pass
os.chdir("data")

# Get country data/list from the third table on the page
df = pd.read_html(url)[2]

# Fix column titles (initially the first row contains the titles)
df.columns = list(df.iloc[0, :])
df.drop(df.index[2])
df.drop(df.index[0], inplace=True)  # same as df = df[1:]

# Delete extra columns
df.drop(df.columns[2:], axis=1, inplace=True)

# df.set_index('Code', inplace=True)

filename = "CountryList.csv"
# filepath = os.path.join(os.getcwd(), filename)
df.to_csv(path_or_buf=filename)
print(df.head())
print(df.tail())
