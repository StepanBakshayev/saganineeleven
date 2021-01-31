import re
from dataclasses import astuple
from itertools import islice
from typing import Iterator, Tuple

from msgpack import packb, unpackb

from .straighten import ElementPointer, Line

# surrogates U+DC80 to U+DCFF
element_re = re.compile(r'\ud800([\U00000000-\U0010ffff]+?)\ud801')

def stringify(line: Line) -> str:
	buffer = []
	for pointer, text in line:
		buffer.append('\ud800')
		buffer.append(packb(astuple(pointer)).decode('utf-8', 'surrogateescape'))
		buffer.append('\ud801')
		buffer.append(text)

	return ''.join(buffer)


def parse(tape: str) -> Iterator[Tuple[ElementPointer, str]]:
	in_element = True
	element_dump = None
	# XXX: There are big memory consumption and big cpu utilization. I don't find any good regexp iterable match.
	for bit in islice(element_re.split(tape), 1, None):
		if in_element:
			element_dump = bit
		else:
			yield ElementPointer(*unpackb(element_dump.encode('utf-8', 'surrogateescape'), use_list=False)), bit
			element_dump = None
		in_element = not in_element
