from collections import defaultdict
from lxml import etree as ET
import codecs, pprint 
import json, sys, re



pp = pprint.PrettyPrinter(indent=4)

# regex expressions to check keys 
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# keys contained on the created section
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]



def xml_iter(filename, func, args):
	"""
		Iterates over an XML map calling the passed function on each element.

		filename: input file containing valid XML
		func: function called passing each child of the root one at the time (must return args)
		args: dictionary containing arguments to pass to func, they're also

		returns the arguments
	"""
	context = ET.iterparse(filename, events=('start',))
	for event, elem in context:
		args = func(elem, args)
		# delete current node and parents saved in memory to prevent 
		# overuse of RAM and consequent use of swap (the tree 
		# gets huge even though the file it's relatively small)
		elem.clear()
		while elem.getprevious() is not None:
			del elem.getparent()[0]
	del context

	return args

def elem_iter(element, args):
	"""
		Calls a function passing the element and its 
		children one at the time.

		returns args
	"""
	args = args["func"](element, args)

	for sub in element:
		args = args["func"](sub, args)
	return args

def xml_iter_gen(filename, func, args):
	"""
		Generator version of xml_iter that yields args for each element.

		filename: input file containing valid XML
		func: function called passing each child of the root one at the time (must return args)
		args: dictionary containing arguments to pass to func, they're updated at each loop

		yield the arguments
	"""
	context = ET.iterparse(filename, events=('start',))
	for event, elem in context:
		args = func(elem, args)
		# delete current node and parents saved in memory to prevent 
		# overuse of RAM and consequent use of swap (the tree 
		# gets huge even though the file it's relatively small)
		elem.clear()
		while elem.getprevious() is not None:
			del elem.getparent()[0]
		yield args
	del context



def add_tag(element, args):
	"""
		Increases the counter of the tag corresponding to
		the element's tag.
	"""
	args["tags"][element.tag] += 1
	return args

def add_attrs(element, args):
	"""
		Increases the counter of the attributes contained
		in the element
	"""
	for attr in element.attrib:
		args["attrs"][attr] += 1
	return args

def shape(element, args):
	"""
		Parses an XML element into a defaultdict and saves it 
		into args["parsed"].

		returns args
	"""
	parsed = args["parsed"]

	attrs = element.attrib
	if element.tag == "tag":
		key = attrs["k"]
		value = attrs["v"]

		if lower.match(key):
			parsed[key] = value
		elif lower_colon.match(key):
			skey = key.split(":")
			# in case there's already a value for this key and it's not a dictionary
			# I create the dictionary and store the old value with None key
			if type(parsed[skey[0]]) != dict:
				parsed[skey[0]] = {None:parsed[skey[0]]}
			parsed[skey[0]][skey[1]] = value
		else:
			parsed["problem_tags"][key] = value

	elif element.tag == "nd":
		# if there's no node, by default the value of 
		# "nodes" is a dictionary
		if type(parsed["nodes"]) == dict:
			parsed["nodes"] = [attrs["ref"]]
		else:
			parsed["nodes"].append(attrs["ref"])
	
	elif element.tag in ["node", "way"]: 
		# type it's already in use therefore __type__
		parsed["__type__"] = element.tag
		for attr in attrs:
			if attr in CREATED:
				parsed["created"][attr] = attrs[attr]
			elif attr in ["lat", "lon"]:
				parsed["pos"][attr] = attrs[attr]
			else:
				parsed[attr] = attrs[attr]

	args["parsed"] = parsed
	return args



def count_tags(file_in):
	"""
		Returns a defaultdict containing tags and occurrencies
		of them.
	"""
	args = {"tags":defaultdict(lambda:0)}
	return xml_iter(file_in, add_tag, args)["tags"]

def count_attrs(file_in):
	"""
		Returns a defaultdict containing attributes and occurrencies
		of them.
	"""
	args = {"attrs":defaultdict(lambda:0), "func":add_attrs}
	return xml_iter(file_in, elem_iter, args)["attrs"]



def shape_element(element, args):
	"""
		Parse an XML element and its children into a defaultdict.

		returns args
	"""
	if element.tag in ["node", "way"]:
		args["parsed"] = defaultdict(lambda:{})
		args["func"] = shape
		args["count"] += 1
		return elem_iter(element, args)
		
	args["parsed"] = None
	return args

def process_map(file_in, v = (False, 0)):
	"""
		Converts an XML map into JSON.

		file_in: input file
		v: verbose, tuple containing boolean and int
		representing interval
	"""
	file_out = file_in + ".json"
	
	with codecs.open(file_out, "w") as fo:
		args = {"count": 0}

		for args in xml_iter_gen(file_in, shape_element, args):
			if args and args["parsed"]:
				fo.write(json.dumps(args["parsed"]) + "\n")
			# if verbose mode true print every [interval] elements
			if v[0] and args["count"] % v[1] == 0:
				print args

	print "Elements count: ", args["count"]



if __name__ == "__main__":
	try:
		filename = sys.argv[1]
		file_out = process_map(filename, v = (True, 100000))
		
		#tags = count_tags(file_in)
		#pp.pprint(dict(tags))
	
		#attrs = count_attrs(file_in)
		#pp.pprint(dict(attrs))
	except IndexError:
		print "usage of this program:\n\tpython model.py [input_file]"
