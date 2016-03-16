import scrapy

class StreetsSpider (scrapy.Spider):

	name = "streets"
	start_urls = ["https://lokalhistoriewiki.no/index.php/Gater_og_veier_i_Oslo_kommune"]

	def parse(self, response):
		# for each row in the first column of the table 
		for el in response.css("table tr td a"):
			# extract the name of the street and yield it
			s = el.css("::text").extract()
			if s != []:
				yield {"name":s[0]}
