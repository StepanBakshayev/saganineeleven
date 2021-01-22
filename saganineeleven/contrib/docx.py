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
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZIP_DEFLATED, ZipExtFile


CHUNK_SIZE = max(256 * 1024, ZipExtFile.MIN_READ_SIZE) # in bytes
ENCODING = 'UTF-8'


def iter(source):
	with ZipFile(source, 'r') as file:
		yield from map(file.open, file.infolist())


def create(path):
	return ZipFile(path, 'w', compression=ZIP_DEFLATED)


def open(archive, path):
	return archive.open(path, 'w')


W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
V = 'urn:schemas-microsoft-com:vml'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


text_nodes = {
	f'{{{W}}}r': -1,
	f'{{{V}}}textpath': 0,
	f'{{{M}}}r': -1,
}


def convert(element: Element) -> str:
	if element.tag == f'{{{V}}}textpath':
		return element.get('string')
	elif element.tag not in {f'{{{W}}}r', f'{{{M}}}r'}:
		raise RuntimeError(f'Unsupported element {element.tag}. Supported {set(text_nodes)}.', element, set(text_nodes))
	chunks = []
	for child in element:
		if child.tag.endswith('}t'):
			chunks.append(child.text)
		# Each other case is cosmetic.
		elif child.tag.endswith(f'{{{W}}}tab'):
			chunks.append('\t')
		elif child.tag.endswith(f'{{{W}}}br'):
			chunks.append('\n')

	return ''.join(chunks)
