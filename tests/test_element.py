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

from saganineeleven.straighten import ETC, ShadowElement, compress, elementstr


def test_elementstr_single():
	element = ShadowElement((0, 0), -1, 10, 0, 10, True)

	estr = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	estr.elements = element,

	beginning = estr[:3]
	assert beginning == str(estr)[:3]
	assert beginning.elements == (replace(element, length=3, is_constant=False),)

	middle = estr[4:7]
	assert middle == str(estr)[4:7]
	assert middle.elements == (replace(element, offset=4, length=3, is_constant=False),)

	end = estr[7:]
	assert end == str(estr)[7:]
	assert end.elements == (replace(element, offset=7, length=3, is_constant=False),)

	# based on regression in lexer (?).
	estr = elementstr("{% if c != 'c' %}character {{ c }}{% endif %}")
	estr.elements = ShadowElement((0, 0), -1, len(estr), 0, len(estr), is_constant=True),
	assert estr[0:17] == "{% if c != 'c' %}"
	assert estr[17:27] == "character "


def test_elementstr_many():
	element = ShadowElement((0, 0), -1, 10, 0, 10, True)

	estr = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length)))*3)
	estr.elements = (element,) * 3

	cut_cut_drop = estr[3:14]
	assert cut_cut_drop == str(estr)[3:14]
	assert cut_cut_drop.elements == (replace(element, offset=3, length=7, is_constant=False), replace(element, length=4, is_constant=False))

	cut_leave_cut = estr[3:-3]
	assert cut_leave_cut == str(estr)[3:-3]
	assert cut_leave_cut.elements == (replace(element, offset=3, length=7, is_constant=False), element, replace(element, length=7, is_constant=False))

	drop_cut_cut = estr[14:-3]
	assert drop_cut_cut == str(estr)[14:-3]
	assert drop_cut_cut.elements == (replace(element, offset=4, length=6, is_constant=False), replace(element, length=7, is_constant=False))


def test_elementstr_iadd():
	element = ShadowElement((0, 0), -1, 10, 0, 10, True)

	empty_empty = elementstr()
	empty_empty += elementstr()
	assert empty_empty == str() + str()

	something_something = elementstr(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	something_something.elements = element,
	something_something += something_something
	assert something_something == str(''.join(map(chr, range(ord('0'), ord('0')+element.length)))) + str(''.join(map(chr, range(ord('0'), ord('0')+element.length))))
	assert something_something.elements == (element,) + (element,)


def test_compress():
	estr = elementstr("!I proud to greet some curios users.There are some possible optimization for a future.I want to sure I don't do it earlier.Buy, ")
	estr.elements = (
		ShadowElement((0, 1), atom=-1, representation_length=11, offset=10, length=1, is_constant=False),
		ShadowElement((0, 2), atom=-1, representation_length=35, offset=0, length=35, is_constant=True),
		ShadowElement((0, 3), atom=-1, representation_length=50, offset=0, length=50, is_constant=True),
		ShadowElement((0, 4), atom=-1, representation_length=37, offset=0, length=37, is_constant=True),
		ShadowElement((0, 5), atom=-1, representation_length=16, offset=0, length=5, is_constant=False),
	)
	compressed = compress(estr)
	assert str(compressed) == f"!I proud to greet some curios users.{ETC}I want to sure I don't do it earlier.Buy, "
	assert compressed.elements == (
		ShadowElement((0, 1), atom=-1, representation_length=11, offset=10, length=1, is_constant=False),
		ShadowElement((0, 2), atom=-1, representation_length=35, offset=0, length=35+len(ETC), is_constant=True),
		ShadowElement((0, 4), atom=-1, representation_length=37, offset=0, length=37, is_constant=True),
		ShadowElement((0, 5), atom=-1, representation_length=16, offset=0, length=5, is_constant=False),
	)
