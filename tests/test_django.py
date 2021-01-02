from dataclasses import replace

from django.conf import settings

from saganineeleven.contrib.django import Lexer
from saganineeleven.straighten import Element, elementstr, Token


def test_lexer():
	settings.configure()
	chunks = (
		("{% for c in 'ABCD' %}", Element((((0, 'root'), 0), ((0, 'p'), 0)), ('',), 0, 0)),
		("{% if c != 'c' %}character {{ c }}{% endif %}", Element((((0, 'root'), 0), ((0, 'p'), 1)), ('',), 0, 0)),
		('{% endfor %}', Element((((0, 'root'), 0), ((0, 'p'), 2)), ('',), 0, 0)),
	)
	lexems = (
		(Token.terminal, "{% for c in 'ABCD' %}"),
		(Token.terminal, "{% if c != 'c' %}"),
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
