from io import StringIO

from saganineeleven.straighten import straighten, Element, ContentType
from saganineeleven.contrib.django import Lexer

def test_all_terminals_present():
	xml = StringIO("""<?xml version="1.0" encoding="UTF-8"?>
		<root>
			<p>Hello,</p>
			<p>{{ name }}!</p>
			<p>I proud to greet some curios users.</p>
			<p>There are some possible optimization for a future.</p>
			<p>I want to sure I don't do it earlier.</p>
			<p>Buy, {{ name }}.</p>
		</root>"""
	)
	template, text = straighten(xml, Lexer)
	assert template is ContentType.template
	template_element = [
		('Hello,', (Element(path=(((0, 'root'), 0), ((0, 'p'), 0)), namespaces=('',), offset=0, length=6),),),
		('{{ name }}', (Element(path=(((0, 'root'), 0), ((0, 'p'), 1)), namespaces=('',), offset=0, length=10),)),
		("!I proud to greet some curios users.There are some possible optimization for a future.I want to sure I don't do it earlier.Buy, ", (Element(path=(((0, 'root'), 0), ((0, 'p'), 1)), namespaces=('',), offset=10, length=1), Element(path=(((0, 'root'), 0), ((0, 'p'), 2)), namespaces=('',), offset=0, length=35), Element(path=(((0, 'root'), 0), ((0, 'p'), 3)), namespaces=('',), offset=0, length=50), Element(path=(((0, 'root'), 0), ((0, 'p'), 4)), namespaces=('',), offset=0, length=37), Element(path=(((0, 'root'), 0), ((0, 'p'), 5)), namespaces=('',), offset=0, length=5))),
		('{{ name }}', (Element(path=(((0, 'root'), 0), ((0, 'p'), 5)), namespaces=('',), offset=5, length=10),)),
		('.', (Element(path=(((0, 'root'), 0), ((0, 'p'), 5)), namespaces=('',), offset=15, length=1),)),
	]
	assert list(map(lambda t: (str(t), t.elements), text)) == template_element
