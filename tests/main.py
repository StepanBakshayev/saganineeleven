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
#
# PYTHONPATH=`pwd` python tests/main.py
#
import saganineeleven
import saganineeleven.stringify
import saganineeleven.contrib
import saganineeleven.contrib.django
import saganineeleven.contrib.docx
import saganineeleven.contrib.odt
from pathlib import Path
from dataclasses import replace
from xml.etree.ElementTree import parse


def test_elementstr_single():
	element = saganineeleven.stringify.Element('///', 0, 10, ())
	elementstr = saganineeleven.stringify.elementstr

	estr = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	estr.elements = element,

	beginning = estr[:3]
	assert beginning == str(estr)[:3]
	assert beginning.elements == (replace(element, length=3),)

	middle = estr[4:7]
	assert middle == str(estr)[4:7]
	assert middle.elements == (replace(element, offset=4, length=3),)

	end = estr[7:]
	assert end == str(estr)[7:]
	assert end.elements == (replace(element, offset=7, length=3),)


def test_elementstr_many():
	element = saganineeleven.stringify.Element('///', 0, 10, ())
	elementstr = saganineeleven.stringify.elementstr

	estr = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length)))*3)
	estr.elements = (element,) * 3

	cut_cut_drop = estr[3:14]
	assert cut_cut_drop == str(estr)[3:14]
	assert cut_cut_drop.elements == (replace(element, offset=3, length=7), replace(element, length=4)), (cut_cut_drop.elements, cut_cut_drop)

	cut_leave_cut = estr[3:-3]
	assert cut_leave_cut == str(estr)[3:-3]
	assert cut_leave_cut.elements == (replace(element, offset=3, length=7), element, replace(element, length=7))

	drop_cut_cut = estr[14:-3]
	assert drop_cut_cut == str(estr)[14:-3]
	assert drop_cut_cut.elements == (replace(element, offset=4, length=6), replace(element, length=7)), drop_cut_cut.elements


def test_elementstr_iadd():
	element = saganineeleven.stringify.Element('///', 0, 10, ())
	elementstr = saganineeleven.stringify.elementstr

	empty_empty = elementstr()
	empty_empty += elementstr()
	assert empty_empty == str() + str()

	something_something = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	something_something.elements = element,
	something_something += something_something
	assert something_something == str(''.join(map(chr, range(ord('0'), ord('0')+element.length)))) + str(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	assert something_something.elements == (element,) + (element,)


def test_element_pack():
	elements = (
		saganineeleven.stringify.Element('abc', 0, 10, ('n0', 'n1')),
		saganineeleven.stringify.Element('', 1, 0, ()),
		saganineeleven.stringify.Element('a'*255*2, 1, 0, ('n0'*255*2, 'n1'*255*2)),
	)

	for element in elements:
		buffer = element.pack()
		unpacked_element = saganineeleven.stringify.Element.unpack(buffer)
		assert element == unpacked_element, (element, unpacked_element)


test_elementstr_single()
test_elementstr_many()
test_elementstr_iadd()
test_element_pack()


files = (
	(saganineeleven.contrib.docx, saganineeleven.contrib.django.Lexer, saganineeleven.contrib.django.render, 'substitute_variable.docx', {'variable': '♟ ♔'}),
	(saganineeleven.contrib.odt, saganineeleven.contrib.django.Lexer, saganineeleven.contrib.django.render, 'substitute_variable.odt', {'variable': '♟ ♔'}),
)
root = Path(__file__).absolute().parent

for handler, Lexer, render, name, context in files:
	with (root / name).open('rb') as source:
		print(source)
		for file in handler.iter(source):
			print(file)
			content_type, text = saganineeleven.stringify.stringify(file, Lexer)
			if content_type is content_type.template:
				print(f'{text!r}')
				print('.')
				print(f'{render(text, context)!r}')
			else:
				print('plain text')
			# file.seek(0)
			# tree = parse(file)
			# for part in text:
			# 	for element in part.elements:
			# 		found = tree.findall(element.path, {f'n{i}': name for i, name in enumerate(element.namespaces)})
			# 		assert found, element.path
			# 		assert len(found) == 1
			print()
		print('--')
