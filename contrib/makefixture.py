#!/usr/bin/env python3
import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from tempfile import NamedTemporaryFile
from xml.etree.ElementTree import ElementTree

from saganineeleven.contrib import odt, docx


INDENT = '  '


def travel_depth(element, level=0):
	if element.text or element.tail or not len(element):
		return
	element.text = '\n' + INDENT * level
	for child in element:
		travel_depth(child, level+1)
		child.tail = '\n' + INDENT * level
	child.tail = '\n' + INDENT * (level - 1)


def parse_and_format(file):
	tree = ElementTree(file=file)
	travel_depth(tree.getroot())
	return tree


def main(options):
	source_path = (Path() / options.path).resolve()
	with NamedTemporaryFile(suffix='.docx') as docx_file:
		converter = 'unoconv', '--format=docx', f'--output={docx_file.name}', str(source_path.resolve())
		run(converter, check=True)

		for handler, file_name, content_name in (odt, str(source_path), 'content.xml'), (docx, docx_file.name, 'word/document.xml'):
			files = handler.iter(file_name)
			content_file = next(filter(lambda f: f.name == content_name, files))
			tree = parse_and_format(content_file)
			with (source_path.parent/f'{source_path.stem}.{handler.__name__.split(".")[-1]}.xml').open('wb') as stream:
				tree.write(stream, xml_declaration=True, encoding='utf-8')


parser = ArgumentParser()
parser.add_argument('path', help='Path to odt template.')


if __name__ == '__main__':
	arguments = parser.parse_args()
	main(arguments)
