import json
from enum import Enum
from itertools import tee
from pathlib import Path
from importlib import import_module

import typer

from saganineeleven import render as do_render

application = typer.Typer()

DOCUMENT_HANDLER = Enum('DocumentHandlerType', zip(*tee('docx'.split(' '))), module=__name__)
TEMPLATE_HANDLER = Enum('DocumentHandlerType', zip(*tee('django'.split(' '))), module=__name__)


@application.command()
def render(
	source: Path=typer.Option(...),
	destination: Path=typer.Option(...),
	document_handler: DOCUMENT_HANDLER=typer.Option(...),
	template_handler: TEMPLATE_HANDLER=typer.Option(...),
	context: str=typer.Option(...)
):
	with source.open('rb') as source_file, destination.open('wb') as destination_file:
		do_render(
			source_file,
			destination_file,
			import_module(f'saganineeleven.contrib.{document_handler.value}'),
			import_module(f'saganineeleven.contrib.{template_handler.value}'),
			json.loads(context)
		)


if __name__ == '__main__':
	application()
