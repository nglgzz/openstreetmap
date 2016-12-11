import pymongo, pprint, json
import sys, re

# function to check whether a string contains a digit
has_num = lambda s: any(c.isdigit() for c in s)

# postcodes to fix
postcodes = {
	"10":"0010",
	"26":"0026",
	"50":"0050",
	"N-0286":"0286",
	"1325 Lysaker":"1325",
	"1283 Oslo":"1283",
	"1900 Fetsund":"1900"
}

# abbreviations to fix
abbreviations = {
	re.compile(r'^.*( gt).*$'):"gate"
}


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def distance(str1, str2):
	"""
		Returns edit distance in percentage
	"""
	return 100 - int(levenshtein(str1, str2)/float(len(str2))*100)


def update_field(collection, field, old_value, new_value):
	query = {field: old_value}
	update = {"$set":{field: new_value}}
	res = collection.update_many(query, update)

	print old_value, " -> ", new_value
	print "(matched-modified):", res.matched_count, res.modified_count

	return res

def check_streets(db_name, data, streets):
	client = pymongo.MongoClient("localhost", 27017)
	db = client[db_name]

	streets_col = db[streets]
	data_col = db[data]

	# fix postcodes
	for old, new in postcodes.items():
		res = update_field(data_col, "addr.postcode", old, new)
		print "Postcode (matched,modified): ", res.matched_count, res.modified_count

	pipeline = [{"$match":{"addr.street":{"$exists":1}}}, {"$group":{"_id":"$addr.street"}}, {"$project":{"name":"$_id"}}]
	data_by_streets = data_col.aggregate(pipeline)


	not_found = 0
	discarded = 0
	changed = 0
	changed_total = 0

	for street in data_by_streets:

		# fix abbreviations
		for abbr in abbreviations:
			if abbr.match(street["name"]):
				new = street["name"].replace(" gt", " gate").strip(".")
				res = update_field(data_col, "addr.street", street["name"], new)
				changed_total += res.modified_count
				changed += 1
				street["name"] = new


		match = streets_col.find_one({"$text":{"$search":street["name"]}})

		if match != None:
			evaluation = distance(street["name"], match["name"])
			# 86-99 auto correct
			# 0-85, 100 discard
			if evaluation > 85 and evaluation < 100:
				# if both the current street name and the match have a number
				# ask the user cause the number could differ and change completely
				# the street name, even if the street names are really similar
				if has_num(match["name"]) and has_num(street["name"]):
					choice = raw_input("{} -> {} ({})[y/N]: ".format(street["name"], match["name"], evaluation))
					if choice.lower() == "y":
						res = update_field(data_col, "addr.street", street["name"], match["name"])
						changed_total += res.modified_count
						changed += 1
					else:
						discarded += 1
				else:
					res = update_field(data_col, "addr.street", street["name"], match["name"])
					changed_total += res.modified_count
					changed += 1
			else:
				discarded += 1
		else:
			not_found += 1

	print "not found: ", not_found
	print "discarded: ", discarded
	print "changed: ", changed
	print "changed total: ", changed_total

if __name__ == "__main__":
	try:
		db_name = sys.argv[1]
		data_col = sys.argv[2]
		streets_col = sys.argv[3]

		check_streets(db_name, data_col, streets_col)
	except IndexError:
		print "usage of this program:\n\tpython import.py [database] [data_collection] [streets_collection]"