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
import dataclasses
from enum import Enum
from xml.etree.ElementTree import ElementTree, parse, Element
from typing_extensions import Literal

from devtools import debug

from itertools import islice, tee, chain
from collections import namedtuple, deque
from typing import Tuple, Sequence, Deque, Iterator, Dict, Union, Optional

from .straighten import ElementPointer, Path

TagIndex = namedtuple('TagIndex', 'namespace name index')


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
		tag = f'{{{tag_index.namespace}}}{tag}'
	for index, child in enumerate(source):
		if child.tag == tag:
			if count == tag_index.index:
				return index, child
			count += 1
	raise ValueError(f'{tag_index!r} was not found in {source.tag}. Looked up for {tag!r}.', tag_index, tag, source)


def lift_up(source: Deque[Element], destination: Deque[Element], position: Tuple[TagIndex, ...]):
	for tag_index in reversed(position):
		source.pop()
		destination.pop()

		origin = source[-1]
		position_index, _ = find(origin, tag_index)
		clone = destination[-1]
		for successor in origin[position_index+1:]:
			clone.append(element_deepcopy(successor))


def move_forward(source: Deque[Element], destination: Deque[Element], position: TagIndex, target: TagIndex):
	source.pop()
	destination.pop()

	origin = source[-1]
	position_index, _ = find(origin, position)
	target_index, _ = find(origin, target)
	clone = destination[-1]
	for successor in origin[position_index+1:target_index]:
		new = element_deepcopy(successor)
		# XXX: bug here. No one test catches it.
		clone[-1].append(new)


def start_target(source: Deque[Element], destination: Deque[Element], target: TagIndex):
	origin = source[-1]
	target_index, target_node = find(origin, target)
	new = element_copy(target_node)
	clone = destination[-1]
	clone.append(new)

	source.append(target_node)
	destination.append(new)


def go_down(source: Deque[Element], destination: Deque[Element], target: Tuple[TagIndex, ...]):
	for tag_index in target:
		origin = source[-1]
		target_index, target_node = find(origin, tag_index)
		clone = destination[-1]
		for predecessor in origin[0:target_index]:
			clone.append(element_deepcopy(predecessor))
		new = element_copy(target_node)
		clone.append(new)

		source.append(target_node)
		destination.append(new)


def copy(source: Deque[Element], destination: Deque[Element], position: Tuple[TagIndex, ...], target: Tuple[TagIndex, ...]):
	assert source
	assert destination
	assert position
	assert target
	assert len(source) == len(destination) == len(position), (source, destination, position)
	assert position[0] == target[0]
	assert position != target

	root_index = 0
	for root_index, (current_pointer, target_pointer) in enumerate(zip(position, target)):
		if current_pointer != target_pointer:
			root_index -= 1
			break

	branch_index = root_index + 1

	# XXX: I didn't cope with general algorithm. I split handling by simple steps and make script.
	if root_index == 0 and len(target) == 1:
		lift_up(source, destination, position[1:])

	else:
		lift_up(source, destination, position[branch_index+1:])

		if branch_index < len(target):
			if branch_index < len(position):
				move_forward(source, destination, position[branch_index], target[branch_index])
				assert len(source) == len(destination) == (root_index + 1), (source, destination, root_index)

			start_target(source, destination, target[branch_index])
			assert len(source) == len(destination) == (branch_index + 1), (source, destination, branch_index)

			go_down(source, destination, target[branch_index+1:])

	assert len(source) == len(destination) == len(target), (source, destination, target)


# XXX: This is not so easy in real life. MS Word encode tabs, newlines with special tag.
def append(place: Element, text):
	place.text += text


# XXX: This is not so easy in real life. MS Word encode tabs, newlines with special tag.
def set(place: Element, text):
	place.text = text


# plane:
# - text
# - element
# element:
# - direction
# - action

Operation = Enum('Operation', 'copy set_text', module=__name__)

@dataclasses.dataclass(frozen=True)
class Range:
	start: Path
	stop: Path

ElementOperation = Enum('ElementOperation', 'copy set_text none', module=__name__)


