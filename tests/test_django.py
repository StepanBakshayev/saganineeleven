from dataclasses import replace

from django.conf import settings

from saganineeleven.contrib.django import Lexer
from saganineeleven.straighten import elementstr, Token, ElementPointer


def test_lexer():
	settings.configure()
	chunks = (
		("{% for c in 'ABCD' %}", ElementPointer((0,), atom=-1, representation_length=21, offset=0, length=21, is_constant=True)),
		("{% if c != 'C' %}character {{ c }}{% endif %}", ElementPointer((1,), atom=-1, representation_length=45, offset=0, length=45, is_constant=True)),
		('{% endfor %}', ElementPointer((2,), atom=-1, representation_length=12, offset=0, length=12, is_constant=True)),
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
