# -*- coding: utf-8 -*-

# не убирать - импортируются типы namedtuple, которые требуются модулю pickle
from epfcomp.base_const import *

from epfcomp import base_const
from epfcomp import context
from epfcomp import custom_handlers
from epfcomp import move_funcs
from epfcomp import strct1c
from epfcomp import obfuscate

import os
import pickle

# В режиме кеширования контекст и другие структуры данных после вычисления выгружаются на диск,
# а при последующем запуске загружаются с диска вместо вычисления.
CACHE_MODE_ON = True

def init_context(dump_folder, build_params, exclude_areas):
    """
    Выполняет кеширование и загрузку из кеша результатов функции get_primary_context.
    @param dump_folder: каталог с выгруженными модулями конфигурации
    @param exclude_areas: список областей, которые следует вырезать перед обработкой
    @return: контекст - специальная структура данных, содержащая структуру общих модулей,
                        модулей форм и модуля обработки
    """
    log('Инициализация контекста')
    if CACHE_MODE_ON and os.path.isfile('init_stage.pickle'):
        with open('init_stage.pickle', 'rb') as f:
            gl_context = pickle.load(f)
            log('Контекст загружен из кеша')
    else:
        gl_context = context.get_primary_context(dump_folder, build_params, exclude_areas)
        if CACHE_MODE_ON:
            with open('init_stage.pickle', 'wb') as f:
                pickle.dump(gl_context, f)
    return gl_context


def do_transfer(context, build_params):
    """
    Основная функция - наполнение модулей форм и модуля объекта обработки процедурами и функциями из общих модулей.
    Состоит из двух частей - перенос процедур и функций в обычные формы (при этом код переносится в модуль объекта)
    и перенос кода в управляемые формы - более сложная схема.
    @param context:
    @return:

    @param context: контекст обработки, см. init_context
    @return:
    """
    log('Подготовка конфигурации перемещения')
    if CACHE_MODE_ON and os.path.isfile('final_stage.pickle'):
        with open('final_stage.pickle', 'rb') as f:
            log('Конфигурация перемещения загружена из файла')
            (context, move_config, dataproc_module_config) = pickle.load(f)
    else:
        if build_params.ordinary_forms:
            # получить настройки перемещения для обычного приложения
            dataproc_module_config = move_funcs.get_move_functions_configuration_ordinary_app(context)

            # Выполнить перемещение процедур и функций в модуль обработки
            move_funcs.transfer_functions_to_dataprocessor_module(context, dataproc_module_config,
                                                                  build_params.object_name)

        if build_params.managed_forms:
            # Получить конфигурацию перемещений в управляемые формы
            move_config = move_funcs.get_move_functions_configuration(context, build_params)

            # Выполнить перемещение процедур и функций в основную форму
            move_funcs.transfer_functions_to_main_form(context, move_config, build_params)

            # Выполнить перемещение процедур и функций во вспомогательные формы
            move_funcs.transfer_functions_to_secondary_form(context, move_config, build_params.object_name)

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


def process_dump(dump_folder: str, build_params, exclude_areas: list,
                 obfuscation_params: dict, loc: str, debug: bool = False) -> dict:
    """
    Точка входа. Выполняет обработку модулей конфигурации.
    @param dump_folder: каталог с выгруженными модулями конфигурации
    @param exclude_areas: список областей, которые следует вырезать перед обработкой
    @param obfuscation_params: параметры обфускации - включаемые и исключаемые идентификаторы,
                               None - не выполнять обфускацию
    @param loc: преобразует локализованные строковые литералы в строку нужной локали, например для loc="ru"
                НСтр("ru='слово';en='word'") => "слово"
                None - не преобразовывать строки
    @param debug: режим отладки, испольуется для служебных целей
    @return: словарь замен для обфусации (если была)
    """

    log('Начало обработки текстов модулей')

    context = init_context(dump_folder, build_params, exclude_areas)

    # Перед тем как обфусцировать составляется словарь процедур и функций в модулях форм - они не будут изменены
    form_handlers_replecements = dict()
    for form_name, form_props in context.gl_form_props.items():
        form_handlers_replecements[form_name] = dict()
        for func_desc in form_props['struct'].proc_funcs_list:
            form_handlers_replecements[form_name][func_desc.name] = None

    context, move_config, dataproc_module_config = do_transfer(context, build_params)

    if loc:
        strct1c.localize(loc)

    # Получим код для модуля объекта обработки
    context.gl_ep_module['text'] = prepare_dataprocessor_module_text(context.gl_ep_module['struct'],
                                                                     dataproc_module_config)
    # Для модулей форм просто получим тексты подготовленные ранее
    for full_form_name, form_prop in context.gl_form_props.items():
        form_prop['text'] = strct1c.get_text(form_prop['struct'])

    replacements_dict = obfuscate.do_obfuscate(context, dataproc_module_config,
                                               obfuscation_params, form_handlers_replecements,
                                               debug) if obfuscation_params else None

    # Выполнить дополнение модуля объекта в кастомном модуле
    custom_handlers.update_context(context)

    def write_module_text(file_name, text):
        file = open(os.path.join(dump_folder, file_name), 'w', encoding='utf-8')
        file.write('\ufeff')
        file.write(text)

    write_module_text('Обработка.' + build_params.object_name + '.МодульОбъекта.txt', context.gl_ep_module['text'])

    for form_name, form_props in context.gl_form_props.items():
        write_module_text(form_props['file_name'], form_props['text'])

    log('Конец обработки текстов модулей')

    return replacements_dict

if __name__ == '__main__':

    obf_exception = {'НачатьИнициализацию', 'Выбрать'}
    obf_force = {'ВидЗапроса_ПолучитьСтатус', 'ДанныеАутентификации', 'ОписаниеПрофиля', 'ПравилаКонвертации'}
    obf_settings = {'force': obf_force, 'except': obf_exception}

    areas = ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"]

    build_params = BuildParams('iBank2', 'Основная', {'Аутентификация', 'ВводPINКода', 'Основная', 'Письмо'}, 
                                                     {'АутентификацияОбычная', 'ВводPINКодаОбычная', 'ОсновнаяОбычная', 'ПисьмоОбычная'})

    replacements_dict = process_dump("dump", build_params, areas, obf_settings, 'ru', True)

    if replacements_dict:
        with open('replacements.txt', 'w') as file:
            for id_orig, id_obf in replacements_dict.items():
                file.write(id_orig + ':' + id_obf + '\n')
