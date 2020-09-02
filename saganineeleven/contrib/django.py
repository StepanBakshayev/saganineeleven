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
from saganineeleven.stringify import Token, elementstr
from collections import deque
from dataclasses import dataclass, field
from django.template import Context
from django.template.base import Template
from django.template.engine import Engine


@dataclass(init=True)
class Lexer:
	"""
	Lexer is for django 3.1. Each django version can change details of implementaion template system.
	This module uses private API.
	"""
	buffer: str = field(default=elementstr(), init=False)
	is_closed: bool = field(default=False, init=False)
	events: deque = field(default_factory=deque, init=False)

	def feed(self, chunk):
		"""
		Django template lexer is based on regex. Our lexer should be 100% comptatible with django.
		I don't find a incremental regex engine. A trick is run regex find first match over again on string to simulate incremental parsing.
		"""
		assert not self.is_closed
		self.buffer += chunk
		last_position = 0
		# XXX: this implementation hold much data in memory. Develop some trick for skiping as much as posible text.
		# Possible solution is checking for spicial cases. For example:
		# - re.escape(BLOCK_TAG_START)
		# - re.escape(VARIABLE_TAG_START)
		# - re.escape(COMMENT_TAG_START)
		# If nothing found then drain text to events.
		for match in tag_re.finditer(self.buffer):
			start, end = match.span()
			text = self.buffer[last_position:start]
			if text:
				self.events.append((Token.text, text))
			# self.buffer is special type. Ignore match and use it method for slicing.
			self.events.append((Token.terminal, self.buffer[start:end]))
			last_position = end + 1

		# perform cutting if there is a any match
		if last_position:
			self.buffer = self.buffer[last_position:]

	def close(self):
		self.is_closed = True

	def read_events(self):
		while self.events:
			yield self.events.popleft()
		if self.is_closed and self.buffer:
			yield Token.text, self.buffer
			self.buffer = None
			self.events = None


def render(template_string, context):
	"Shortcut."
	engine = Engine(debug=False, loaders=())
	template = Template(template_string, engine=engine)
	return template.render(Context(context, autoescape=False))
