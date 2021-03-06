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
import re
from dataclasses import astuple, dataclass
from itertools import chain
from pathlib import Path
from typing import MutableSequence
from xml.etree.ElementTree import Element, ElementTree
from xml.etree.ElementTree import parse as xml_parse

import pytest

from saganineeleven.contrib import docx, odt
from saganineeleven.contrib.django import Lexer, render
from saganineeleven.executor import (Route, TreeBuilder, delineate_boundaries,
                                     enforce, get_chain, get_root,
                                     make_ending_range, make_opening_range)
from saganineeleven.straighten import straighten
from saganineeleven.stringify import parse, stringify

fixture_path = Path(__file__).absolute().parent / 'fixture'


def test_get_root():
	assert get_root('abc', 'abc') == 'abc'
	assert get_root('a', 'b') == ''
	assert get_root('ac', 'ab') == 'a'
	assert get_root('0ac143', '0abi[wg') == '0a'
	assert get_root('', '0abi[wg') == ''
	assert get_root('0ac143', '') == ''


def parametrize_by_path(path):
	mapping = {'docx': docx, 'odt': odt}
	for xml in path.parent.glob(f'{path.stem}*.xml'):
		file_name, handler_name = xml.stem.split('.')
		if handler_name in mapping:
			yield pytest.param(xml, Lexer, mapping[handler_name], id=xml.name)


@dataclass(frozen=True)
class ElementData:
	tag: str
	attrib: dict
	text: str
	tail: str
	children: tuple

namespace_re = re.compile(r'^{(?P<namespace>.*?)}(?P<name>.*?)$')


def dataform(element: Element, namespaces: MutableSequence) -> ElementData:
	tag = element.tag
	match = namespace_re.match(tag)
	if match:
		namespace, name = match.group('namespace', 'name')
		if namespace not in namespaces:
			namespaces.append(namespace)
		ns = namespaces.index(namespace)
		tag = f'{{ns{ns}}}{name}'

	attrib = {}
	for key, value in element.attrib.items():
		match = namespace_re.match(key)
		if match:
			namespace, name = match.group('namespace', 'name')
			if namespace not in namespaces:
				namespaces.append(namespace)
			ns = namespaces.index(namespace)
			key = f'{{ns{ns}}}{name}'
		attrib[key] = value

	return ElementData(
		tag, attrib, element.text, element.tail,
		tuple(map(lambda e: dataform(e, namespaces), element))
	)


@pytest.mark.parametrize('path,lexer,handler', tuple(chain.from_iterable(map(parametrize_by_path, fixture_path.glob('*.odt')))))
def test_enforce(path, lexer, handler):
	with path.open('br') as template_stream, (path.parent / f'{path.stem}-rendered{path.suffix}').open('rb') as paragon_stream:
		origin_tree = xml_parse(template_stream)
		origin_root = origin_tree.getroot()
		content, line = straighten(origin_root, lexer, handler.text_nodes, handler.convert)
		assert content is content.template
		namespaces = []
		boundaries = delineate_boundaries(origin_root, line)

		template = stringify(line)
		tape = list(parse(render(template, {})))

		builder = enforce(origin_root, tape, boundaries, handler.processor_factory)
		data = dataform(builder.destination, namespaces)

		paragon_root = xml_parse(paragon_stream).getroot()
		paragon_data = dataform(paragon_root, namespaces)

		if data != paragon_data:
			from pprint import pprint
			with (Path().parent / f'{path.stem}-paragon.txt').open('tw') as out:
				pprint(astuple(paragon_data), stream=out, width=120)
			with (Path().parent / f'{path.stem}-data.txt').open('tw') as out:
				pprint(astuple(data), stream=out, width=120)
		assert data == paragon_data


def test_making_boundaries():
	with (fixture_path/'case_03.docx.xml').open('br') as stream:
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()

		previous_path = \
			(0, 4, 1, 1, 0, 0, 0, 7, 0, 0, 3, 0, 0, 1)
		path = \
			(0, 4, 1, 1, 1, 0, 0, 0, 0, 0, 1)
		root = get_root(previous_path, path)
		branch_index = len(root)

		chain = tuple(get_chain(origin_root, previous_path))
		routes = make_ending_range(chain, previous_path, branch_index+1)
		assert routes == (Route(branch=(0, 4, 1, 1, 0, 0, 0, 7, 0, 0), crossroad=(4,)),)

		routes = make_opening_range(path, branch_index+1)
		assert routes == (Route(branch=(0, 4, 1, 1, 1, 0, 0, 0, 0, 0), crossroad=(0,)),)


def test_delineate_boundaries():
	with (fixture_path/'case_03.docx.xml').open('br') as stream:
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()
		content, line = straighten(origin_root, Lexer, docx.text_nodes, docx.convert)
		assert content is content.template

		boundaries = delineate_boundaries(origin_root, line)

		assert set(boundaries.keys()) == {*range(1, 6)}

	with (fixture_path/'!case_03.odt.xml').open('br') as stream:
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()
		content, line = straighten(origin_root, Lexer, odt.text_nodes, odt.convert)
		assert content is content.template

		boundaries = delineate_boundaries(origin_root, line)

		assert boundaries[min(boundaries)].ending == (Route(branch=(), crossroad=(0, 1, 2)),)

	with (fixture_path/'objects_display.docx.xml').open('br') as stream:
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()
		content, line = straighten(origin_root, Lexer, docx.text_nodes, docx.convert)
		assert content is content.template

		boundaries = delineate_boundaries(origin_root, line)

		# XXX: wait for allowing <AlternateContent/>
		# assert boundaries[10].gap == Route(branch=(0,), crossroad=(5,))


@pytest.mark.parametrize('path,lexer,handler', tuple(chain.from_iterable(map(parametrize_by_path, fixture_path.glob('*.odt')))))
def test_continues(path, lexer, handler):
	with path.open('br') as template_stream:
		origin_tree = xml_parse(template_stream)
		origin_root = origin_tree.getroot()
		content, line = straighten(origin_root, lexer, handler.text_nodes, handler.convert)
		assert content is content.template
		namespaces = []
		origin_data = dataform(origin_root, namespaces)
		boundaries = delineate_boundaries(origin_root, line)

		builder = TreeBuilder(origin_root)
		previous_path = ()
		for pointer, text in line:
			if pointer.path == previous_path:
				continue

			if pointer.index in boundaries:
				boundary = boundaries[pointer.index]
				builder.copy(boundary.ending+(boundary.gap,)+boundary.opening)
			builder.copy((Route(pointer.path[:-1], pointer.path[-1:]),))

			previous_path = pointer.path

		boundary = boundaries[pointer.index+1]
		builder.copy(boundary.ending+(boundary.gap,)+boundary.opening)

		if dataform(builder.destination, namespaces) != origin_data:
			with (Path().parent / path.name).open('bw') as out:
				ElementTree(builder.destination).write(out, xml_declaration=True, encoding='utf-8')

		assert dataform(builder.destination, namespaces) == origin_data
