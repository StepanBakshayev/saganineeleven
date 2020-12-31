from saganineeleven.stringify import stringify, parse
from saganineeleven.straighten import elementstr, Element

def test():
	str_element = [
		('Hello,', Element(path=(((0, 'root'), 0), ((0, 'p'), 0)), namespaces=('', 'xns'), offset=0, length=6)),
		('{{ name }}', Element(path=(((0, 'root'), 0), ((0, 'p'), 1)), namespaces=('', 'xns'), offset=0, length=10)),
		("I proud to greet some curios users.", Element(path=(((0, 'root'), 0), ((0, 'p'), 2)), namespaces=('',), offset=0, length=35)),
		("There are some possible optimization for a future.", Element(path=(((0, 'root'), 0), ((0, 'p'), 3)), namespaces=('',), offset=0, length=50)),
		("I want to sure I don't do it earlier.", Element(path=(((0, 'root'), 0), ((0, 'p'), 4)), namespaces=('',), offset=0, length=37)),
		("Buy, ", Element(path=(((0, 'root'), 0), ((0, 'p'), 5)), namespaces=('',), offset=0, length=5)),
		('{{ name }}', Element(path=(((0, 'root'), 0), ((0, 'p'), 5)), namespaces=('', 'xns'), offset=5, length=10)),
	]
	text = []
	for string, element in str_element:
		es = elementstr(string)
		es.elements = element,
		text.append(es)

	assert list(map(lambda p: (p[1], p[0]), parse(stringify(text)))) == str_element
