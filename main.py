# -*- coding: utf-8 -*-

# не убирать - импортируются типы namedtuple, которые требуются модулю pickle
from base_const import *

import context
import locsettings
import move_funcs
import os
import pickle
import strct1c

# Используется для отбора среди обработок нужной
PROCESSOR_NAME = "iBank2"

# Использовать кеширование, в этом случае некоторые структуры данных будут выгружены на диск
# Для того что бы в следующий раз не вычислять их
CACHE_MODE_ON = True

TODO_DUMP_FOLDER = "dump"

# todo для универсальности должно параметризоваться и вычисляться подвызовы
FUNC_FOR_OBTAIN_MAIN_FORM = 'CommonModule.iBank2_ОбщегоНазначенияКлиент.ПолучитьОсновногоВладельцаФормы'

# Cписок вырезаемых из кода областей.
# Все остальные области остануться "как есть" с удаленными обрамлениями областей.
# todo должен параметризоваться
EXCLUDE_AREAS = ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"]

MAIN_MANAGED_FORM_NAME = "Основная"

if CACHE_MODE_ON and os.path.isfile('init_stage.pickle'):
    with open('init_stage.pickle', 'rb') as f:
        gl_context = pickle.load(f)
else:
    gl_context = context.get_primary_context(TODO_DUMP_FOLDER, EXCLUDE_AREAS)
    if CACHE_MODE_ON:
        with open('init_stage.pickle', 'wb') as f:
            pickle.dump(gl_context, f)

if CACHE_MODE_ON and os.path.isfile('final_stage.pickle'):
    with open('final_stage.pickle', 'rb') as f:
        (gl_context, gl_move_config) = pickle.load(f)
else:
    # Получить конфигурацию перемещений
    gl_move_config = move_funcs.get_move_functions_configuration(gl_context, FUNC_FOR_OBTAIN_MAIN_FORM)

    # Выполнить перемещение процедур и функций в основную форму
    move_funcs.transfer_functions_to_main_form(gl_context, gl_move_config, PROCESSOR_NAME)

    # Выполнить перемещение процедур и функций во вспомогательные формы
    move_funcs.transfer_functions_to_secondary_form(gl_context, gl_move_config,
                                                    PROCESSOR_NAME,
                                                    FUNC_FOR_OBTAIN_MAIN_FORM)
    if CACHE_MODE_ON:
        with open('final_stage.pickle', 'wb') as f:
            pickle.dump( (gl_context, gl_move_config) , f)

for full_form_name, form_prop in gl_context.gl_form_props.items():
    form_prop['text'] = strct1c.get_text(form_prop['struct'])

#######################################################################################################
# Локализация.

loc_dict = locsettings.get_localization_settings('ru')
for form_name, form_props in gl_context.gl_form_props.items():
   # todo пока только управляемые формы
   if not form_props['is_managed']:
       continue
   module_text = form_props['text']
   for loc_key, loc_val in loc_dict.items():
       module_text = module_text.replace("{"+loc_key+"}", loc_val)
   form_props['text'] = module_text

# выгрузка подготовленных текстов на диск
for form_name, form_props in gl_context.gl_form_props.items():
    if form_props['is_managed']:
        file_name = form_props['file_name']
        text = form_props['text']
        file = open(os.path.join('dump.new', file_name), 'w', encoding='utf-8')
        file.write(u'\ufeff')
        file.write(text)
    else:
        pass

# При переносе функций во вспомогательную форму необходимо удалить признак экспортной функции.
# functions_to_move_dict
# replace_calls_to_primary_module

# Во вспомогательных управляемых формах
# а) добавить переменную модуля формы ОсновнаяФорма
# б) в обработчик ПриОткрытии (должен быть добавлен во все формы) добавить вызов ОсновнаяФорма = ПолучитьОсновнуюФорму() (вместо ПолучитьОсновногоВладельцаФормы)
# в) во обращениях к основной форме вместо ПолучитьОсновногоВладельцаФормы() использовать ОсновнаяФорма


