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


Token = Enum('Event', 'text terminal', module=__name__)


class DummyLexer:
	"""
	DummyLexer is sample of Lexer.
	"""
	slots = 'buffer', 'is_closed'

	def __init__(self):
		self.buffer = []
		self.is_closed = False

	def feed(self, chunk):
		pass

	def close(self):
		self.is_closed = True

	def read_events(self):
		if self.is_closed:
			return (Token.text, None),
		return ()


def stringify(
	file,
	Lexer=DummyLexer
) -> str:
	text = []
	lexer = Lexer()
	# XXX: this is not pull parser. Consider in the future the possibility of using XMLPullParser.
	for (event, element) in ElementTree.iterparse(file, events=('end',)):
		tree = element.iter()
		# pull root. It is node by self.
		next(tree)
		# The invariant is childfree nodes with text.
		if next(tree, None) is not None:
			continue
		if element.text is None:
			continue
		lexer.feed(element.text)
		for event, elem in lexer.read_events():
			pass
		print(event, element, element.text)
		text.append(element.text or '')

	lexer.close()
	for event, elem in lexer.read_events():
		pass

	return ''.join(text)
