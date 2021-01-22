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
import sys
from dataclasses import dataclass, field, replace
from enum import Enum
from operator import itemgetter, attrgetter
from xml.etree.ElementTree import ElementTree, parse, Element
from typing_extensions import Literal

from devtools import debug

from itertools import islice, tee, chain
from collections import namedtuple, deque
from typing import Tuple, Sequence, Deque, Iterator, Dict, Union, Optional, List, Mapping, TypeVar, NewType

from .straighten import ElementPointer, Path, Line, Index


def get_root(a: Sequence, b: Sequence) -> Sequence:
	index = -1
	for index, (i, j) in enumerate(zip(a, b)):
		if i != j:
			index -= 1
			break
	return a[:index+1]


# XXX: copy-paste from Element.copy partially.
def element_selfcopy(element: Element) -> Element:
	new = element.makeelement(element.tag, element.attrib)
	new.text = element.text
	new.tail = element.tail
	return new


def element_deepcopy(element: Element):
	new = element_selfcopy(element)
	for child in element:
		new.append(element_deepcopy(child))
	return new


@dataclass(frozen=True)
class Route:
	branch: Path  # Elements from this list is coped by self.
	crossroad: Tuple[Index, ...]  # Elements from this list is coped deep.


@dataclass
class TreeBuilder:
	source: Element
	destination: Element = field(init=False)
	source_chain: List[Element] = field(default_factory=list, init=False)
	destination_chain: List[Element] = field(default_factory=list, init=False)
	current_route: Route = field(default_factory=lambda: Route((), ()), init=False)
	current_element: Element = field(init=False)

	def __post_init__(self):
		self.source_chain.append(self.source)

		self.destination = element_selfcopy(self.source)
		self.destination_chain.append(self.destination)
		self.current_element = self.destination

	def copy(self, routes: Iterator[Route]):
		for route in routes:
			root = get_root(route.branch, self.current_route.branch)
			branch_index = len(root)
			# _branch starts with root.
			self.source_chain = self.source_chain[:branch_index + 1]
			self.destination_chain = self.destination_chain[:branch_index + 1]

			for index in route.branch[branch_index:]:
				# There are many similar names, append, indexing. Use intermediate names for different terms.
				origin_parent = self.source_chain[-1]
				parent = self.destination_chain[-1]

				origin = origin_parent[index]
				new = element_selfcopy(origin)
				parent.append(new)

				self.source_chain.append(origin)
				self.destination_chain.append(new)

				self.current_element = new
				self.current_route = route

			origin_parent = self.source_chain[-1]
			parent = self.destination_chain[-1]
			for index in route.crossroad:
				origin = origin_parent[index]
				new = element_deepcopy(origin)
				parent.append(new)

				self.current_element = new
				self.current_route = route


@dataclass(frozen=True)
class Boundary:
	ending: Tuple[Route, ...]
	gap: Route
	opening: Tuple[Route, ...]


OPENER = 0


def get_chain(tree_root, path: Path):
	node = tree_root
	for index in path:
		node = node[index]
		yield node


def make_ending_range(chain, pointer_path, waterline):
	ending = []
	for i in range(len(pointer_path)-1, waterline, -1):
		parent = chain[i-1]
		index = pointer_path[i]
		route = Route(pointer_path[:i], ())
		if index + 1 < len(parent):
			route = replace(route, crossroad=tuple(range(index+1, len(parent))))
		ending.append(route)
	return tuple(ending)


def make_opening_range(pointer_path, waterline):
	opening = []
	for i in range(waterline, len(pointer_path)):
		index = pointer_path[i]
		route = Route(pointer_path[:i], ())
		if index != OPENER:
			route = replace(route, crossroad=tuple(range(0, index)))
		opening.append(route)
	return tuple(opening)


