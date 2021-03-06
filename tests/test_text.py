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
from dataclasses import astuple
from xml.etree.ElementTree import fromstring

from test_executor import dataform

from saganineeleven.contrib import docx
from saganineeleven.contrib.docx import processor_factory
from saganineeleven.executor import Route, TreeBuilder


def test_docx():
	single_text = fromstring("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
	<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr></w:rPr><w:t>{% for c in &apos;ABC&apos; %}</w:t></w:r>""")
	chartags_multiple_text = fromstring("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
	<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr></w:rPr><w:tab/><w:t xml:space="preserve">   {% </w:t><w:t>if c != &apos;B&apos; %}{{ c }}{% else%}</w:t></w:r>""")
	preserve_multiple_text = fromstring("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
	<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:rPr><w:i w:val="false"/><w:iCs w:val="false"/></w:rPr><w:t xml:space="preserve">{% cycle &apos;&apos; &apos;\t is odd&apos; %}   </w:t><w:br/><w:t>, world!</w:t></w:r>""")

	# textual representation of content
	assert tuple(docx.convert(single_text)) == (((1,), "{% for c in 'ABC' %}"),)
	assert tuple(docx.convert(preserve_multiple_text)) == (((1,), "{% cycle '' '\t is odd' %}   "), ((2,), '❬br∕❭'), ((3,), ', world!'))
	assert tuple(docx.convert(chartags_multiple_text)) == (((1,), '❬tab∕❭'), ((2,), '   {% '), ((3,), "if c != 'B' %}{{ c }}{% else%}"))

	# interpretation of textual representation in tree
	namespaces = []
	# fill namespaces
	astuple(dataform(chartags_multiple_text, namespaces))
	builder = TreeBuilder(chartags_multiple_text)
	builder.copy((Route((), (0, 1)), Route((), (2,))))
	processor = processor_factory(builder.destination_chain[-1], builder.current_element)
	processor.feed(' ')
	processor.feed(' ')
	processor.feed(' ')
	processor.feed('\t A\n')
	processor.close()
	assert astuple(dataform(builder.destination, namespaces)) == (
		 '{ns0}r',
		 {},
		 None,
		 None,
		 (('{ns0}rPr', {}, None, None, ()),
		  ('{ns0}tab', {}, None, None, ()),
		  ('{ns0}t', {'{ns1}space': 'preserve'}, '   ', None, ()),
		  ('{ns0}tab', {}, None, None, ()),
		  ('{ns0}t', {'{ns1}space': 'preserve'}, ' A', None, ()),
		  ('{ns0}br', {}, None, None, ())))
