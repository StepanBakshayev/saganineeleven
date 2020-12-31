from itertools import islice
from typing import Sequence, Iterator, Tuple

import re

from msgpack import packb, unpackb

from .straighten import elementstr, Element
from dataclasses import astuple

# surrogates U+DC80 to U+DCFF
element_re = re.compile(r'\ud800([\U00000000-\U0010ffff]+?)\ud801')

def stringify(text: Sequence[elementstr]) -> str:
	buffer = []
	for chunk in text:
		offset = 0
		for element in chunk.elements:
			buffer.append('\ud800')
			buffer.append(packb(astuple(element)).decode('utf-8', 'surrogateescape'))
			buffer.append('\ud801')
			buffer.append(str.__getitem__(chunk, slice(offset, offset+element.length)))
			offset += element.length
	return ''.join(buffer)


def parse(tape: str) -> Iterator[Tuple[Element, str]]:
	in_element = True
	element_dump = None
	# XXX: There are big memory consumption and big cpu utilization. I don't find any good regexp iterable match.
	for bit in islice(element_re.split(tape), 1, None):
		if in_element:
			element_dump = bit
		else:
			yield Element(*unpackb(element_dump.encode('utf-8', 'surrogateescape'), use_list=False)), bit
			element_dump = None
		in_element = not in_element
