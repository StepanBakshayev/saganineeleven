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
from xml.etree import ElementTree
from enum import Enum
from dataclasses import dataclass, field, fields, make_dataclass, replace
from collections import deque, Counter, namedtuple
from itertools import chain, islice
from typing import Tuple
import re
from struct import pack, unpack_from, calcsize
from operator import attrgetter

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


@dataclass(frozen=True)
class Element:
	path: str
	offset: int
	length: int
	namespaces: Tuple[str]

	def pack(self):
		assert tuple(map(attrgetter('name'), fields(self))) == ('path', 'offset', 'length', 'namespaces')
		buffer = bytearray()

		# XXX: p(ascal) string while unpacking size is undeterminal.
		# use a low-level handmade solution.
		max_length = 255
		path_bytes = self.path.encode('utf-8')
		chunks = (path_bytes[i:i+max_length] for i in range(0, len(path_bytes), max_length))
		for chunk in chunks:
			chunk_length = len(chunk)
			buffer.extend(pack(f'!B{chunk_length}s', chunk_length, chunk))
		buffer.extend(pack('!B0s', 0, b''))

		buffer.extend(pack('!Q', self.offset))

		buffer.extend(pack('!Q', self.length))

		for namespace in self.namespaces:
			namespace_bytes = namespace.encode('utf-8')
			chunks = (namespace_bytes[i:i+max_length] for i in range(0, len(namespace_bytes), max_length))
			for chunk in chunks:
				chunk_length = len(chunk)
				buffer.extend(pack(f'!B{chunk_length}s', chunk_length, chunk))
			buffer.extend(pack('!B0s', 0, b''))
		buffer.extend(pack('!B0s', 0, b''))

		return buffer

	@classmethod
	def unpack(cls, buffer):
		assert tuple(map(attrgetter('name'), fields(cls))) == ('path', 'offset', 'length', 'namespaces')

		offset = 0
		element_path = []
		while True:
			chunk_length = unpack_from('!B', buffer, offset)[0]
			offset += calcsize('!B')
			if not chunk_length:
				break
			chunk = unpack_from(f'!{chunk_length}s', buffer, offset)[0]
			offset += calcsize(f'!{chunk_length}s')
			element_path.append(chunk.decode('utf-8'))

		element_offset = unpack_from('!Q', buffer, offset)[0]
		offset += calcsize('!Q')

		element_length = unpack_from('!Q', buffer, offset)[0]
		offset += calcsize('!Q')

		element_namespaces = []
		while True:
			namespace = []
			while True:
				chunk_length = unpack_from('!B', buffer, offset)[0]
				offset += calcsize('!B')
				if not chunk_length:
					break
				chunk = unpack_from(f'!{chunk_length}s', buffer, offset)[0]
				offset += calcsize(f'!{chunk_length}s')
				namespace.append(chunk.decode('utf-8'))
			if not namespace:
				break
			element_namespaces.append(''.join(namespace))

		return cls(
			''.join(element_path),
			element_offset,
			element_length,
			tuple(element_namespaces),
		)



class elementstr(str):
	__slots__ = 'elements',

	def __iadd__(self, other):
		new = self.__class__(f'{self!s}{other!s}')
		new.elements = getattr(self, 'elements', ()) + getattr(other, 'elements', ())
		return new

	def __getitem__(self, key):
		assert isinstance(key, slice)
		assert key.step in (None, 1)
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
# surrogates U+DC80 to U+DCFF
element_re = re.compile(r'\ud800([\U00000000-\U0010ffff]+?)\ud801')


def stringify(
	file,
	Lexer
) -> Tuple[ContentType, str]:
	text = []
	lexer = Lexer()
	Node = namedtuple('Node', 'tag counter')
	route = deque((Node(None, Counter()),))
	content_type = ContentType.plaintext
	# XXX: this is not pull parser. Consider in the future the possibility of using XMLPullParser.
	for (event, element) in ElementTree.iterparse(file, events=('start', 'end',)):
		if event == 'start':
			tag = element.tag
			route[-1].counter[tag] += 1
			route.append(Node(tag, Counter()))

		elif event == 'end':
			route.pop()

			# The invariant is childfree nodes with text.
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
			namespace_re = re.compile('^{(?P<namespace>.*?)}(?P<tagname>.*?)$')
			for r in reversed(route):
				order = r.counter[element_tag]
				match = namespace_re.match(element_tag)
				if match:
					namespace, tagname = match.group('namespace', 'tagname')
					try:
						index = namespaces.index(namespace)
					except ValueError:
						namespaces.append(namespace)
						index = len(namespaces) - 1
					element_tag = f'n{index}:{tagname}'

				path.appendleft(f'{element_tag}[{order}]')
				element_tag = r.tag
				if element_tag is None:
					break

			chunk = elementstr(element.text)
			# xml.etree.ElementTree.ElementTree.find does not support match for root element of tree. Cut head.
			# XXX: there are root element in namespaces. It is nonsense.
			chunk.elements = Element(f"./{'/'.join(islice(path, 1, None))}", 0, len(chunk), tuple(namespaces)),

			lexer.feed(chunk)
			for token, element in lexer.read_events():
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
		if token is Token.terminal:
			content_type = ContentType.template
			solid = elementstr(element)
			# XXX: this is wrong. It is Poor's man solution.
			solid.elements = replace(element.elements[0], length=len(element)),
			element = solid
		text.append(element)

	buffer = []
	for chunk in text:
		offset = 0
		for element in chunk.elements:
			buffer.append('\ud800')
			buffer.append(element.pack().decode('utf-8', 'surrogateescape'))
			buffer.append('\ud801')
			buffer.append(str.__getitem__(chunk, slice(offset, offset+element.length)))
			offset += element.length

	return content_type, ''.join(buffer)
