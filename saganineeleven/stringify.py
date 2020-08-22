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
from xml.etree import ElementTree


def stringify(
	file
) -> str:
	text = []
	for (event, element) in ElementTree.iterparse(file):
		tree = element.iter()
		# pull root. It is node by self.
		next(tree)
		if next(tree, None) is not None:
			continue
		if element.text is None:
			continue
		print(event, element, element.text)
		text.append(element.text or '')
	return ''.join(text)
