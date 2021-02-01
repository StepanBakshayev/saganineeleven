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
from itertools import count

from saganineeleven.straighten import ETC, ElementPointer
from saganineeleven.stringify import parse, stringify


def test():
	indexer = count(1)
	# XXX: Test does not require ElementPointer semantically correction.
	line = [
		(ElementPointer(path=(0, 0, 1,), index=next(indexer), is_constant=True), 'Hello,',),
		(ElementPointer(path=(0, 1, 1,), index=next(indexer), is_constant=False), '{{ name }}',),
		(ElementPointer(path=(0, 1, 1,), index=next(indexer), is_constant=False), f"!",),
		(ElementPointer(path=(0, 2, 1,), index=next(indexer), is_constant=True), f"I proud to greet some curios users.{ETC}",),
		(ElementPointer(path=(0, 4, 1,), index=next(indexer), is_constant=True), f"I want to sure I don't do it earlier.",),
		(ElementPointer(path=(0, 5, 1,), index=next(indexer), is_constant=False), f"Buy, ",),
		(ElementPointer(path=(0, 5, 1,), index=next(indexer), is_constant=False), '{{ name }}',),
		(ElementPointer(path=(0, 5, 1,), index=next(indexer), is_constant=False), '.',),
	]
	assert list(parse(stringify(line))) == line
