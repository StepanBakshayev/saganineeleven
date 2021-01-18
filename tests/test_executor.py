import sys
from collections import deque
from io import StringIO
from pathlib import Path

import pytest
from devtools import debug

from saganineeleven.contrib.django import Lexer, render
from saganineeleven.contrib.docx import text_nodes, convert
from saganineeleven.executor import get_root, delineate_boundaries, fake_enforce
from xml.etree.ElementTree import parse as xml_parse, ElementTree

from saganineeleven.straighten import straighten
from saganineeleven.stringify import stringify, parse

fixture_path = Path(__file__).absolute().parent / 'fixture'

def test_get_root():
	assert get_root('a', 'b') == ''
	assert get_root('ac', 'ab') == 'a'
	assert get_root('0ac143', '0abi[wg') == '0a'


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


# def test_make_opening_range():
# 	make_opening_range((0, 1, 2, 1, 1), )

def test_boundaries():
	with (fixture_path/'case_03.docx.xml').open('br') as stream:
		content, line = straighten(stream, Lexer, text_nodes, convert)
		assert content is content.template
		stream.seek(0)
		origin_tree = xml_parse(stream)
		origin_root = origin_tree.getroot()

		debug(line)
		boundaries = delineate_boundaries(origin_root, line)
		builder = fake_enforce(origin_root, line, boundaries)
		debug(builder)
		buffer = StringIO()
		print('')
		with (Path()/'result.docx.xml').open('bw') as stream:
			ElementTree(builder.destination).write(stream, encoding='utf-8', xml_declaration=True)

	assert False
