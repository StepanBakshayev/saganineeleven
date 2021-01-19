import re
import sys
from collections import deque, namedtuple
from io import StringIO
from itertools import chain
from pathlib import Path
from typing import Sequence

import pytest
from devtools import debug

from saganineeleven.contrib.django import Lexer, render
from saganineeleven.contrib.docx import text_nodes, convert
from saganineeleven.contrib import docx, odt
from saganineeleven.executor import get_root, delineate_boundaries, fake_enforce, make_ending_range, get_chain, Route, \
	make_opening_range, TreeBuilder
from xml.etree.ElementTree import parse as xml_parse, ElementTree, Element

from saganineeleven.straighten import straighten
from saganineeleven.stringify import stringify, parse

fixture_path = Path(__file__).absolute().parent / 'fixture'


def test_get_root():
	assert get_root('abc', 'abc') == 'abc'
	assert get_root('a', 'b') == ''
	assert get_root('ac', 'ab') == 'a'
	assert get_root('0ac143', '0abi[wg') == '0a'
	assert get_root('', '0abi[wg') == ''
	assert get_root('0ac143', '') == ''


@pytest.mark.skip
def test_opening_container_none_copy_ending():
	sample = (
		{Operation.copy: Range((0, 0, 0, 0), (0, 0, 0))},  # XXX: optimize this for deep copy of (0, 0, 0).
		{Operation.copy: Range((0, 0, 2), (0, 1, 5))},
	)

	with (fixture_path/'paragraph_none_copy.docx.xml').open('br') as stream:
		content, text = straighten(stream, Lexer, text_nodes, convert)
		assert content is content.template
		template = stringify(text)
		result = render(template, {})
		stream.seek(0)
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()
		log = tuple(decode(origin_root, parse(result)))

		assert log == sample


@pytest.mark.skip
def test_opening_container_copy_none_ending():
	from ruamel.yaml import YAML
	yaml = YAML()

	sample = (
		{Operation.copy: Range((0, 0, 0, 0), (0, 0, 1))},  # XXX: optimize this for deep copy of (0, 0, 0).
		{Operation.copy: Range((0, 1), (0, 1, 5))},  # XXX: optimize this for deep copy of (0, 1).
	)

	with (fixture_path/'paragraph_copy_none.docx.xml').open('br') as stream:
		content, text = straighten(stream, Lexer, text_nodes, convert)
		assert content is content.template
		template = stringify(text)
		result = render(template, {})
		stream.seek(0)
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()
		log = []
		print('')
		print(repr(result))
		print('')
		for op in decode(origin_root, parse(result)):
			operation, value = next(iter(op.items()))
			if operation is operation.copy:
				value = [[repr(value.start), make_x(origin_root, value.start)], [repr(value.stop), make_x(origin_root, value.stop)]]
			yaml.dump([[operation.name, value]], sys.stdout)
			log.append(op)
			print('')

		assert tuple(log) == sample


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
		content, line = straighten(stream, Lexer, docx.text_nodes, docx.convert)
		assert content is content.template
		stream.seek(0)
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()

		boundaries = delineate_boundaries(origin_root, line)

		assert set(boundaries.keys()) == {*range(1, 8)}

	with (fixture_path/'case_03.odt.xml').open('br') as stream:
		content, line = straighten(stream, Lexer, odt.text_nodes, odt.convert)
		assert content is content.template
		stream.seek(0)
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()

		boundaries = delineate_boundaries(origin_root, line)

		assert boundaries[min(boundaries)].ending == (Route(branch=(), crossroad=(0, 1, 2)),)


ElementData = namedtuple('ElementData', 'tag attrib text tail children', module=__name__)
namespace_re = re.compile(r'^{(?P<namespace>.*?)}(?P<name>.*?)$')


def dataficay(element: Element, namespaces: Sequence) -> ElementData:
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
		tuple(map(lambda e: dataficay(e, namespaces), element._children))
	)


def parametrize_by_path(path):
	for xml in path.parent.glob(f'{path.stem}*.xml'):
		file_name, handler_name = xml.stem.split('.')
		yield pytest.param(xml, Lexer, {'docx': docx, 'odt': odt}[handler_name], id=xml.name)


@pytest.mark.parametrize('path,lexer,handler', tuple(*map(parametrize_by_path, fixture_path.glob('*.odt'))))
def test_continues(path, lexer, handler):
	with path.open('br') as stream:
		content, line = straighten(stream, lexer, handler.text_nodes, handler.convert)
		assert content is content.template
		stream.seek(0)
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()
		namespaces = []
		origin_data = dataficay(origin_root, namespaces)
		boundaries = delineate_boundaries(origin_root, line)

		builder = TreeBuilder(origin_root)
		previous_path = ()
		for pointer, text in line:
			if pointer.path == previous_path:
				continue

			previous_path = pointer.path
			if pointer.index in boundaries:
				boundary = boundaries[pointer.index]
				for route in chain(boundary.ending, boundary.gap, boundary.opening):
					builder.insert(route)
			builder.insert(Route(pointer.path[:-1], (pointer.path[-1],)))

		boundary = boundaries[pointer.index+1]
		for route in chain(boundary.ending, boundary.gap, boundary.opening):
			builder.insert(route)

		assert dataficay(builder.destination, namespaces) == origin_data
