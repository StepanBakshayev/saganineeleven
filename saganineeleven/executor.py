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
	current_element: Optional[Element] = field(default=None, init=False)

	def __post_init__(self):
		self.source_chain.append(self.source)

		self.destination = element_selfcopy(self.source)
		self.destination_chain.append(self.destination)

	def copy(self, routes: Iterator[Route]):
		for route in routes:
			root = get_root(route.branch, self.current_route.branch)
			branch_index = len(root)
			# _branch starts with root.
			self.source_chain = self.source_chain[:branch_index + 1]
			self.destination_chain = self.destination_chain[:branch_index + 1]
			self.current_route = Route(root, ())
			self.current_element = None

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
		if index + 1 < len(parent):
			ending.append(Route(branch=pointer_path[:i], crossroad=tuple(range(index+1, len(parent)))))
	return tuple(ending)


def make_opening_range(pointer_path, waterline):
	opening = []
	for i in range(waterline, len(pointer_path)):
		index = pointer_path[i]
		if index != OPENER:
			opening.append(Route(branch=pointer_path[:i], crossroad=tuple(range(0, index))))
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


@dataclass(frozen=True)
class ElementPosition:
	path: Path
	index: int


@dataclass(frozen=True)
class LoopBody:
	start: ElementPosition
	stop: ElementPosition


