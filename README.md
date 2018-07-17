# TravelTomo
Main script is "_tripAdivisor-test.py"
Last working version is "_tripAdvisor.py"

## Script to pull data from Trip Advisor's "Things to do" search results
This code takes data from Trip Advisor about attractions in the location/city, to be
stored in a csv file (wip) and to be cleaned using pandas.

Data includes each attraction's Title, Rating, Review Count, Phone Number, Address, Locality, Country, Opening Hours

# Data Heirarchy (Each is a field in the csv)

## Title
 The title of each attraction as a string
## Rating
 A decimal score up to 5.0
## Review Count
 The number of user reviews, an integer
## User Reviews (WIP)
 A collection of the first 10 user reviews stored as a dictionary
 with each username as a key and each paragraph as a value
## Phone Number
 The phone number and country code, a string
## Address
 The street address if it exists as a string
## Locality
 The locality (usually zip code and province) as a string
## Country
 The country where the location/city is as a string
## Date Generated
 The date the list was generated as a datetime object with microseconds scrubbed to 0
## Keywords
 Most common tags/keywords used in the user review section, stored as dictionary with
 each keyword as the key and the frequency of its occurance as the value
## Estimated Duration of Visit (WIP)
 A string containing the estimated duration given by Trip Advisor
## Estimated Cost
 A string of cost in the displayed (local) currency
