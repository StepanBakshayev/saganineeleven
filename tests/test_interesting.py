import sys
from pathlib import Path

from saganineeleven.contrib.django import Lexer, render
from saganineeleven.executor import enforce
from saganineeleven.straighten import straighten
from saganineeleven.stringify import stringify, parse

fixture_path = Path(__file__).absolute().parent

def test():
	from ruamel.yaml import YAML
	yaml = YAML()
	for path in (fixture_path/'case_01.docx.xml'),:
		print(path.name)
		with path.open('br') as stream:
			content, text = straighten(stream, Lexer)
			assert content is content.template
			template = stringify(text)
			result = render(template, {'show': True})
			stream.seek(0)
			tree, log = enforce(stream, parse(result), None)
			yaml.dump(log, sys.stdout)
			print('')
			with open(Path(__file__).absolute().parent.parent / f'{path.stem}.rendered.xml', 'bw') as stream:
				tree.write(stream, encoding='utf-8', xml_declaration=True)
	assert False