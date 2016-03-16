import pymongo
import sys, re
import json


mongo = ("localhost", 27017)


def iter_json(filename):
	"""
		Generator to read a JSON file line by line
		useful to read big files without wasting 
		memory.
	"""
	with open(filename, "r") as f:
		for jsonline in f:
			yield json.loads(jsonline.strip("[").strip("]").strip("\n").strip(",")) 

def get_jsonlines(filename, n = 5):
	"""
		Return a list with n lines
		from a JSON file.
	"""
	data = []
	for json in iter_json(filename):
		if len(data) < n:
			data.append(json)
		else:
			return data

def mongo_import(db_name, col_name, filename, overwrite = True, v = (False, 0)):
	"""
		Imports JSON documents from a file to MongoDB.

		db_name: name of the database
		col_name: name of the collection
		filename: name of the source file
		overwrite: boolean, self-explaining
		v: verbose, tuple containing a boolean and an int
		representing the interval
	"""
	client = pymongo.MongoClient(mongo[0], mongo[1])
	collection = client[db_name][col_name]
	
	c = 0
	if overwrite:
		collection.drop()

	for json in iter_json(filename):
		collection.insert_one(json)
		if v[0] and c % v[1] == 0:
			print c, " documents added."
		c += 1
	print c, " documents added."



if __name__ == "__main__":
	try:
		db_name = sys.argv[1]
		col_name = sys.argv[2]
		filename = sys.argv[3]

		mongo_import(db_name, col_name, filename, overwrite = True, v = (True, 10000))
	except IndexError:
		print "usage of this program:\n\tpython import.py [database] [collection] [filename]"
