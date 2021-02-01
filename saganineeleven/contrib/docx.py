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
"""
Docx is part of Office Open XML. It has specification ECMA-376 https://www.ecma-international.org/publications-and-standards/standards/ecma-376/.
It is available 5th edition of time of writing.
The specification contains formal machine readable description additional to text. There are XML Schema and RELAXNG.
RELAXNG is less known format, but it is not XML hence it is more humane.

Module need a few things to known about format. Extract xml, pack xml, represent text to render, compile peaces of rendered result.
The last thing is most important and complicated. It requires making design decisions about interpretation forth and back.

TEXT

Text is located in run (CT_R).

ECMA-376-Fifth-Edition-Parts-1-3-and-4.zip/ECMA-376, Fifth Edition, Part 1 - Fundamentals And Markup Language Reference.zip/OfficeOpenXML-RELAXNG-Strict.zip/OfficeOpenXML-RELAXNG-Strict.zip/wml.rnc

w_CT_R =
  attribute w:rsidRPr { w_ST_LongHexNumber }?,
  attribute w:rsidDel { w_ST_LongHexNumber }?,
  attribute w:rsidR { w_ST_LongHexNumber }?,
  w_EG_RPr?,
  w_EG_RunInnerContent

w_EG_RunInnerContent =
  element br { w_CT_Br }
  | element t { w_CT_Text }
  | element contentPart { w_CT_Rel }
  | element delText { w_CT_Text }
  | element instrText { w_CT_Text }
  | element delInstrText { w_CT_Text }
  | element noBreakHyphen { w_CT_Empty }
  | element softHyphen { w_CT_Empty }?
  | element dayShort { w_CT_Empty }?
  | element monthShort { w_CT_Empty }?
  | element yearShort { w_CT_Empty }?
  | element dayLong { w_CT_Empty }?
  | element monthLong { w_CT_Empty }?
  | element yearLong { w_CT_Empty }?
  | element annotationRef { w_CT_Empty }?
  | element footnoteRef { w_CT_Empty }?
  | element endnoteRef { w_CT_Empty }?
  | element separator { w_CT_Empty }?
  | element continuationSeparator { w_CT_Empty }?
  | element sym { w_CT_Sym }?
  | element pgNum { w_CT_Empty }?
  | element cr { w_CT_Empty }?
  | element tab { w_CT_Empty }?
  | element object { w_CT_Object }
  | element fldChar { w_CT_FldChar }
  | element ruby { w_CT_Ruby }
  | element footnoteReference { w_CT_FtnEdnRef }
  | element endnoteReference { w_CT_FtnEdnRef }
  | element commentReference { w_CT_Markup }
  | element drawing { w_CT_Drawing }
  | element ptab { w_CT_PTab }?
  | element lastRenderedPageBreak { w_CT_Empty }?

Characters are presented in w_CT_Text, but not all. There are break, tab and others represented with tags.
Also there are displayed information. For example, dayShort displays "the current date filtered through the specified date picture".
It is part of "textual represented content".
The task of converting tag content to text is restore sequence of displayed characters. It is not required to emulate rendering of Microsoft Word text processor.

BIG SURPRISE! There is cat in bag. You can see AlternateContent on any place. It is generic container for anything. It has some variants to match and fallback version.
It is hard to present in template, because textual representation may be different. Also there are side effects with placing side by side match options together.
"""
import re
from dataclasses import dataclass
from itertools import chain, count
from typing import Iterable, Tuple
from xml.etree.ElementTree import Element
from zipfile import ZIP_DEFLATED, ZipExtFile, ZipFile

from saganineeleven.straighten import Path

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
XML = 'http://www.w3.org/XML/1998/namespace'


text_nodes = {
	f'{{{W}}}r': -2,
	f'{{{V}}}textpath': -1,
	f'{{{M}}}r': -2,
}


def convert_vml(element: Element) -> Iterable[Tuple[Path, str]]:
	return ((), element.get('string')),


