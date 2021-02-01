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
from dataclasses import replace

from django.conf import settings

from saganineeleven.contrib.django import Lexer
from saganineeleven.straighten import ShadowElement, Token, elementstr


def test_lexer():
	settings.configure()
	chunks = (
		("{% for c in 'ABCD' %}", ShadowElement((0,), atom=0, representation_length=21, offset=0, length=21, is_constant=True)),
		("{% if c != 'C' %}character {{ c }}{% endif %}", ShadowElement((1,), atom=0, representation_length=45, offset=0, length=45, is_constant=True)),
		('{% endfor %}', ShadowElement((2,), atom=0, representation_length=12, offset=0, length=12, is_constant=True)),
	)
	lexems = (
		(Token.terminal, "{% for c in 'ABCD' %}"),
		(Token.terminal, "{% if c != 'C' %}"),
		(Token.text, 'character '),
		(Token.terminal, '{{ c }}'),
		(Token.terminal, '{% endif %}'),
		(Token.terminal, '{% endfor %}')
	)
	lexer = Lexer()
	for text, element in chunks:
		str_element = elementstr(text)
		str_element.elements = replace(element, length=len(text)),
		lexer.feed(str_element)

	lexer.close()

	events = tuple(map(lambda p: (p[0], str(p[1])), lexer.read_events()))
	assert events == lexems
