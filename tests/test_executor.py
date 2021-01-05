from collections import deque
from io import StringIO

from saganineeleven.executor import copy, element_copy, TagIndex

from xml.etree.ElementTree import fromstring, ElementTree

from saganineeleven.straighten import namespace_re


def test_copy():
	xml = """<?xml version='1.0' encoding='UTF-8'?>\n"""\
"""<document>
		<p>paragraph</p>
		<table>
			<tr>
				<td>cell 1</td>
				<td>cell 2</td>
			</tr>
			<tr>
				<td>cell 3</td>
				<td>cell 4</td>
			</tr>
		</table>
		<p>list item</p>
		<figure>
			<t>title</t>
			<path>
				<point><x>1</x><y>11</y></point>
				<point><x>2</x><y>22</y></point>
				<point><x>3</x><y>33</y></point>
				<point><x>4</x><y>44</y></point>
			</path>
		</figure>
		<section>
			<param1 value="a" />
			<param2 value="b" />
			<param3 value="c" />
		</section>
	</document>"""
	origin_tree = ElementTree(fromstring(xml))
	origin_root = origin_tree.getroot()
	source = deque((origin_root,))

	result_root = element_copy(origin_root)
	result = ElementTree(result_root)
	destination = deque((result_root,))

	element_tag = result_root.tag
	namespace, tagname = '', element_tag
	match = namespace_re.match(element_tag)
	if match:
		namespace, tagname = match.group('namespace', 'tagname')

	ri = TagIndex(namespace, tagname, 0)
	previous_path = ri,
	paths = (
		(ri, TagIndex('', 'p', 0)),
		(ri, TagIndex('', 'table', 0), TagIndex('', 'tr', 0), TagIndex('', 'td', 0)),
		(ri, TagIndex('', 'table', 0), TagIndex('', 'tr', 0), TagIndex('', 'td', 1)),
		(ri, TagIndex('', 'table', 0), TagIndex('', 'tr', 1), TagIndex('', 'td', 0)),
		(ri, TagIndex('', 'table', 0), TagIndex('', 'tr', 1), TagIndex('', 'td', 1)),
		(ri, TagIndex('', 'p', 1)),
		(ri, TagIndex('', 'figure', 0), TagIndex('', 't', 0)),
		(ri, TagIndex('', 'figure', 0), TagIndex('', 'path', 0), TagIndex('', 'point', 1), TagIndex('', 'y', 0)),
		(ri,),
	)
	for path in paths:
		copy(source, destination, previous_path, path)
		previous_path = path

	buffer = StringIO()
	result.write(buffer, encoding='unicode', xml_declaration=True)
	assert buffer.getvalue() == xml
