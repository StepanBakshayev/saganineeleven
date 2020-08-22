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
import saganineeleven
import saganineeleven.stringify
import saganineeleven.contrib
import saganineeleven.contrib.docx
import saganineeleven.contrib.odt
from pathlib import Path

files = (
	(saganineeleven.contrib.docx, 'hello.docx'),
	(saganineeleven.contrib.odt, 'hello.odt'),
)
root = Path(__file__).absolute().parent

for handler, name in files:
	with (root / name).open('rb') as source:
		print(source)
		for file in handler.iter(source):
			print(file)
			text = saganineeleven.stringify.stringify(file)
			print(text)
			print()
		print('--')
