### Self-studying project with MongoDB
-------

This project aims to learning how to use MongoDB with Python and build a Web interface with Flask. 

Required python packages: pymongo, flask, bokeh, gevent 

You can run the following code to install requirements:

```
pip install -r requirements.txt
```

**Please make sure you have all those packages installed in your machine before you go any further.** 

Testing Data: The house prices estimation training data from Kaggle Competition, available [here](https://www.kaggle.com/c/house-prices-advanced-regression-techniques/data).

Full training list: 
  * Insert data into MongoDB
  * Query data from MongoDB
  * Build Web interface 

### Database structure
-------
There are five collections in the "**test_database**". 
- "**test_houseprices**", the small amount of data for initial testing; 
- "**currencyEuroBase**", the currency exchange rate information from [European Central Bank](http://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html); 
- "**data_fields**", the data fields name with description; 
- "**test**", the full range of data; 
- "**test_quality**", the field name with missing data count and rate.

### How to set up server and database for web interface (Windows)
-------

1.	Please download and install Mongodb, [here](https://www.mongodb.com/download-center?jmp=nav#community) and Studio 3T, [here](https://studio3t.com/download/?gclid=CjwKCAiA_c7UBRAjEiwApCZi8S22lBU81zoWG7zI8AAofJZpeBDKOUCDY-1J9EGkS-75mY6WHnFO3hoC4XUQAvD_BwE). 
2.	Set up database with mongodump folder. (**Please decompress the mongodump file in a directory before you go any further.**) 
- Run mongod.exe in cmd. It might be in the path "C:\Program Files\MongoDB\Server\3.6\bin\mongod.exe"
- Open Studio 3T and connect with DB server (localhost:27017)
- In the Studio 3T, click the “Import” in the top graphical menu. 
  
  Choose "**BSON – mongodump folder**" -> Select the mongodump folder -> Make sure you have checked all collections in the "**test_database**" -> ... -> "Start Import"
- Now, you should have a database called "**test_database**" with five collections under localhost:27017 DB server.
3.	Open a new cmd, and run test1.py.
```
python test1.py
```
4.	Now that the server’s running, visit http://localhost:8080/ with your Web browser. You’ll see the “House Price Estimation” web interface.  


### Introduction of Web Interface
--------

*In the web interface users can do the following tasks:*
1.	Visualize example data table 
2.	Add new data into database 
3.	Searching data 
4.	Require data and download excel file
5.	Require figures

In the web interface example, there are five sections: 
- “**Example Data**”, a static table shows the first 20 rows of the “*test_houseprices*” collection. When the sale price is over 200000, the cell will be filled by red color. 
- “**Adding new price information**”, a html form can add new data into “*test_houseprices*” collection. All four fields are required and house ‘Id’ will be automated generated.
- “**Searching for records**”, a html form can request data from “*test_houseprices*” collection with at least one request.
- “**Exchange currency**”, a html form will query the house prices infos from "*test_houseprice*" and add one column called "*Price(currency)*". You can also download the excel file after exchanging. 
Basically, it request a query that join the "*test_houseprices*" with the "*currencyEuroBase*" collection and calcuate the "*SalePrice*" in the request currency.  
- “**Plot for Sale Price**”, it will present nice bokeh style figure for different types of data together with average sale price in different value. More precisely, it will present a line plot with datetime x-axis for date related data(e.g. Month and Year sold), a line plot with requested data value for numerical data, or a spot plot with categories for categorial data.  

Those sections are corresponding to the listed tasks, separately. The first four section only test with five fields from the original data as shown in the “**Example Data**”.  There is a new column called “**currency**”, which is random generated from a currency list from “**currencyEuroBase**” collection. 

Notice: All the data are raw data. When you plot the sale price with some fields, you might get an empty figure. 
