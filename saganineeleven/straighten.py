# Copyright 2020 Stepan Bakshayev
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
from collections import deque, Counter, namedtuple
from dataclasses import dataclass, replace
from enum import Enum
from itertools import chain
from typing import Tuple, List, Set, Callable
from xml.etree.ElementTree import iterparse, ElementTree, Element

from devtools import debug

Token = Enum('Event', 'text terminal', module=__name__)


# XXX: write this after real lexer
# class DummyLexer:
# 	"""
# 	DummyLexer is sample of Lexer.
# 	"""
# 	slots = 'chunk',

# 	def __init__(self):
# 		self.chunk = None

# 	def feed(self, chunk):
# 		self.chunk = chunk

# 	def read_events(self):
# 		return (Token.text, self.chunk),


Index = int

@dataclass(frozen=True)
class ElementPointer:
	path: Tuple[Index, ...]
	representation_length: int
	offset: int
	length: int
	is_constant: bool


class elementstr(str):
	__slots__ = 'elements',

	def __iadd__(self, other):
		new = self.__class__(f'{self!s}{other!s}')
		new.elements = getattr(self, 'elements', ()) + getattr(other, 'elements', ())
		return new

	def __getitem__(self, key):
		assert isinstance(key, slice), type(key)
		assert key.step in (None, 1), key.step
		new = self.__class__(super().__getitem__(key))
		new.elements = ()

		start, stop, _ = key.indices(len(self))
		# It are mircooptimization and algorithm requirement.
		if start < len(self):
			assert self.elements
			cursor = 0
			elements = iter(self.elements)
			for element in elements:
				if cursor <= start < element.length + cursor:
					break
				cursor += element.length
			# There are valid element anyway guaranteed by upper condition guard (aka "algorithm requirement").
			element_offset = start - cursor
			start_element = replace(element, offset=(element.offset+element_offset), length=(element.length-element_offset))
			cursor += element_offset
			new_elements = []
			for element in chain((start_element,), elements):
				element = replace(element, length=min(element.length, stop-cursor))
				new_elements.append(element)
				cursor += element.length
				if cursor == stop:
					break

			for index in 0, -1:
				element = new_elements[index]
				is_constant = element.representation_length == element.length
				if is_constant:
					assert element.offset == 0
				new_elements[index] = replace(element, is_constant=is_constant)

			new.elements = tuple(new_elements)

		return new

	def __repr__(self):
		return f"<elementstr: '{self!s}', {getattr(self, 'elements', ())}>"


ContentType = Enum('ContentType', 'plaintext template', module=__name__)


MINIMAL_TEXT_LENGTH = len('I love you.')
ETC = '❰⋯❱'


def compress(element: elementstr) -> elementstr:
	if len(element.elements) > 2 and len(element) > MINIMAL_TEXT_LENGTH:
		chunks = []
		elements = []
		offset = 0
		for part in element.elements[0], element.elements[1]:
			chunks.append(str.__getitem__(element, slice(offset, part.length+offset)))
			elements.append(part)
			offset += part.length
			if part.is_constant:
				break
		if (len(element.elements) - len(elements)) > len(elements):
			chunks.append(ETC)
			elements[-1] = replace(elements[-1], length=elements[-1].length+len(ETC))
			last_chunk = len(chunks)
			last_element = len(elements)
			offset = 0
			for part in element.elements[-1], element.elements[-2]:
				chunks.insert(last_chunk, str.__getitem__(element, slice(-part.length-offset, -offset or None)))
				elements.insert(last_element, part)
				offset += part.length
				if part.is_constant:
					break

			element = elementstr(''.join(chunks))
			element.elements = tuple(elements)

	return element


def straighten(
	file,
	Lexer,
	text_nodes: Set[str],
	converter: Callable[[Element], str]
) -> Tuple[ContentType, List[elementstr]]:
	text = []
	lexer = Lexer()
	content_type = ContentType.plaintext
	# XXX: ElementTree construct whole tree in memory anyway. This consumes memory for nothing.
	parser = iterparse(file, events=('start', 'end',))
	event, element = next(parser)
	assert event == 'start'
	branch = [element]
	for (event, element) in parser:
		if event == 'start':
			branch.append(element)

		elif event == 'end':
			if element.tag in text_nodes:
				chunk = elementstr(converter(element))
				chunk.elements = ElementPointer(
					path=tuple(map(lambda z: list(z[0]).index(z[1]), zip(branch, branch[1:]))),
					representation_length=len(chunk),
					offset=0,
					length=len(chunk),
					is_constant=True,
				),
				lexer.feed(chunk)

			branch.pop()
			# XXX: It is stub for ElementTree, unlink children to free memory.
			element[:] = []

		else:
			raise RuntimeError(f'Unsupported event type {event} from ElementTree.iterparse().')

	lexer.close()
	for token, element in lexer.read_events():
		# terminal can be splitted by many elements, get first and ignore others.
		if token is Token.terminal:
			content_type = ContentType.template
			solid = elementstr(element)
			# XXX: this is wrong. It is Poor's man solution.
			solid.elements = replace(element.elements[0], length=len(element)),
			element = solid
		elif token is Token.text:
			element = compress(element)

		text.append(element)

	return content_type, text
