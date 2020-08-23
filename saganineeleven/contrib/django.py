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
from django.template.base import tag_re
from saganineeleven.stringify import Token
from collections import deque


class Lexer:
	"""
	Lexer is for django 3.1. Each django version can change details of implementaion template system.
	This module uses private API.
	"""
	slots = 'buffer', 'is_closed', 'events'

	def __init__(self):
		self.buffer = ''
		self.is_closed = False
		self.events = deque()

	def feed(self, chunk):
		"""
		Django template lexer is based on regex. Our lexer should be 100% comptatible with django.
		I don't find a incremental regex engine. A trick is run regex find first match over again on string to simulate incremental parsing.
		"""
		assert not self.is_closed
		self.buffer += chunk
		in_tag = False
		token_type = {
			True: Token.terminal,
			False: Token.text,
		}
		# use a original processing method
		for bit in tag_re.split(self.buffer):
			self.events.append((token_type[in_tag], bit))
			in_tag = not in_tag
		# last bit is text anyway
		_, self.buffer = self.events.pop()

	def close(self):
		self.is_closed = True

	def read_events(self):
		while self.events:
			yield self.events.popleft()
		if self.is_closed:
			yield Token.text, self.buffer
			self.buffer = None
			self.events = None
