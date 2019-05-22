# TravelTomo
Main script is "tripAdivisor.py"
"sql-script.py" and "genCountryTable.py" are utilities for connecting with

## Purpose
  This script demonstrates backend data collection techniques
  There is no user interface with this project


## Script to pull data from Trip Advisor's "Things to do" search results
This code takes data from Trip Advisor about attractions in the location/city, to be
stored in a csv file (wip) and to be cleaned using pandas.

Data includes each attraction's Title, Rating, Review Count, Phone Number, Address, Locality, Country, Opening Hours

# Data Heirarchy

### Main Table

## Title
 The title of each attraction as a string
## Rating
 A decimal score up to 5.0
## Review Count
 The number of user reviews, an integer
## Phone Number
 The phone number and country code, a string
## Address
 The street address if it exists as a string
## Locality
 The locality (usually zip code and province) as a string
## Date Generated
 The date the list was generated as a datetime object with microseconds scrubbed to 0
## Keywords
 Most common tags/keywords used in the user review section, stored as dictionary with
 each keyword as the key and the frequency of its occurance as the value
## Estimated Duration of Visit (WIP)
 A string containing the estimated duration given by Trip Advisor
## Estimated Cost
 A string of cost in the displayed (local) currency

### User Review Table (WIP)
 Contains user reviews, usernames, ratings, dates, and user locations

### Country Table (WIP)
 Contains info such as population, GDP, currency, pop. density, demographics
