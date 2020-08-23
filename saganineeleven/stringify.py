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
from dataclasses import dataclass, field, make_dataclass
from collections import deque, Counter

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


class elementstr(str):
	pass


def stringify(
	file,
	Lexer
) -> str:
	text = []
	lexer = Lexer()
	route = deque()
	# XXX: this is not pull parser. Consider in the future the possibility of using XMLPullParser.
	for (event, element) in ElementTree.iterparse(file, events=('start', 'end',)):
		if event == 'start':
			tag = element.tag
			if route:
				route[-1][1][tag] += 1
			route.append((tag, Counter()))

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

			chunk = elementstr(element.text)
			path = deque()
			element_tag = element.tag
			for r in reversed(route):
				path.appendleft(f'{element_tag}[{r[1][element_tag]}]')
				element_tag = r[0]
			path.appendleft(f'{element_tag}[1]')
			chunk.elements = Element('/'.join(path), 0, len(chunk)),

			lexer.feed(chunk)
			for event, elem in lexer.read_events():
				print(event, elem)
			text.append(element.text or '')

		else:
			raise RuntimeError(f'Unsupported event type {event} from ElementTree.iterparse().')

	lexer.close()
	for event, elem in lexer.read_events():
		print(event, elem)

	return ''.join(text)