def get_operation(pointer: ElementPointer, text: str) -> ElementOperation:
	if pointer.is_constant and pointer.length == len(text):
		assert pointer.offset == 0, (pointer, text)
		return ElementOperation.copy
	elif text:
		assert pointer.offset < pointer.representation_length, (pointer, text)
		assert pointer.length, (pointer, text)
		return ElementOperation.set_text
	return ElementOperation.none


def play(origin_root: Element, tape: Iterator[Tuple[ElementPointer, str]]) -> Iterator[Union[Dict[Literal[Operation.copy], Range], Dict[Literal[Operation.set_text], str]]]:
	opening = []
	node = origin_root
	while len(node):
		opening.append(0)
		node = node[0]
	opening = tuple(opening)

	ending = []
	node = origin_root
	while len(node):
		ending.append(len(node)-1)
		node = node[-1]
	ending = tuple(ending)

	def get_root(a, b):
		root_index = 0
		for index, (i, j) in enumerate(zip(a, b)):
			if i != j:
				root_index -= 1
				break
		return a[:root_index+1]

	annotation, plain = tee(tape)
	path_text = map(lambda p0t1: (p0t1[0].path, p0t1[1]), plain)
	annotated_tape = zip(map(lambda p0t1: get_operation(p0t1[0], p0t1[1]), annotation), path_text)

	# Code below uses variables after for-cycle. Do explicit check to prevent some cryptic errors as NameError.
	head_tape = next(annotated_tape, None)
	if head_tape is None:
		raise ValueError('tape must contain at least one pair of element and text.')

	copy_range_start = None
	last_text_path = None
	full_tape = chain(
		((ElementOperation.copy, (opening, '')), head_tape,),
		annotated_tape,
		((ElementOperation.copy, (ending, '')),),
		((ElementOperation.none, (ending, '')),),
	)
	for operation, (path, text) in full_tape:
		if operation is ElementOperation.none:
			if copy_range_start:
				root = get_root(copy_range_start, path)
				branch_index = len(root)
				start_successor = copy_range_start[branch_index] + 1
				end_exclude = path[branch_index]
				if end_exclude == start_successor:
					yield {Operation.copy: Range(copy_range_start, root+(start_successor,))}
				else:
					yield {Operation.copy: Range(copy_range_start, root+(end_exclude-1,))}
				copy_range_start = None

		elif operation is ElementOperation.copy:
			if copy_range_start is None:
				copy_range_start = path

		elif operation is ElementOperation.set_text:
			if path != last_text_path:
				yield {Operation.copy: Range(path, path)}
				last_text_path = path
			yield {Operation.set_text: text}


def enforce(origin: 'FileLikeObject', tape: Iterator[Tuple[Element, str]], middleware) -> Tuple[ElementTree, list]:
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
	initial_path = TagIndex(namespace, tagname, 0),
	previous_path = initial_path
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

		tag_repr = lambda t: f'{t.name}[{t.index}]'
		log.append([
			['/'.join(map(tag_repr, previous_path)), '/'.join(map(tag_repr, path))],
			[plane.name, direction.name, action.name],
			text,
		])
		debug(log[-1])

		if plane is Plane.element:
			if action is Action.copy:
				copy(source, destination, previous_path, path)
				set(destination[-1], text)
				previous_path = path
				previous_offset = element.offset
			elif action is Action.skip:
				# explicit handling.
				# XXX: call middleware for handling skipping. copy will be handling too in near future.
				root_index = 0
				for root_index, (a, b) in enumerate(zip(previous_path, path)):
					if a != b:
						root_index -= 1
						break
				source = deque(islice(source, root_index+1))
				destination = deque(islice(destination, root_index+1))
				previous_path = previous_path[:root_index+1]
				previous_offset = element.offset
			else:
				raise RuntimeError('Unsupported action', action)
		elif plane is Plane.text:
			append(destination[-1], text)
			previous_offset = element.offset
		else:
			raise RuntimeError('Unsupported plane', plane)


	tag_repr = lambda t: f'{t.name}[{t.index}]'
	log.append([
		['/'.join(map(tag_repr, previous_path)), '/'.join(map(tag_repr, path))],
		[plane.name, direction.name, action.name],
		text,
	])
	debug(log[-1])
	copy(source, destination, previous_path, initial_path)

	return result, log
