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
from xml.etree.ElementTree import ElementTree, parse, Element
from .straighten import namespace_re
from itertools import islice
from collections import namedtuple, deque
from typing import Tuple, Sequence, Deque

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


# XXX: copy-paste from Element.copy partially.
def element_copy(element: Element) -> Element:
	new = element.makeelement(element.tag, element.attrib)
	new.text = element.text
	new.tail = element.tail
	return new


def element_deepcopy(element: Element):
	new = element_copy(element)
	for child in element:
		new.append(element_deepcopy(child))
	return new


def find(source: Element, tag_index: TagIndex) -> Tuple[int, Element]:
	count = 0
	tag = tag_index.name
	if tag_index.namespace:
		tag = f'{tag_index.namespace}{tag}'
	for index, child in enumerate(source):
		if child.tag == tag:
			if count == tag_index.index:
				return index, child
			count += 1
	raise ValueError(f'{tag_index!r} was not found in {source.tag}', tag_index, source)


def copy(source: Deque[Element], destination: Deque[Element], position: Tuple[TagIndex, ...], target: Tuple[TagIndex, ...]):
	# require root to present
	assert destination
	assert position
	assert target
	# require root to equal
	assert position[0] == target[0]
	# require sync between branch position
	assert len(destination) == len(position), (destination, position)
	# require different position and target
	assert position != target

	root_index = 0
	for root_index, (current_pointer, target_pointer) in enumerate(zip(position, target)):
		if current_pointer != target_pointer:
			root_index -= 1
			break

	root_node = source[root_index]
	branch_index = root_index + 1
	position_index = 0

	# stairs to the top: copy successors siblings on each level and lift up
	# from TagIndex.index to last child on each level.
	if (branch_index + 1) < len(position):
		for index in range(len(position)-1, branch_index, -1):
			source.pop()
			destination.pop()
			parent = source[-1]
			position_index, _ = find(parent, position[index])
			for successor in parent[position_index+1:]:
				parent.append(element_deepcopy(successor))
		assert len(source) == len(destination) == (branch_index + 1), (source, destination, branch_index)

	# floor: cross border between root_index+1 of position and target
	if branch_index < len(position):
		position_index, _ = find(root_node, position[branch_index])
		position_index += 1
		source.pop()
		destination.pop()
	assert len(source) == len(destination) == (root_index + 1), (source, destination, root_index)
	if branch_index < len(target):
		target_index, target_node = find(root_node, target[branch_index])
		target_parent = destination[-1]
		for successor in root_node[position_index:target_index]:
			new = element_deepcopy(successor)
			target_parent[-1].append(new)
		new = element_copy(target_node)
		target_parent.append(new)
		source.append(target_node)
		destination.append(new)
		assert len(source) == len(destination) == (branch_index + 1), (source, destination, branch_index)

	# stairs to the bottom: copy predecessors siblings on each level and go down
	# from 0 to TagIndex.index on each level
	if (branch_index + 1) < len(target):
		for index in range(branch_index+1, len(target), 1):
			parent = source[-1]
			target_parent = destination[-1]
			target_index, target_node = find(parent, target[index])
			for predecessor in parent[0:target_index]:
				target_parent.append(element_deepcopy(predecessor))
			new = element_copy(target_node)
			target_parent.append(new)
			source.append(target_node)
			destination.append(new)

	assert len(source) == len(destination) == len(target), (source, destination, target)


# XXX: This is not so easy in real life. MS Word encode tabs, newlines with special tag.
def append(place: Element, text):
	place.text += text


# plane:
# - text
# - element
# element:
# - direction
# - action

Plane = Enum('Plane', 'element text', module=__name__)
Direction = Enum('Direction', 'backward forward none', module=__name__)
Action = Enum('Action', 'copy skip none', module=__name__)


def enforce(origin: 'FileLikeObject', tape: Sequence[Tuple[Element, str]], middleware) -> Tuple[ElementTree, list]:
	"""
	Enforce contains those operations:
	- substitute variables
	- skip terminals
	- drop conditions body
	- copy partial or allocate place for new iteration of cycle body
	- mirror unchanged text in between

	Substitute requires managing text of element. Substitute can happen many times in one element or completely replace whole text.
	Skip terminals is a like substitute with zero length text. It opens door to ignore some nodes from origin.
	Drop conditions body requires accurate cut part of tree (partial copy in terms of this kind implementation) on boundary of different levels of hierarchy.
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
	origin_root = origin_tree.getroot()
	result_root = element_copy(origin_root)
	result = ElementTree(result_root)
	element_tag = result_root.tag
	namespace, tagname = '', element_tag
	match = namespace_re.match(element_tag)
	if match:
		namespace, tagname = match.group('namespace', 'tagname')
	destination = deque((result_root,))
	source = deque((origin_root,))
	previous_path = TagIndex(namespace, tagname, 0),
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
			action = Action.copy
			if element.length and not text:
				action = Action.skip

		if plane is Plane.element:
			if action is Action.copy:
				copy(source, destination, previous_path, path)
			elif action is Action.skip:
				# explicit handling.
				# XXX: call middleware for handling skipping. copy will be handling too in near future.
				pass
			else:
				raise RuntimeError('Unsupported action', action)
		elif plane is Plane.text:
			append(destination[-1], text)
		else:
			raise RuntimeError('Unsupported plane', plane)

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
	return result, log
