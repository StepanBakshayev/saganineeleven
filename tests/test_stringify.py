from saganineeleven.stringify import stringify, parse
from saganineeleven.straighten import elementstr, ElementPointer, ETC


def test():
	str_element = [
		('Hello,', ElementPointer(path=(0, 0, 1,), representation_length=6, offset=0, length=6, is_constant=True)),
		('{{ name }}', ElementPointer(path=(0, 1, 1,), representation_length=11, offset=0, length=10, is_constant=False)),
		(f"!", ElementPointer(path=(0, 1, 1,), representation_length=11, offset=10, length=1, is_constant=False)),
		(f"I proud to greet some curios users.{ETC}", ElementPointer(path=(0, 2, 1,), representation_length=35, offset=0, length=35+len(ETC), is_constant=True)),
		(f"I want to sure I don't do it earlier.", ElementPointer(path=(0, 4, 1,), representation_length=37, offset=0, length=37, is_constant=True)),
		(f"Buy, ", ElementPointer(path=(0, 5, 1,), representation_length=16, offset=0, length=5, is_constant=False)),
		('{{ name }}', ElementPointer(path=(0, 5, 1,), representation_length=16, offset=5, length=10, is_constant=False)),
		('.', ElementPointer(path=(0, 5, 1,), representation_length=16, offset=15, length=1, is_constant=False)),
	]
	text = []
	for string, element in str_element:
		es = elementstr(string)
		es.elements = element,
		text.append(es)

	assert list(map(lambda p: (p[1], p[0]), parse(stringify(text)))) == str_element