def delineate_boundaries(tree_root: Element, line: Line) -> Mapping[Index, Boundary]:
	registry = {}
	pointers = map(itemgetter(0), line)
	previous_pointer = next(pointers)
	previous_route = tuple(get_chain(tree_root, previous_pointer.path))
	common_root = previous_pointer.path
	for pointer in pointers:
		if previous_pointer.path != pointer.path:
			root = get_root(previous_pointer.path, pointer.path)
			assert root < previous_pointer.path < pointer.path, (root, previous_pointer.path, pointer.path)
			branch_index = len(root)
			ending = ()
			gap = Route(root, ())
			opening = ()

			if branch_index + 1 < len(previous_pointer.path):
				ending = make_ending_range(previous_route, previous_pointer.path, branch_index+1)

			if previous_pointer.path[branch_index]+1 < pointer.path[branch_index]:
				gap = replace(gap, crossroad=tuple(range(previous_pointer.path[branch_index]+1, pointer.path[branch_index])))

			if branch_index + 1 < len(pointer.path):
				opening = make_opening_range(pointer.path, branch_index+1)

			if any((ending, gap.crossroad, opening)):
				registry[pointer.index] = Boundary(ending=ending, gap=gap, opening=opening)

		previous_pointer = pointer
		previous_route = tuple(get_chain(tree_root, previous_pointer.path))
		common_root = get_root(common_root, previous_pointer.path)

	branch_index = len(common_root)
	gap = Route(common_root, ())

	first_pointer = line[0][0]
	ending = make_opening_range(first_pointer.path[:branch_index], 0)
	opening = make_opening_range(first_pointer.path, branch_index)
	registry[first_pointer.index] = Boundary(ending=ending, gap=gap, opening=opening)

	last_pointer = line[-1][0]
	ending = make_ending_range(previous_route, last_pointer.path, branch_index)
	opening = make_ending_range(previous_route, last_pointer.path[:branch_index+1], 0)
	registry[last_pointer.index+1] = Boundary(ending=ending, gap=gap, opening=opening)

	return registry


def fake_enforce(source: Element, tape: Line, boundaries: Mapping[Index, Boundary]) -> TreeBuilder:
	builder = TreeBuilder(source)

	def iterate_boundaries(boundaries, start, stop):
		for index in range(start, stop):
			if index in boundaries:
				yield index, boundaries[index]

	def jump_over(iboundaries):
		i_up = next(iboundaries, None)
		if i_up is None:
			return
		_, up = i_up
		while True:
			i_down = next(iboundaries, None)
			if i_down is None:
				yield up.opening, ()
				return
			_, down = i_down
			yield up.opening, down.ending
			up = down

	previous_path = ()
	previous_index = min(boundaries) - 1
	last_discard = False
	# boundaries are used to skip holes in tree in climbing up in tree and moving forward on tape.
	for pointer, text in tape:
		# discard
		if not pointer.is_constant and not text:
			last_discard = True
			continue

		debug(last_discard, pointer, text)
		# build
		# XXX: ignore cycles for awhile.
		if previous_path != pointer.path:
			routes = ()
			level = previous_path

			debug(previous_index, boundaries)
			next_to_previous_index = previous_index + 1
			if next_to_previous_index in boundaries:
				routes += boundaries[next_to_previous_index].ending
				level = boundaries[next_to_previous_index].gap.branch
				debug('next_to_previous_index', routes)

			if last_discard:
				# pave route to current element
				watermark = get_root(previous_path, pointer.path)
				index = next_to_previous_index
				if watermark < level:
					closing_boundaries = iterate_boundaries(boundaries, index, pointer.index+1)
					for index, boundary in closing_boundaries:
						for route in boundary.ending+(boundary.gap,):
							if level > route.branch:
								routes += route,
								level = route.branch
						if level == watermark:
							break
					debug('closing', routes)

				debug(index, pointer.index)
				if index < pointer.index:
					watermark = pointer.path
					debug(index, iterate_boundaries(boundaries, index, pointer.index+1))
					prelude_boundaries = iterate_boundaries(boundaries, index, pointer.index+1)
					# debug(routes, level, watermark, index)
					prelude = []
					for up, down in jump_over(prelude_boundaries):
						debug(up, down)
						for route in up:
							if watermark < route.branch:
								break
							prelude.append(route)
						for route in down:
							while route.branch <= prelude[-1]:
								prelude.pop()
					routes += tuple(prelude)
					debug('prelude', routes)

			# self prelude
			if pointer.index in boundaries:
				routes += boundaries[pointer.index].gap,
				routes += boundaries[pointer.index].opening
			debug('selfprelude', routes)

			# copy self
			routes += Route(pointer.path[:-1], pointer.path[-1:]),
			debug('self', routes)
			builder.copy(filter(attrgetter('crossroad'), routes))
			print('---')

		# set text
		if not pointer.is_constant and text:
			# XXX: temporary stub, each document handler must provide middleware for management text content.
			for element in builder.current_element:
				if element.tag.endswith('}t'):
					break
			if previous_path != pointer.path:
				element.text = text
			else:
				element.text += text

		previous_path = pointer.path
		previous_index = pointer.index
		last_discard = False

	routes = ()
	if previous_index + 1 in boundaries:
		routes += boundaries[previous_index+1].ending
	# 1) continue closing
	# copy current
	last_index = max(boundaries)
	routes += boundaries[last_index].opening
	builder.copy(filter(attrgetter('crossroad'), routes))

	return builder


