import sys
import os
from datetime import datetime
import pandas as pd
from panadas import DataFrame
import requests
from bs4 import BeautifulSoup

url = "https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements"

response = requests.get(url)
source_code = response.text
soup = BeautifulSoup(source_code, "lxml")

df = pd.DataFrame() 

