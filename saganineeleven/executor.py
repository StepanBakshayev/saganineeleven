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


def enforce(origin: 'FileLikeObject', tape: str, middleware) -> ElementTree:
	"""
	Copy nodes from origin. Replace text with rendered variables.
	"""
	origin_tree = parse(origin)
	# XXX: It is just for starting implementation to copy root.
	# XXX: It is bad design to copy each element from one tree to another.
	result_tree = ElementTree(origin_tree.getroot().copy())

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

	previous_path = None
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
		print(element, text)
	# находимся ли мы в том же элементе?
		location_changed = previous_path != element.path
		if location_changed:
			origin_offset = 0

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
