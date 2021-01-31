from itertools import count

from saganineeleven.straighten import ETC, ElementPointer
from saganineeleven.stringify import parse, stringify


def test():
	indexer = count(1)
	# XXX: Test does not require ElementPointer semantically correction.
	line = [
		(ElementPointer(path=(0, 0, 1,), index=next(indexer), is_constant=True), 'Hello,',),
		(ElementPointer(path=(0, 1, 1,), index=next(indexer), is_constant=False), '{{ name }}',),
		(ElementPointer(path=(0, 1, 1,), index=next(indexer), is_constant=False), f"!",),
		(ElementPointer(path=(0, 2, 1,), index=next(indexer), is_constant=True), f"I proud to greet some curios users.{ETC}",),
		(ElementPointer(path=(0, 4, 1,), index=next(indexer), is_constant=True), f"I want to sure I don't do it earlier.",),
		(ElementPointer(path=(0, 5, 1,), index=next(indexer), is_constant=False), f"Buy, ",),
		(ElementPointer(path=(0, 5, 1,), index=next(indexer), is_constant=False), '{{ name }}',),
		(ElementPointer(path=(0, 5, 1,), index=next(indexer), is_constant=False), '.',),
	]
	assert list(parse(stringify(line))) == line
