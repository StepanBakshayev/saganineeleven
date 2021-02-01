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
from io import StringIO

import pytest

from saganineeleven.contrib.django import Lexer
from saganineeleven.contrib.docx import convert, text_nodes
from saganineeleven.straighten import (ETC, ContentType, ShadowElement,
                                       straighten)


@pytest.mark.skip(reason='until make decision about compress in pipeline')
def test_all_terminals_present():
	xml = StringIO("""<?xml version="1.0" encoding="UTF-8"?>
		<w:document xmlns:o="urn:schemas-microsoft-com:office:office"
			xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
			<w:body>
				<w:p>
					<w:pPr>
						<w:pStyle w:val="Normal"/>
						<w:bidi w:val="0"/>
						<w:jc w:val="left"/>
						<w:rPr></w:rPr>
					</w:pPr>
					<w:r>
						<w:rPr></w:rPr>
						<w:t>Hello,</w:t>
					</w:r>
				</w:p>
				<w:p>
					<w:pPr>
						<w:pStyle w:val="Normal"/>
						<w:bidi w:val="0"/>
						<w:jc w:val="left"/>
						<w:rPr></w:rPr>
					</w:pPr>
					<w:r>
						<w:rPr></w:rPr>
						<w:t>{{ name }}!</w:t>
					</w:r>
				</w:p>
				<w:p>
					<w:pPr>
						<w:pStyle w:val="Normal"/>
						<w:bidi w:val="0"/>
						<w:jc w:val="left"/>
						<w:rPr></w:rPr>
					</w:pPr>
					<w:r>
						<w:rPr></w:rPr>
						<w:t>I proud to greet some curios users.</w:t>
					</w:r>
				</w:p>
				<w:p>
					<w:pPr>
						<w:pStyle w:val="Normal"/>
						<w:bidi w:val="0"/>
						<w:jc w:val="left"/>
						<w:rPr></w:rPr>
					</w:pPr>
					<w:r>
						<w:rPr></w:rPr>
						<w:t>There are some possible optimization for a future.</w:t>
					</w:r>
				</w:p>
				<w:p>
					<w:pPr>
						<w:pStyle w:val="Normal"/>
						<w:bidi w:val="0"/>
						<w:jc w:val="left"/>
						<w:rPr></w:rPr>
					</w:pPr>
					<w:r>
						<w:rPr></w:rPr>
						<w:t>I want to sure I don't do it earlier.</w:t>
					</w:r>
				</w:p>
				<w:p>
					<w:pPr>
						<w:pStyle w:val="Normal"/>
						<w:bidi w:val="0"/>
						<w:jc w:val="left"/>
						<w:rPr></w:rPr>
					</w:pPr>
					<w:r>
						<w:rPr></w:rPr>
						<w:t>Buy, {{ name }}.</w:t>
					</w:r>
				</w:p>
			</w:body>
		</w:document>
	""")
	template, text = straighten(xml, Lexer, text_nodes, convert)
	assert template is ContentType.template
	template_element = [
		('Hello,', (ShadowElement(path=(0, 0, 1,), atom=-1, representation_length=6, offset=0, length=6, is_constant=True),),),
		('{{ name }}', (ShadowElement(path=(0, 1, 1,), atom=-1, representation_length=11, offset=0, length=10, is_constant=False), ShadowElement(path=(0, 1, 1), atom=-1, representation_length=11, offset=10, length=0, is_constant=False),)),
		(f"!I proud to greet some curios users.{ETC}I want to sure I don't do it earlier.Buy, ",
		 (ShadowElement(path=(0, 1, 1,), atom=-1, representation_length=11, offset=10, length=1, is_constant=False), ShadowElement(path=(0, 2, 1,), atom=-1, representation_length=35, offset=0, length=35+len(ETC), is_constant=True), ShadowElement(path=(0, 4, 1,), atom=-1, representation_length=37, offset=0, length=37, is_constant=True), ShadowElement(path=(0, 5, 1,), atom=-1, representation_length=16, offset=0, length=5, is_constant=False))),
		('{{ name }}', (ShadowElement(path=(0, 5, 1,), atom=-1, representation_length=16, offset=5, length=10, is_constant=False), ShadowElement(path=(0, 5, 1), atom=-1, representation_length=16, offset=15, length=0, is_constant=False),)),
		('.', (ShadowElement(path=(0, 5, 1,), atom=-1, representation_length=16, offset=15, length=1, is_constant=False),)),
	]
	assert list(map(lambda t: (str(t), t.elements), text)) == template_element
