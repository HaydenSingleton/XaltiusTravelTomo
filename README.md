# TravelTomo
Main script is _tripAdivisor-test
Last working version is _tripAdvisor

# Script to pull data from Trip Advisor's "Things to do page"
This code takes data from Trip Advisor about attractions in the location/city, to be
stored in a csv file (wip) and to be cleaned using pandas.

Data includes each attraction's Title, Rating, Review Count, Phone Number, Address, Locality, Country, Opening Hours

# Data Heirarchy [Each is a field in the csv]

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
## Country
 The country where the location/city is as a string
## Opening Hours
 Times each attraction is open as a list of tuples for each combination
 of opening hours for every day of the week
## Estimated Cost (WIP)
 A string of cost in the displayed currency
## Estimated Time of Visit (WIP)
 A string containing the estimated duration given by Trip Advisor
## Reviews (WIP)
 A collection of user reviews as a filename of a csv file containing all reviews, scores,
 dates, and titles for an attraction, all stored in a local directory named after the city
