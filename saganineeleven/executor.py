# Copyright 2020 Stepan Bakshayev
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
from xml.etree.ElementTree import ElementTree, parse
from .stringify import element_re, Element
from itertools import islice
from collections import namedtuple, deque
import re
from typing import Tuple

TagIndex = namedtuple('TagIndex', 'namespace name index')


def fill_gap(branch: deque, position: Tuple[TagIndex], destination: Tuple[TagIndex]):
	# ветка содержит:
	# - оригинальный элемент, используется для выпотрощения детей
	# - клон, используется для операции append
	# опеределить сколько позиций нужно выкинуть с хвоста из ветки по разнице position-destination
	# начать с хвоста ветки отбрасывать элементы скидывая детей в клоны по порядку, пока не достигнется количество позиций.
	# начать заполнять ветку вглубь добавляя элементы в хвост и скидывая детей в дерево через клонов.
	# ВНИМАНИЕ! нужно уметь копировать целыми поддеревьями, потому что может быть p[2]/r[4], а следом p[5]/r[2]. Нужно скопировать поддерево p[3], p[4] и внутри p[5] ещё родственников до r[2].
	pass


def enforce(origin: 'FileLikeObject', tape: str, middleware) -> ElementTree:
	"""
	Copy nodes from origin. Replace text with rendered variables.
	"""
	# XXX: It is memory consumption here.
	origin_tree = parse(origin)

	# XXX: It is just for starting implementation to copy root.
	# XXX: It is bad design to copy each element from one tree to another.
	result_tree = ElementTree(origin_tree.getroot().copy())
	# Free tinking. Postpone ideas by finishing cycling.
	# TreeBuilder is used to construct ElementTree instead of incremental dump as I think at fist.
	# XXX: We don't use or rely of nodes in memory. Consider writing incremental dump against xml.etree.ElementTree._serialize_xml.
	# XXX: We don't need parse origin neither. We copy substring from original to result.

	def iterate(tape):
		in_element = True
		element_dump = None
		# XXX: There are big memory consumption and big cpu utilization.
		for bit in islice(element_re.split(tape), 1, None):
			if in_element:
				element_dump = bit
			else:
				yield Element.unpack(element_dump.encode('utf-8', 'surrogateescape')), bit
				element_dump = None
			in_element = not in_element

	# XXX: return to Element and rewrite it for structuted path.
	path_re = re.compile(r'^n(?P<namespace>\d+):(?P<name>[^\[]+)\[(?P<index>\d+)\]$')
	def parse_path(string, namespaces):
		root, *parts = string.split('/')
		for part in parts:
			kwargs = path_re.match(part).groupdict()
			yield TagIndex(
				namespace=namespaces[int(kwargs['namespace'])],
				name=kwargs['name'],
				index=int(kwargs['index'])-1,
			)

	previous_path = ()
	# у нас есть орининал
	# у нас есть текущая позиция и изменения от неё.
	# у нас нет (как бы подразумевая только параметры функции и текущий рассматриваемый элемент)
	# информации как соотностися позиция текущая (в потенциально измененом Element.text) и ориганильном.
	# достаточно завести offset, что бы обозначить на чем оборвалась раскройка оригинального Element.text.
	# offset указывает на оригинальный Element.text.
	origin_offset = 0
	location_changed = False
	# получили элемент
	for element, text in iterate(tape):
	# находимся ли мы в том же элементе?
		path = tuple(parse_path(element.path, element.namespaces))
		location_changed = previous_path != path
		if location_changed:
			origin_offset = 0

		# fill_gap()

		# Можно использовать ссылки на элементы в памяти и прям туда фигачить.
		# Element.append
		previous_path = path

	# че-то нужно сделать
	# если да, тогда произвести подстановку текста.
	# подстановка текста состоит из ???

	# для вставки достаточно сканировать поседовательно исходник
	# для условного вывода достаточно сканировать последовательно исходик
	# для циклов нет
	# А в чем проблема? нужно трекать состояние куда вставлять очередную ветку элементов и сопоставлять их с текущим
	#
	# Вывод: для циклов необходимо отталкиваться от ленты. Для остальных операций - от исходника.
	# Изначальная идея - это создать НЕОБХОДИМУЮ ИНФРАСТРУКТУРУ и для неё выполнить простейшую операцию: замена.
	#
	# Инфрастуктура включает в себя
	# - копирование элементов на основе ленты
	# - отладка копироания через инъекцию специфики (docx)
	return result_tree
