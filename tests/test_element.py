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
from dataclasses import replace

from saganineeleven.straighten import Element, elementstr


def test_elementstr_single():
	element = Element((0, 'r'), ('',), 0, 10)

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

	# based on regression in lexer (?).
	estr = elementstr("{% if c != 'c' %}character {{ c }}{% endif %}")
	estr.elements = Element((((0, 'root'), 0), ((0, 'p'), 1)), ('',), 0, 0),
	assert estr[0:17] == "{% if c != 'c' %}"
	assert estr[17:27] == "character "


def test_elementstr_many():
	element = Element((0, 'r'), ('',), 0, 10)

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
	element = Element((0, 'r'), ('',), 0, 10)

	empty_empty = elementstr()
	empty_empty += elementstr()
	assert empty_empty == str() + str()

	something_something = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	something_something.elements = element,
	something_something += something_something
	assert something_something == str(''.join(map(chr, range(ord('0'), ord('0')+element.length)))) + str(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	assert something_something.elements == (element,) + (element,)
