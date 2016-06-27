# -*- coding: utf-8 -*-

# не убирать - импортируются типы namedtuple, которые требуются модулю pickle
from base_const import *

import base_const
import context
import custom_handlers
import move_funcs
import os
import pickle
import strct1c

# Использовать кеширование, в этом случае некоторые структуры данных будут выгружены на диск
# Для того что бы в следующий раз не вычислять их
CACHE_MODE_ON = True


def init_context(dump_folder, exclude_areas):
    if CACHE_MODE_ON and os.path.isfile('init_stage.pickle'):
        with open('init_stage.pickle', 'rb') as f:
            gl_context = pickle.load(f)
    else:
        gl_context = context.get_primary_context(dump_folder, exclude_areas)
        if CACHE_MODE_ON:
            with open('init_stage.pickle', 'wb') as f:
                pickle.dump(gl_context, f)
    return gl_context


def do_transfer(context):
    if CACHE_MODE_ON and os.path.isfile('final_stage.pickle'):
        with open('final_stage.pickle', 'rb') as f:
            (context, move_config, dataproc_module_config) = pickle.load(f)
    else:

        # получить настройки перемещения для обычного приложения
        dataproc_module_config = move_funcs.get_move_functions_configuration_ordinary_app(context)

        # Выполнить перемещение процедур и функций в модуль обработки
        move_funcs.transfer_functions_to_dataprocessor_module(context, dataproc_module_config)

        # Получить конфигурацию перемещений
        move_config = move_funcs.get_move_functions_configuration(context)

        # Выполнить перемещение процедур и функций в основную форму
        move_funcs.transfer_functions_to_main_form(context, move_config, custom_handlers.PROCESSOR_NAME)

        # Выполнить перемещение процедур и функций во вспомогательные формы
        move_funcs.transfer_functions_to_secondary_form(context, move_config)
        if CACHE_MODE_ON:
            with open('final_stage.pickle', 'wb') as f:
                pickle.dump( (context, move_config, dataproc_module_config) , f)
    return (context, move_config, dataproc_module_config)

def prepare_dataprocessor_module_text(dataprocessor_module_struct, gl_dataproc_module_config):

    # Извлечем из модуля набор функций, которые напрямую вызываются из модуля объекта в режиме тонкого клиента.
    # Например, функция СведенияОВнешнейОбработке(..), которую требует БСП.
    dp_module_chain_funcs = []
    dp_module_chain_names = {name.split('.')[2] for name in gl_dataproc_module_config.dp_module_chain}
    index = 0
    while index < len(dataprocessor_module_struct.proc_funcs_list):
        name = dataprocessor_module_struct.proc_funcs_list[index].name
        if name in dp_module_chain_names:
            dp_module_chain_funcs.append(dataprocessor_module_struct.proc_funcs_list.pop(index))
        else:
            index = index + 1

    # Составим текст модуля самостоятельно по схеме:
    #   <глобальные переменные>
    #   <процедуры и функции для запуска модуля объекта в управляемом приложении>
    #   #Если ТолстыйКлиентОбычноеПриложение Тогда
    #       <процедуры и функции вызываемые из обычных форм>
    #       <код модуля>
    #   #КонецЕсли

    # установим начальный отступ
    strct1c.set_indent(0)

    # получить текст глобальных переменные
    module_text = strct1c.get_op_list_text(dataprocessor_module_struct.global_vars_list)

    # добавить цепочку вызова для чисто модульных вызовов
    for func_desc in dp_module_chain_funcs:
        module_text += func_desc.get_text() + '\n'

    # все функции, которые были перенесены в модуль для вызова из обычных форм обрамить в инструкцию препроцессора
    module_text += '\n' + '#Если ТолстыйКлиентОбычноеПриложение Тогда' + '\n\n' \
                      + strct1c.get_op_list_text(dataprocessor_module_struct.proc_funcs_list, False) + '\n' \
                      + strct1c.get_op_list_text(dataprocessor_module_struct.statements_list) \
                      + '#КонецЕсли' + '\n'
    # скопировать текст
    return module_text


def make(dump_folder, exclude_areas):

    context = init_context(dump_folder, exclude_areas)
    context, move_config, dataproc_module_config = do_transfer(context)

    # Получим код для модуля объекта обработки
    context.gl_ep_module['text'] = prepare_dataprocessor_module_text(context.gl_ep_module['struct'],
                                                                     dataproc_module_config)

    # Для модулей форм просто получим тексты подготовленные ранее
    for full_form_name, form_prop in context.gl_form_props.items():
        form_prop['text'] = strct1c.get_text(form_prop['struct'])

    # Выполнить дополнение модуля объекта в кастомном модуле
    custom_handlers.update_module_texts(context)

    def write_module_text(file_name, text):
        file = open(os.path.join('dump.new', file_name), 'w', encoding='utf-8')
        file.write(u'\ufeff')
        file.write(text)

    write_module_text('Обработка.' + custom_handlers.PROCESSOR_NAME + '.МодульОбъекта.txt', context.gl_ep_module['text'])

    for form_name, form_props in context.gl_form_props.items():
        write_module_text(form_props['file_name'], form_props['text'])
    pass

if __name__ == '__main__':
    make("dump", ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"])
