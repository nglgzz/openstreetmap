# OpenStreetMap
This project is about wrangling data coming from OpenStreetMap.
The goal of this project was to learn about the steps for getting data, using MongoDB and its Python driver to save it on a database, and cleaning that data.

Even though the process wasn't linear, the order in which the scripts are supposed to be used is the following. Once you have exported the XML file from OpenStreetMap, `model.py` is
executed to parse XML to JSON, then it's `import.py`'s turn to import the JSON documents into MongoDB, once that is finished, `street_spider.py` has to be run using Scrapy and its task is to
scrape street names information from a local wiki, then `import.py` is run again to import the file generated by the spider, and finally `clean.py` is used to correct some of the streetnames we initially imported using the scraped ones.