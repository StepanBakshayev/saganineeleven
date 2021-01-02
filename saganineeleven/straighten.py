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
from typing import Tuple, List
from xml.etree import ElementTree

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

TagType = Tuple[int, str]


@dataclass(frozen=True)
class Element:
	path: Tuple[Tuple[TagType, int], ...]
	namespaces: Tuple[str, ...]
	offset: int
	length: int


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
		# mircooptimization + flow requirement
		if start < len(self):
			cursor = 0
			elements = iter(self.elements)
			for element in elements:
				if cursor <= start < element.length + cursor:
					break
				cursor += element.length
			# there are valid element anyway guaranteed by upper condition guard
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
			new.elements = tuple(new_elements)

		return new

	def __repr__(self):
		return f"<elementstr: '{self!s}', {getattr(self, 'elements', ())}>"


ContentType = Enum('ContentType', 'plaintext template', module=__name__)


def straighten(
	file,
	Lexer
) -> Tuple[ContentType, List[elementstr]]:
	text = []
	lexer = Lexer()
	Node = namedtuple('Node', 'tag counter')
	route = deque((Node(None, Counter()),))
	content_type = ContentType.plaintext
	# XXX: ElementTree construct whole tree in memory anyway. This consumes memory for nothing.
	for (event, element) in ElementTree.iterparse(file, events=('start', 'end',)):
		if event == 'start':
			tag = element.tag
			route[-1].counter[tag] += 1
			route.append(Node(tag, Counter()))

		elif event == 'end':
			route.pop()

			# Test must be in leaf node.
			# XXX: this is ugly way for checking children.
			tree = element.iter()
			# pull root. It is node by self.
			next(tree)
			if next(tree, None) is not None:
				continue

			# shortcut
			if element.text is None:
				continue

			namespaces = []
			path = deque()
			element_tag = element.tag
			namespace_re = re.compile(r'^{(?P<namespace>.*?)}(?P<tagname>.*?)$')
			for r in reversed(route):
				order = r.counter[element_tag]
				namespace, tagname = '', element_tag
				match = namespace_re.match(element_tag)
				if match:
					namespace, tagname = match.group('namespace', 'tagname')
				try:
					index = namespaces.index(namespace)
				except ValueError:
					namespaces.append(namespace)
					index = len(namespaces) - 1
				path.appendleft(((index, tagname), order-1))

				element_tag = r.tag
				if element_tag is None:
					break

			chunk = elementstr(element.text)
			# xml.etree.ElementTree.ElementTree.find does not support match for root element of tree. Cut head.
			# XXX: there are root element in namespaces. It is nonsense.
			chunk.elements = Element(tuple(path), tuple(namespaces), 0, len(chunk)),

			lexer.feed(chunk)
			for token, element in lexer.read_events():
				# terminal can be splitted by many elements, get first and ignore others.
				if token is Token.terminal:
					content_type = ContentType.template
					solid = elementstr(element)
					# XXX: this is wrong. It is Poor's man solution.
					solid.elements = replace(element.elements[0], length=len(element)),
					element = solid
				text.append(element)

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
		text.append(element)

	return content_type, text
