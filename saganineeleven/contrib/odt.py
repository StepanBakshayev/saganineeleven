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
from zipfile import ZipFile, ZIP_DEFLATED, ZipExtFile


CHUNK_SIZE = max(256 * 1024, ZipExtFile.MIN_READ_SIZE) # in bytes
ENCODING = 'UTF-8'


def iter(source):
	with ZipFile(source, 'r') as file:
		yield from map(file.open, filter(lambda i: i.filename.endswith('.xml'), file.infolist()))


def create(path):
	return ZipFile(path, 'w', compression=ZIP_DEFLATED)


def open(archive, path):
	return archive.open(path, 'w')
