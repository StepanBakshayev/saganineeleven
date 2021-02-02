from typing import BinaryIO, Mapping, Callable
from typing_extensions import Protocol

from .straighten import straighten, LexerProtocol
from .executor import delineate_boundaries, enforce
from xml.etree.ElementTree import parse as xml_parse, ElementTree

from .stringify import stringify, parse


class DocumentHandler(Protocol):
	text_nodes: Mapping
	convert: Callable
	processor_factory: Callable
	open: Callable
	iter: Callable
	create: Callable


class TemplateHandler(Protocol):
	Lexer: LexerProtocol
	render: Callable


def copy(source, destination):
	for chunk in iter(lambda: source.read(4*1024), None):
		destination.write(chunk)


def render(
	source: BinaryIO,
	destination: BinaryIO,
	document_handler: DocumentHandler,
	template_handler: TemplateHandler,
	context: dict
):
	with document_handler.create(destination) as archive:
		for source_file in document_handler.iter(source):
			with source_file, document_handler.open(archive, source_file.name) as destination_file:
				if source_file.suffix != '.xml':
					copy(source_file, destination_file)
					continue

				origin_tree = xml_parse(source_file)
				origin_root = origin_tree.getroot()
				content, line = straighten(origin_root, template_handler.Lexer, document_handler.text_nodes, document_handler.convert)
				if content is not content.template:
					copy(source_file, destination_file)
					continue

				boundaries = delineate_boundaries(origin_root, line)
				template = stringify(line)
				tape = parse(template_handler.render(template, context))
				builder = enforce(origin_root, tape, boundaries, document_handler.processor_factory)
				# XXX: etree does not store original parameters of xml.
				ElementTree(builder.destination).write(destination_file, encoding='utf-8', xml_declaration=True)