def fake_enforce(source: Element, tape: Line, boundaries: Mapping[Index, Boundary]) -> TreeBuilder:
	def iterate_boundaries(boundaries, start, stop):
		for index in range(start, stop):
			yield index, boundaries[index]

	def jump_over(iboundaries):
		i_up = next(iboundaries, None)
		if i_up is None:
			return
		_, up = i_up
		while True:
			i_down = next(iboundaries, None)
			if i_down is None:
				return
			_, down = i_down
			yield up.opening, len(down.gap.branch) + 1
			up = down

	builder = TreeBuilder(source)

	previous_present = ElementPosition(path=(), index=min(boundaries)-1)
	previous_discarded = None
	loop_body = None
	last_discard = False
	# boundaries are used to skip holes in tree in climbing up in tree and moving forward on tape.
	for pointer, text in tape:
		if loop_body and pointer.index > loop_body.stop.index:
			loop_body = None
		if previous_discarded and pointer.index < previous_discarded.index:
			loop_body = LoopBody(ElementPosition(pointer.path, pointer.index), previous_discarded)
			previous_discarded = None

		# discard
		if not pointer.is_constant and not text:
			previous_discarded = ElementPosition(pointer.path, pointer.index)
			last_discard = True
			continue

		# calculate real distance movement from previous position.
		# It is possible to have empty discarded pointers earlier.
		if pointer.index - previous_present.index > 1:
			debug('discard', previous_present)
			last_discard = True
		else:
			last_discard = False

		debug(pointer, text)
		debug(last_discard)
		build = False
		# build
		if loop_body:
			routes = ()
			level = previous_present.path

			debug(loop_body, previous_present)

			next_to_previous_index = previous_present.index + 1
			previous_boundary = boundaries[next_to_previous_index]
			routes += previous_boundary.ending + (previous_boundary.gap,)
			level = boundaries[next_to_previous_index].gap.branch

			# close from present to loop_body.stop
			watermark = get_root(level, loop_body.stop.path)
			if watermark < level:
				debug(watermark, level)

				rolling_index = next_to_previous_index
				closing_boundaries = iterate_boundaries(boundaries, rolling_index+1, loop_body.stop.index)
				for index, boundary in closing_boundaries:
					rolling_index = index
					for route in boundary.ending+(boundary.gap,):
						if level > route.branch:
							routes += route,
							level = route.branch
					if level == watermark:
						break
				debug('closing', routes)

			# climb up from loop_body.start to pointer
			prelude_boundaries = iterate_boundaries(boundaries, loop_body.start.index+1, pointer.index+1)
			prelude = []
			max_depth = len(pointer.path)
			for up, lower_depth in jump_over(prelude_boundaries):
				lower_depth = min(max_depth, lower_depth)
				debug(up, lower_depth)

				for route in up:
					if len(route.branch) >= lower_depth:
						break
					prelude.append(route)
				debug('up', prelude)

				while prelude and (len(prelude[-1].branch) + bool(prelude[-1].crossroad)) > lower_depth:
					debug(prelude.pop())
				print('---')

			routes += tuple(prelude)
			debug('prelude', routes)

			# self prelude
			if True:
				routes += boundaries[pointer.index].gap,
			routes += boundaries[pointer.index].opening
			debug('selfprelude', routes)

			# copy self
			routes += Route(pointer.path[:-1], pointer.path[-1:]),
			debug('self', routes)
			# empty crossroads are critical here. it reset state of builder.
			builder.copy(routes)
			print('loop copy')
			build = True

		# XXX: this condition is wrong for identifying builder.copy needs (copy presented node or allocate node for set_text).
		elif previous_present.path != pointer.path:
			routes = ()
			level = previous_present.path

			debug(previous_present.index)

			next_to_previous_index = previous_present.index + 1
			previous_boundary = boundaries[next_to_previous_index]
			routes += previous_boundary.ending + (previous_boundary.gap,)
			level = boundaries[next_to_previous_index].gap.branch

			debug(next_to_previous_index, previous_boundary)
			debug('next_to_previous_index', routes)

			if last_discard:
				# pave route to current element
				rolling_index = next_to_previous_index

				# First, close all opened elements by present pointers, but with holes on the way to current pointer.
				# Requirement is sync point of previous and current pointers deeper.
				watermark = get_root(level, pointer.path)
				if watermark < level:
					debug(watermark, level)

					closing_boundaries = iterate_boundaries(boundaries, rolling_index+1, pointer.index+1)
					for index, boundary in closing_boundaries:
						rolling_index = index
						for route in boundary.ending+(boundary.gap,):
							if level > route.branch:
								routes += route,
								level = route.branch
						if level == watermark:
							break
					debug('closing', routes)

				# Second, climb up to current pointer using prelude from holes.
				# Requirement is holes between previous and current pointers.
				# XXX: I suspect one more requirement. It is about some distance in depth between root and pointer.path.
				if rolling_index < pointer.index:
					debug(rolling_index, pointer.index)

					prelude_boundaries = iterate_boundaries(boundaries, rolling_index, pointer.index+1)
					prelude = []
					max_depth = len(pointer.path)
					for up, lower_depth in jump_over(prelude_boundaries):
						lower_depth = min(max_depth, lower_depth)
						debug(up, lower_depth)

						for route in up:
							if len(route.branch) >= lower_depth:
								break
							prelude.append(route)
						debug('up', prelude)

						while prelude and (len(prelude[-1].branch) + bool(prelude[-1].crossroad)) > lower_depth:
							debug(prelude.pop())
						print('---')

					routes += tuple(prelude)
					debug('prelude', routes)

			# self prelude
			if last_discard:
				routes += boundaries[pointer.index].gap,
			routes += boundaries[pointer.index].opening
			debug('selfprelude', routes)

			# copy self
			routes += Route(pointer.path[:-1], pointer.path[-1:]),
			debug('self', routes)
			builder.copy(filter(attrgetter('crossroad'), routes))
			print('copy')
			build = True

		# set text
		if not pointer.is_constant and text:
			# XXX: temporary stub, each document handler must provide middleware for management text content.
			current_element = builder.current_element
			if current_element.tag.endswith('}r'):
				for element in current_element:
					if element.tag.endswith('}t'):
						break
				if build:
					element.text = text
				else:
					element.text += text
				debug('run', element.text)
			elif current_element.tag.endswith('}textpath'):
				if build:
					current_element.set('string', text)
				else:
					current_element.set('string', current_element.get('string')+text)
				debug('textpath', current_element.attrib)
			else:
				raise  NotImplementedError(repr(current_element))
			print('set_text')

		previous_present = ElementPosition(pointer.path, pointer.index)
		previous_discarded = None
		last_discard = False
		print()

	last_index = max(boundaries)

	routes = ()
	next_to_previous_index = previous_present.index + 1
	previous_boundary = boundaries[next_to_previous_index]
	routes += previous_boundary.ending + (previous_boundary.gap,)
	level = boundaries[next_to_previous_index].gap.branch
	debug('previous present', routes)
	# 1) continue closing
	debug(last_discard, previous_present, last_index, boundaries[last_index])
	if last_discard:
		rolling_index = next_to_previous_index

		# First, close all opened elements by present pointers, but with holes on the way to current pointer.
		# Requirement is sync point of previous and current pointers deeper.
		watermark = boundaries[last_index].gap.branch
		debug(watermark, level)
		if watermark < level:
			debug(watermark, level)
			debug(rolling_index+1, last_index+1, boundaries)

			closing_boundaries = iterate_boundaries(boundaries, rolling_index+1, last_index+1)
			for index, boundary in closing_boundaries:
				rolling_index = index
				for route in boundary.ending+(boundary.gap,):
					if level > route.branch:
						routes += route,
						level = route.branch
				if level == watermark:
					break

			debug('close', routes)
	# copy current
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
