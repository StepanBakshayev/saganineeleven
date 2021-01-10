import sys
from pathlib import Path
from typing import List

from saganineeleven.contrib import docx, odt
from saganineeleven.contrib.django import Lexer, render
from saganineeleven.executor import enforce, play
from saganineeleven.straighten import straighten, Path as ElementPath
from saganineeleven.stringify import stringify, parse
from xml.etree.ElementTree import parse as xml_parse, Element

fixture_path = Path(__file__).absolute().parent


def make_x(root: Element, path: ElementPath) -> List[str]:
	if path is None:
		return 'None'
	parent = root
	chunks = ['.']
	for index in path:
		try:
			child = parent[index]
		except IndexError:
			chunks.append('?')
			break
		tag = child.tag
		count = 0
		for c in parent:
			if c.tag == tag:
				if c == child:
					break
				count += 1
		chunks.append(f'{tag}[{count}]')
		parent = child
	return chunks


def test():
	from ruamel.yaml import YAML
	yaml = YAML()
	for path, text_nodes, convert in (fixture_path/'case_01.docx.xml', docx.text_nodes, docx.convert),(fixture_path/'case_01.odt.xml', odt.text_nodes, odt.convert),:
		print(path.name)
		with path.open('br') as stream:
			content, text = straighten(stream, Lexer, text_nodes, convert)
			assert content is content.template
			template = stringify(text)
			result = render(template, {'show': True})
			stream.seek(0)
			origin_tree = xml_parse(stream)
			origin_root = origin_tree.getroot()
			log = []
			for op in play(origin_root, parse(result)):
				operation, value = next(iter(op.items()))
				if operation is operation.copy:
					value = [[value.start, make_x(origin_root, value.start)], [value.stop, make_x(origin_root, value.stop)]]
				log.append([operation.name, value])
			yaml.dump(log, sys.stdout)
			print('')

	assert False
