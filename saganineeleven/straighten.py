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
from dataclasses import dataclass, replace
from enum import Enum
from itertools import chain
from typing import Callable, Iterable, Mapping, Sequence, Tuple
from xml.etree.ElementTree import Element

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
Path = Tuple[Index, ...]


@dataclass(frozen=True)
class ShadowElement:
	"""ElementPointer contains two kinds of information:
	- navigation (fields: path)
	- interpretation (fields: representation_length, offset, length, is_constant)

	Interpretation ways down to two states:
	- original node from source tree to copy as is (fields: is_constant=True)
	- node with dynamic content (fields: is_constant=False, offset, length, representation_length)

	The field `is_constant` is depended of offset, length, representation_length.

	It is allowed to have ElementPointer with zero length."""
	path: Path
	atom: int
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


def travel(node: Element, level=0):
	yield level, node
	for child in node:
		yield from travel(child, level+1)


@dataclass(frozen=True)
class ElementPointer:
	path: Path
	is_constant: bool
	index: int


Line = Sequence[Tuple[ElementPointer, str]]


def straighten(
	root: Element,
	Lexer,
	text_nodes: Mapping[str, int],
	converter: Callable[[Element], Iterable[Tuple[Path, str]]]
) -> Tuple[ContentType, Line]:
	lexer = Lexer()
	content_type = ContentType.plaintext
	traveler = travel(root)
	branch = []
	watermark = None
	for level, element in traveler:
		if watermark is not None:
			if level > watermark:
				continue
			watermark = None

		if level+1 <= len(branch):
			branch[level:] = []
		branch.append(element)

		if element.tag in text_nodes:
			for path, text in converter(element):
				chunk = elementstr(text)
				chunk.elements = ShadowElement(
					path=tuple(map(lambda z: list(z[0]).index(z[1]), zip(branch, branch[1:])))+path,
					atom=text_nodes[element.tag]-len(path)+1,  # below code block is using reverse, prepare data for handling.
					representation_length=len(chunk),
					offset=0,
					length=len(chunk),
					is_constant=True,
				),
				lexer.feed(chunk)

			watermark = level

	line = []
	index = 0
	previous_path = ()

	lexer.close()
	for token, estr in lexer.read_events():
		elements, text = estr.elements, str(estr)
		if token is Token.terminal:
			content_type = ContentType.template

			first, *rest = elements
			container = tuple(reversed(first.path))[-first.atom:]
			if any(container != tuple(reversed(e.path))[-e.atom:] for e in rest):
				raise RuntimeError(f'Terminal {token} `{text!s}` is splitted across different atoms {elements!r}.', token, text, elements)

			# There are two interesting cases for further processing.
			# It is substitution with variable. It is coping with cycle.
			# Terminal is consuming by template engine. Leaves breadcrumbs before for variable and after for cycle.
			# Once more terminal can be splitted by many elements, use first and ignore others.
			# XXX: this is wrong. It is Poor's man solution.
			head, tail = elements[0], elements[-1]
			elements = replace(head, length=len(estr), is_constant=False),
			for element in rest:
				elements += replace(element, offset=element.offset+element.length, length=0, is_constant=False),

		offset = 0
		for element in elements:
			# XXX: put in test check for continuous index numbers.
			if element.path != previous_path:
				index += 1
				previous_path = element.path
			line.append((
				ElementPointer(path=element.path, is_constant=element.is_constant, index=index),
				text[offset:offset+element.length],
			))
			offset += element.length

	return content_type, line
