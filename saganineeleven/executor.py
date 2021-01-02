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
from enum import Enum
from xml.etree.ElementTree import ElementTree, parse
from .straighten import Element
from itertools import islice
from collections import namedtuple, deque
from typing import Tuple, Sequence

TagIndex = namedtuple('TagIndex', 'namespace name index')


# This is stupid copy. It does not do anything more. Function handling cycles search another place.
def mirror_nodes(source: ElementTree, destination: ElementTree, position: Tuple[TagIndex], target: Tuple[TagIndex]):
	# ветка содержит:
	# - оригинальный элемент, используется для выпотрощения детей
	# - клон, используется для операции append
	# опеределить сколько позиций нужно выкинуть с хвоста из ветки по разнице position-destination
	# начать с хвоста ветки отбрасывать элементы скидывая детей в клоны по порядку, пока не достигнется количество позиций.
	# начать заполнять ветку вглубь добавляя элементы в хвост и скидывая детей в дерево через клонов.
	# ВНИМАНИЕ! нужно уметь копировать целыми поддеревьями, потому что может быть p[2]/r[4], а следом p[5]/r[2]. Нужно скопировать поддерево p[3], p[4] и внутри p[5] ещё родственников до r[2].
	# position and target have:
	# - shared head
	# - different tail
	#
	pass

# plane:
# - text
# - element
# element:
# - direction
# - action

Plane = Enum('Plane', 'element text', module=__name__)
Direction = Enum('Direction', 'backward forward none', module=__name__)
Action = Enum('Action', 'clone skip none', module=__name__)


def enforce(origin: 'FileLikeObject', tape: Sequence[Tuple[Element, str]], middleware) -> list:
	"""
	Enforce contains those operations:
	- substitute variables
	- skip terminals
	- drop conditions body
	- clone partial or allocate place for new iteration of cycle body
	- mirror unchanged text in between

	Substitute requires managing text of element. Substitute can happen many times in one element or completely replace whole text.
	Skip terminals is a like substitute with zero length text. It opens door to ignore some nodes from origin.
	Drop conditions body requires accurate cut part of tree (partial clone in terms of this kind implementation) on boundary of different levels of hierarchy.
	Vague operation of cycle body requires look behind on origin tree and construct new branch for inside operation from above.
	Mirror unchanged text (in terms of template) is a suspect for variant of operations from above.
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

	# XXX: return to Element and rewrite it for structuted path.
	def restore_path(element: Element):
		for (namespace_id, tag), index in element.path:
			yield TagIndex(
				namespace=element.namespaces[namespace_id],
				name=tag,
				index=index,
			)

	log = []
	previous_path = ()
	# у нас есть орининал
	# у нас есть текущая позиция и изменения от неё.
	# у нас нет (как бы подразумевая только параметры функции и текущий рассматриваемый элемент)
	# информации как соотностися позиция текущая (в потенциально измененом Element.text) и ориганильном.
	# достаточно завести offset, что бы обозначить на чем оборвалась раскройка оригинального Element.text.
	# offset указывает на оригинальный Element.text.
	previous_offset = 0
	for element, text in tape:
		path = tuple(restore_path(element))
		if path == previous_path and element.offset != previous_offset:
			plane = Plane.text
			direction = Direction.none
			action = Action.none
		else:
			plane = Plane.element
			if path > previous_path:
				direction = Direction.forward
			else:
				direction = Direction.backward
			action = Action.clone
			if element.length and not text:
				action = Action.skip

		# markers:
		# [operation on elements]
		# - cycle: path is behind or equal, less then or equal
		# - false condition, nonterminal symbols, absentee system block: path is ahead, greater then
		# [operation on element.text]
		# - substitute, false conditions, absentee system block: path is equal
		#    - cycle: offset is behind or equal, less then or equal
		#    - false condition, nonterminal symbols, absentee system block: offset is ahead, greater then
		# location_changed = previous_path != path
		# if location_changed:
		# 	origin_offset = 0

		tag_repr = lambda t: f'{t.name}[{t.index}]'
		log.append([
			['/'.join(map(tag_repr, previous_path)), '/'.join(map(tag_repr, path))],
			[plane.name, direction.name, action.name],
			text,
		])
		previous_path = path
		previous_offset = element.offset

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
	return log
