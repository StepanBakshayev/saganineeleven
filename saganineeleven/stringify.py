# Copyright 2021 Stepan Bakshayev
#
# This file is part of saganineeleven.
#
# saganineeleven is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# saganineeleven is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with saganineeleven.  If not, see <https://www.gnu.org/licenses/>.
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