# Utility function for debug purpose.
def make_x(root: Element, path: Path) -> List[str]:
	if path is None:
		return 'None'
	parent = root
	tag = parent.tag
	count = 0
	chunks = [f'{tag}[{count}]']
	for index in path:
		try:
			child = parent[index]
		except IndexError:
			chunks.append(f'{parent}?{index}')
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


# # plane:
# # - text
# # - element
# # element:
# # - direction
# # - action
#
#
#
#
# Operation = Enum('Operation', 'copy set_text', module=__name__)
#
#
# ElementOperation = Enum('ElementOperation', 'copy set_text none', module=__name__)
#
#
# def get_operation(pointer: ElementPointer, text: str) -> ElementOperation:
# 	if pointer.is_constant:
# 		assert pointer.offset == 0, (pointer, text)
# 		assert pointer.length == len(text)
# 		return ElementOperation.copy
# 	elif text:
# 		assert pointer.offset < pointer.representation_length, (pointer, text)
# 		assert pointer.length, (pointer, text)
# 		return ElementOperation.set_text
# 	return ElementOperation.none
#
#

#
#
# def decode(tree_root: Element, tape: Iterator[Tuple[ElementPointer, str]]) -> Iterator[Union[Dict[Literal[Operation.copy], Range], Dict[Literal[Operation.set_text], str]]]:
# 	"""
# 	This is not decode. It is interpretate or trans-something.
#
# 	"""
# 	annotation, plain = tee(tape)
# 	annotated_tape = zip(map(lambda p0t1: get_operation(p0t1[0], p0t1[1]), annotation), plain)
#
# 	annotated_tape = chain(
# 		(head_tape,),
# 		annotated_tape,
# 	)
#
# 	last_text_path = None
# 	previous_position = ((), 0, 0)
# 	for operation, (pointer, text) in annotated_tape:
# 		path = pointer.path
# 		position = tuple(map(lambda n: getattr(pointer, n), ('path', 'offset', 'length')))
# 		# debug(operation, position, make_x(tree_root, path), text)
# 		# print('')
# 		if operation is ElementOperation.none:
# 			if copy_range_start:
# 				root = get_root(copy_range_start, path)
# 				branch_index = len(root)
# 				start_successor = copy_range_start[branch_index] + 1
# 				end_exclude = path[branch_index]
# 				if end_exclude == start_successor:
# 					yield {Operation.copy: Range(copy_range_start, root+(start_successor,))}
# 				else:
# 					yield {Operation.copy: Range(copy_range_start, root+(end_exclude-1,))}
# 				copy_range_start = None
#
# 		elif operation is ElementOperation.copy:
# 			if copy_range_start is None:
# 				copy_range_start = path
#
# 		elif operation is ElementOperation.set_text:
# 			if path != last_text_path:
# 				yield {Operation.copy: Range(path, path)}
# 				last_text_path = path
# 			yield {Operation.set_text: text}
#
# 		else:
# 			raise RuntimeError(f'Unsupported operation {operation}.', operation)
#
# 		assert previous_position != position, ((make_x(root, previous_position[0]), previous_position), (make_x(root, position[0]), position))
# 		previous_position = position
#
#
# def enforce(origin: 'FileLikeObject', tape: Iterator[Tuple[Element, str]], middleware) -> Tuple[ElementTree, list]:
# 	"""
# 	Enforce contains those operations:
# 	- substitute variables
# 	- skip terminals
# 	- drop conditions body
# 	- copy partial or allocate place for new iteration of cycle body
# 	- mirror unchanged text in between
#
# 	Substitute requires managing text of element. Substitute can happen many times in one element or completely replace whole text.
# 	Skip terminals is a like substitute with zero length text. It opens door to ignore some nodes from origin.
# 	Drop conditions body requires accurate cut part of tree (partial copy in terms of this kind implementation) on boundary of different levels of hierarchy.
# 	Vague operation of cycle body requires look behind on origin tree and construct new branch for inside operation from above.
# 	Mirror unchanged text (in terms of template) is a suspect for variant of operations from above.
# 	"""
# 	# XXX: It is memory consumption here.
# 	origin_tree = parse(origin)
#
# 	# XXX: It is just for starting implementation to copy root.
# 	# XXX: It is bad design to copy each element from one tree to another.
# 	result_tree = ElementTree(origin_tree.getroot().copy())
# 	# Free tinking. Postpone ideas by finishing cycling.
# 	# TreeBuilder is used to construct ElementTree instead of incremental dump as I think at fist.
# 	# XXX: We don't use or rely of nodes in memory. Consider writing incremental dump against xml.etree.ElementTree._serialize_xml.
# 	# XXX: We don't need parse origin neither. We copy substring from original to result.
#
# 	# XXX: return to Element and rewrite it for structuted path.
# 	def restore_path(element: Element):
# 		for (namespace_id, tag), index in element.path:
# 			yield TagIndex(
# 				namespace=element.namespaces[namespace_id],
# 				name=tag,
# 				index=index,
# 			)
#
# 	log = []
# 	origin_root = origin_tree.getroot()
# 	result_root = element_copy(origin_root)
# 	result = ElementTree(result_root)
# 	element_tag = result_root.tag
# 	namespace, tagname = '', element_tag
# 	match = namespace_re.match(element_tag)
# 	if match:
# 		namespace, tagname = match.group('namespace', 'tagname')
# 	destination = deque((result_root,))
# 	source = deque((origin_root,))
# 	initial_path = TagIndex(namespace, tagname, 0),
# 	previous_path = initial_path
# 	previous_offset = 0
# 	for element, text in tape:
# 		path = tuple(restore_path(element))
# 		if path == previous_path and element.offset != previous_offset:
# 			plane = Plane.text
# 			direction = Direction.none
# 			action = Action.none
# 		else:
# 			plane = Plane.element
# 			if path > previous_path:
# 				direction = Direction.forward
# 			else:
# 				direction = Direction.backward
# 			action = Action.copy
# 			if element.length and not text:
# 				action = Action.skip
#
# 		tag_repr = lambda t: f'{t.name}[{t.index}]'
# 		log.append([
# 			['/'.join(map(tag_repr, previous_path)), '/'.join(map(tag_repr, path))],
# 			[plane.name, direction.name, action.name],
# 			text,
# 		])
# 		# debug(log[-1])
#
# 		if plane is Plane.element:
# 			if action is Action.copy:
# 				copy(source, destination, previous_path, path)
# 				set(destination[-1], text)
# 				previous_path = path
# 				previous_offset = element.offset
# 			elif action is Action.skip:
# 				# explicit handling.
# 				# XXX: call middleware for handling skipping. copy will be handling too in near future.
# 				root_index = 0
# 				for root_index, (a, b) in enumerate(zip(previous_path, path)):
# 					if a != b:
# 						root_index -= 1
# 						break
# 				source = deque(islice(source, root_index+1))
# 				destination = deque(islice(destination, root_index+1))
# 				previous_path = previous_path[:root_index+1]
# 				previous_offset = element.offset
# 			else:
# 				raise RuntimeError('Unsupported action', action)
# 		elif plane is Plane.text:
# 			append(destination[-1], text)
# 			previous_offset = element.offset
# 		else:
# 			raise RuntimeError('Unsupported plane', plane)
#
#
# 	tag_repr = lambda t: f'{t.name}[{t.index}]'
# 	log.append([
# 		['/'.join(map(tag_repr, previous_path)), '/'.join(map(tag_repr, path))],
# 		[plane.name, direction.name, action.name],
# 		text,
# 	])
# 	# debug(log[-1])
# 	copy(source, destination, previous_path, initial_path)
#
# 	return result, log