# w_EG_RunInnerContent =
ignore = set()
display = set()
include_text = set()
#   element br { w_CT_Br }
display.add(f'{{{W}}}br')
#   | element t { w_CT_Text }
include_text.add(f'{{{W}}}t')
#   | element contentPart { w_CT_Rel }
ignore.add(f'{{{W}}}contentPart')
#   | element delText { w_CT_Text }
ignore.add(f'{{{W}}}delText')
#   | element instrText { w_CT_Text }
ignore.add(f'{{{W}}}instrText')
#   | element delInstrText { w_CT_Text }
ignore.add(f'{{{W}}}delInstrText')
#   | element noBreakHyphen { w_CT_Empty }
display.add(f'{{{W}}}noBreakHyphen')
#   | element softHyphen { w_CT_Empty }?
display.add(f'{{{W}}}softHyphen')
#   | element dayShort { w_CT_Empty }?
display.add(f'{{{W}}}dayShort')
#   | element monthShort { w_CT_Empty }?
display.add(f'{{{W}}}monthShort')
#   | element yearShort { w_CT_Empty }?
display.add(f'{{{W}}}yearShort')
#   | element dayLong { w_CT_Empty }?
display.add(f'{{{W}}}dayLong')
#   | element monthLong { w_CT_Empty }?
display.add(f'{{{W}}}monthLong')
#   | element yearLong { w_CT_Empty }?
display.add(f'{{{W}}}yearLong')
#   | element annotationRef { w_CT_Empty }?
ignore.add(f'{{{W}}}annotationRef')
#   | element footnoteRef { w_CT_Empty }?
ignore.add(f'{{{W}}}footnoteRef')
#   | element endnoteRef { w_CT_Empty }?
ignore.add(f'{{{W}}}endnoteRef')
#   | element separator { w_CT_Empty }?
display.add(f'{{{W}}}separator')
#   | element continuationSeparator { w_CT_Empty }?
display.add(f'{{{W}}}continuationSeparator')
#   | element sym { w_CT_Sym }?
display.add(f'{{{W}}}sym')
#   | element pgNum { w_CT_Empty }?
display.add(f'{{{W}}}pgNum')
#   | element cr { w_CT_Empty }?
display.add(f'{{{W}}}cr')
#   | element tab { w_CT_Empty }?
display.add(f'{{{W}}}tab')
#   | element object { w_CT_Object }
ignore.add(f'{{{W}}}fldChar')
#   | element fldChar { w_CT_FldChar }
ignore.add(f'{{{W}}}fldChar')
#   | element ruby { w_CT_Ruby }
display.add(f'{{{W}}}ruby')
#   | element footnoteReference { w_CT_FtnEdnRef }
ignore.add(f'{{{W}}}footnoteReference')
#   | element endnoteReference { w_CT_FtnEdnRef }
ignore.add(f'{{{W}}}endnoteReference')
#   | element commentReference { w_CT_Markup }
ignore.add(f'{{{W}}}commentReference')
#   | element drawing { w_CT_Drawing }
ignore.add(f'{{{W}}}drawing')
#   | element ptab { w_CT_PTab }?
display.add(f'{{{W}}}ptab')
#   | element lastRenderedPageBreak { w_CT_Empty }?
display.add(f'{{{W}}}lastRenderedPageBreak')

# Special thing
ignore.add('{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent')

ignore = frozenset(ignore)
display = frozenset(display)
include_text = frozenset(include_text)


def convert_run(element: Element) -> Iterable[Tuple[Path, str]]:
	# w_CT_R =
	#   attribute w:rsidRPr { w_ST_LongHexNumber }?,
	#   attribute w:rsidDel { w_ST_LongHexNumber }?,
	#   attribute w:rsidR { w_ST_LongHexNumber }?,
	#   w_EG_RPr?,
	#   w_EG_RunInnerContent
	# R[un]Pr[operties]
	# w_EG_RPr = element rPr { w_CT_RPr }?
	start = 0
	first, *content = element
	if first.tag == f'{{{W}}}rPr':
		start += 1
	else:
		content = chain((first,), content)

	for i, child in zip(count(start), content):
		if child.tag in ignore:
			# explicit instruction
			continue
		elif child.tag in include_text:
			yield (i,), child.text
		elif child.tag in display:
			_, name = child.tag.split('}')
			# XXX: Template module should provide escape function to protect this textual representation from being interpreted as terminal.
			yield (i,), f'❬{name}∕❭'


def convert(element: Element) -> Iterable[Tuple[Path, str]]:
	handler = {
		f'{{{V}}}textpath': convert_vml,
		f'{{{W}}}r': convert_run,
		f'{{{M}}}r': convert_run,
	}.get(element.tag)
	if handler is None:
		raise RuntimeError(f'Unsupported element {element.tag}. Supported {set(text_nodes)}.', element, set(text_nodes))

	return handler(element)


@dataclass
class ElementAttribProcessor:
	destination_parent: Element
	destination: Element
	name: str

	def __post_init__(self):
		self.destination.attrib[self.name] = ''

	def feed(self, chunk):
		self.destination.attrib[self.name] += chunk

	def close(self):
		pass


char_tags_pattern = re.compile(r'([\t\n])')
char_tags_mapping = {
	'\t': f'{{{W}}}tab',
	'\n': f'{{{W}}}br',
}


@dataclass
class ElementTextProcessor:
	destination_parent: Element
	destination: Element

	def __post_init__(self):
		self.destination.text = ''
		self.destination.attrib.pop(f'{{{XML}}}space', None)

	def feed(self, chunk):
		is_special = True
		for bit in char_tags_pattern.split(chunk):
			is_special = not is_special
			if is_special:
				char_tag = self.destination.makeelement(char_tags_mapping[bit], {})
				self.destination_parent.append(char_tag)
				# w_EG_RunInnerContent =
				#   | element t { w_CT_Text }
				# w_CT_Text = s_ST_String, xml_space?
				# It is save to use copy method, because element `t` does not contain children and its one attribute is already cleared.
				new = self.destination.copy()
				new.text = ''
				self.destination_parent.append(new)
				if self.destination.text.startswith(' ') or self.destination.text.endswith(' '):
					self.destination.attrib[f'{{{XML}}}space'] = 'preserve'
				self.destination = new

			else:
				self.destination.text += bit

	def close(self):
		if self.destination.text == '':
			self.destination_parent.remove(self.destination)

		elif self.destination.text.startswith(' ') or self.destination.text.endswith(' '):
			self.destination.attrib[f'{{{XML}}}space'] = 'preserve'


def processor_factory(destination_parent: Element, destination: Element):
	kwargs = {'destination_parent': destination_parent, 'destination': destination}
	if destination.tag == f'{{{V}}}textpath':
		return ElementAttribProcessor(name='textpath', **kwargs)
	elif destination.tag in {f'{{{W}}}t', f'{{{M}}}t'}:
		return ElementTextProcessor(**kwargs)
	else:
		raise RuntimeError(f'Unsupported element {destination.tag}. Supported {set(text_nodes)}.', destination, set(text_nodes))
