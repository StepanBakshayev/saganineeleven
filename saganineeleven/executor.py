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


def enforce(origin: 'FileLikeObject', tape: str, middleware) -> ElementTree:
	# copy nodes
	# replace text

	# для вставки достаточно сканировать поседовательно исходник
	# для условного вывода достаточно сканировать последовательно исходик
	# для циклов нет
	# А в чем проблема? нужно трекать состояние куда вставлять очередную ветку элементов и сопоставлять их с текущим
	#
	# Вывод: для циклов необходимо отталкиваться от ленты. Для остальных операций - от исходника.
	# Изначальная идея - это создать НЕОБХОДИМУЮ ИНФРАСТРУКТУРУ и для неё выполнить простейшую операцию: замена.
	#
	# Инфрастуктура включает в себя
	# - создание архива (docx)
	# - копипаста файлов, которые остаются без изменения (docx)
	# - копирование элементов на основе ленты
	# - отладка копироания через инъекцию специфики (docx)
	return parse(origin)
