# -*- coding: utf-8 -*-

import dumped_modules_handler
import parser1c
import preproc1c
import os
import strct1c
import utils
from base_const import *

class ContextType:
    gl_app_module = None
    gl_ep_module = None
    gl_form_props = None
    gl_common_modules_props = None
    gl_all_funcs_desc = None
    gl_func_subcalls = None

def get_application_module_props(dump_folder, exclude_areas):
    """
    Получает тексты и структуру модулей обычного и управляемого приложения.
    @param dump_folder (str): каталог с выгруженными текстами модулей
    @param exclude_areas (list): список областей, исключаемых из модулей при получении структуры
    @return (dict): структура со свойствами
    """
    gl_app_module = dict()
    gl_app_module[APP_TYPE_MANAGED] = dict()
    gl_app_module[APP_TYPE_ORDINARY] = dict()

    # Получение структуры модуля управляемого приложения.
    gl_app_module[APP_TYPE_MANAGED]['text_origin'] = open(
        os.path.join(dump_folder, 'Конфигурация.МодульУправляемогоПриложения.txt'), encoding='utf-8').read()
    preproc = preproc1c.Preprocessor1C(gl_app_module[APP_TYPE_MANAGED]['text_origin'])
    text_managed = preproc.execute('ТонкийКлиент', exclude_areas)
    gl_app_module[APP_TYPE_MANAGED]['text'] = text_managed
    gl_app_module[APP_TYPE_MANAGED]['struct'] = parser1c.parser.parse(text_managed)

    # Получение структуры модуля обычного приложения.
    gl_app_module[APP_TYPE_ORDINARY]['text_origin'] = open(
        os.path.join(dump_folder, 'Конфигурация.МодульОбычногоПриложения.txt'), encoding='utf-8').read()
    preproc = preproc1c.Preprocessor1C(gl_app_module[APP_TYPE_ORDINARY]['text_origin'])
    text_ordinary = preproc.execute('ТолстыйКлиентОбычноеПриложение', exclude_areas)
    gl_app_module[APP_TYPE_ORDINARY]['text'] = text_ordinary
    gl_app_module[APP_TYPE_ORDINARY]['struct'] = parser1c.parser.parse(text_ordinary)

    return gl_app_module


def get_processor_module_props(dump_folder, exclude_areas):

    processor_file_name = ''
    dump_files_list = [f for f in os.listdir(dump_folder) if os.path.isfile(os.path.join(dump_folder, f))]
    for full_file_name in dump_files_list:
        if full_file_name.split('.')[2] == 'МодульОбъекта':
            processor_file_name = full_file_name

    if not processor_file_name:
        # todo может быть такое, что модуль объекта обработки пустой и необходимо будет его создать
        # при этом нужно будет знать полное имя файла, а значит и имя обрабоки.
        # Пример имени файла модуля: Обработка.ExtProc.МодульОбъекта.txt
        raise Exception("Не найден модуль объекта обработки")

    module_props = dict()
    module_props['text_origin'] = open(os.path.join(dump_folder, processor_file_name), encoding='utf-8').read()
    preproc = preproc1c.Preprocessor1C(module_props['text_origin'])
    text = preproc.execute('ТолстыйКлиентОбычноеПриложение', exclude_areas)
    module_props['text'] = text
    module_props['struct'] = parser1c.parser.parse(text)
    return module_props

def get_form_properties(dump_folder, exclude_areas):
    """
    Получает тексты и структуру модулей форм.
    @param dump_folder (str): каталог с выгруженными текстами модулей
    @param exclude_areas (list): список областей, исключаемых из модулей при получении структуры
    @return (dict): структура со свойствами
    """
    gl_form_props = dumped_modules_handler.get_forms_properties(dump_folder, 'iBank2')
    for form_name, form_props in gl_form_props.items():
        context = "ТонкийКлиент" if form_props['is_managed'] else "ТолстыйКлиентОбычноеПриложение"
        # Выполнить препроцессинг, избавиться от областей
        preproc = preproc1c.Preprocessor1C(form_props['text_origin'])
        new_text = preproc.execute(context, exclude_areas, ["НаКлиенте"])
        new_text = add_semicolon_after_preproc(new_text)
        form_props['text'] = new_text
        # Получить синтаксическую структуру модуля
        form_props['struct'] = parser1c.parser.parse(new_text)
    return gl_form_props


def get_common_modules_properties(dump_folder, exclude_areas):
    """
    Получает тексты и структуру общих модулей.
    @param dump_folder (str): каталог с выгруженными текстами модулей
    @param exclude_areas (list): список областей, исключаемых из модулей при получении структуры
    @return (dict): структура со свойствами
    """
    gl_common_modules_props = dumped_modules_handler.get_modules_properties(dump_folder, 'iBank2')
    for module_name, module_props in gl_common_modules_props.items():
        try:
            # Разрешить препроцессор, избавиться от областей
            preproc = preproc1c.Preprocessor1C(gl_common_modules_props[module_name]['text_origin'])
            module_props['text_managed'] = preproc.execute("ТонкийКлиент", exclude_areas, ['НаКлиенте', 'Сервер'])
            module_props['text_managed'] = add_semicolon_after_preproc(module_props['text_managed'])
            module_props['struct_managed'] = parser1c.parser.parse(module_props['text_managed'])

            # Разрешить препроцессор, избавиться от областей
            preproc = preproc1c.Preprocessor1C(gl_common_modules_props[module_name]['text_origin'])
            module_props['text_ordinary'] = preproc.execute('ТолстыйКлиентОбычноеПриложение', exclude_areas)
            module_props['struct_ordinary'] = parser1c.parser.parse(module_props['text_ordinary'])
        except:
            raise Exception("Ошибка при разборе модуля : " + module_name)
    return gl_common_modules_props


def get_functions_description(gl_form_props, gl_common_modules_props, gl_ep_module):
    """
     Формирование общего списка процедур и функций во всех общих модулях и модулях форм.
     В соотвествие имени каждой процедуры/функции ставится её описание типа strct1c.Function.
     Этот список будет использован в дальнейшем для различных случаев, например,
     фильтрация системных вызовов от обращений к процедурам и функций общих модулей.
        Пример:
               'CommonModule.ОбработчикиСобытийФормКлиент.ПриОткрытии': <strct1c.Function object at 0x03520810>
               'FormManaged.Основная.ПриОткрытии': <strct1c.Function object at 0x03F64C10>
               'DataProcessor.EPName.СведенияОВнешнейОбработке': <strct1c.Function object at 0x03F5CF10>
    """
    gl_all_funcs_desc = dict()
    gl_all_funcs_desc[APP_TYPE_MANAGED] = dict()
    gl_all_funcs_desc[APP_TYPE_ORDINARY] = dict()

    # Заполнение списка процедур и функций модуля обработки
    for proc_func in gl_ep_module['struct'].proc_funcs_list:
        full_func_name = DATA_PROCESSOR + '.' + 'iBank2' + '.' + proc_func.name
        gl_all_funcs_desc[APP_TYPE_ORDINARY][full_func_name] = proc_func

    # Заполнение списка процедур и функций управляемых и обычных форм
    for form_name, form_props in gl_form_props.items():
        for proc_func in form_props['struct'].proc_funcs_list:
            if form_props['is_managed']:
                form_type = FORM_MANAGED
                app_type = APP_TYPE_MANAGED
            else:
                form_type = FORM_ORDINARY
                app_type = APP_TYPE_ORDINARY
            full_func_name = form_type + '.' + form_name + '.' + proc_func.name
            gl_all_funcs_desc[app_type][full_func_name] = proc_func

    for module_name, module_props in gl_common_modules_props.items():
        # заполнение списка процедур и функций общих модулей управляемого приложения
        for proc_func in module_props['struct_managed'].proc_funcs_list:
            full_func_name = COMMON_MODULE + '.' + module_name + "." + proc_func.name
            gl_all_funcs_desc[APP_TYPE_MANAGED][full_func_name] = proc_func
        # заполнение списка процедур и функций общих модулей обычного приложения
        for proc_func in module_props['struct_ordinary'].proc_funcs_list:
            full_func_name = COMMON_MODULE + '.' + module_name + "." + proc_func.name
            if full_func_name == 'CommonModule.iBank2_ОбщегоНазначения.ПолучитьЗначениеОбъектаОбработки':
                a = 1
            gl_all_funcs_desc[APP_TYPE_ORDINARY][full_func_name] = proc_func

    return gl_all_funcs_desc


def get_functions_subcalls(gl_form_props, gl_common_modules_props, gl_ep_module, gl_all_funcs_desc):
    """
    Формирование списка вызовов для каждой функции каждой формы и модуля.
    Эти списки будут использованы на следующем этапе для формирования модулей форм.
    Структура списка следующая:
      имя_формы.имя_функции: {имя_локальной_функции_формы, .., имя_модуля.имя_функции}
      имя_модуля.имя_функции: {имя_локальной_функции_модуля, .., имя_модуля.имя_функции}
    @param gl_form_props (dict): свойства форм: тексты, структура, тип приложения
    @param gl_common_modules_props (dict): свойства общих модулей: контекст, тексты, структура
    @param gl_ep_module (dict): свойства модуля обработки
    @param gl_all_funcs_desc (dict): ссылки описания всех функций
    @return:
    """
    gl_func_subcalls = dict()
    gl_func_subcalls[APP_TYPE_MANAGED] = dict()
    gl_func_subcalls[APP_TYPE_ORDINARY] = dict()

    all_funcs_desc_lower = dict()
    all_funcs_desc_lower[APP_TYPE_MANAGED] = set()
    all_funcs_desc_lower[APP_TYPE_ORDINARY] = set()
    for app_type, funcs_desc in gl_all_funcs_desc.items():
        all_funcs_desc_lower[app_type] = [full_func_name.lower() for full_func_name in funcs_desc]

    # заполняет gl_func_subcalls по процедурам и функциями модуля обработки
    for proc_func in gl_ep_module['struct'].proc_funcs_list:
        sub_calls_dict = get_sub_call_list(gl_all_funcs_desc[APP_TYPE_ORDINARY], all_funcs_desc_lower[APP_TYPE_ORDINARY],
                                           proc_func.body.statements, DATA_PROCESSOR, "iBank2")
        full_func_name = DATA_PROCESSOR + '.' + 'iBank2' + '.' + proc_func.name
        gl_func_subcalls[APP_TYPE_ORDINARY][full_func_name] = sub_calls_dict

    # цикл заполняет gl_func_subcalls по процедурам и функциями форм
    for form_name, form_props in gl_form_props.items():
        for proc_func in form_props['struct'].proc_funcs_list:
            if form_props['is_managed']:
                form_type = FORM_MANAGED
                app_type = APP_TYPE_MANAGED
            else:
                form_type = FORM_ORDINARY
                app_type = APP_TYPE_ORDINARY
            sub_calls_dict = get_sub_call_list(gl_all_funcs_desc[app_type], all_funcs_desc_lower[app_type],
                                               proc_func.body.statements, form_type, form_name)
            full_func_name = form_type + '.' + form_name + '.' + proc_func.name
            gl_func_subcalls[app_type][full_func_name] = sub_calls_dict

    # цикл заполняет gl_func_subcalls по процедурам и функциями общих модулей
    for module_name, module_props in gl_common_modules_props.items():
        for proc_func in module_props['struct_managed'].proc_funcs_list:
            sub_calls_dict = get_sub_call_list(gl_all_funcs_desc[APP_TYPE_MANAGED],
                                               all_funcs_desc_lower[app_type],
                                               proc_func.body.statements, COMMON_MODULE, module_name)
            full_func_name = COMMON_MODULE + '.' + module_name + '.' + proc_func.name
            gl_func_subcalls[APP_TYPE_MANAGED][full_func_name] = sub_calls_dict
        for proc_func in module_props['struct_ordinary'].proc_funcs_list:
            sub_calls_dict = get_sub_call_list(gl_all_funcs_desc[APP_TYPE_ORDINARY],
                                               all_funcs_desc_lower[app_type],
                                               proc_func.body.statements, COMMON_MODULE, module_name)
            full_func_name = COMMON_MODULE + '.' + module_name + '.' + proc_func.name
            gl_func_subcalls[APP_TYPE_ORDINARY][full_func_name] = sub_calls_dict
    return gl_func_subcalls

def update_local_calls_to_common(gl_func_subcalls):
    """
    Выполняет замену вызовов функций как локальных на вызовы с обращением через общий модуль.
    @param gl_func_subcalls (dict): список вызовов функций для каждой функции приложения
    @return None:
    """
    for app_type, func_calls in gl_func_subcalls.items():
        for full_func_name, sub_calls_dict in func_calls.items():
            for called_func_name, sub_calls_list in sub_calls_dict.items():
                for index in range(len(sub_calls_list)):
                    sub_call = sub_calls_list[index]
                    if isinstance(sub_call, strct1c.FuncCall):
                        parts = called_func_name.split('.')
                        if parts[0] == COMMON_MODULE:
                            owner = strct1c.get_owner(sub_call)
                            new_call = strct1c.DottedExpression(strct1c.Identifier(parts[1]))
                            new_call.append(sub_call)
                            strct1c.set_owner(new_call, owner)
                            strct1c.set_owner(sub_call, new_call)
                            owner.replace_obj(sub_call, new_call)
                            sub_calls_list[index] = new_call

def get_primary_context(dump_folder, exclude_areas):

    context = ContextType()
    # Получение текстов и структуры модулей обычного и управляемого приложения
    context.gl_app_module = get_application_module_props(dump_folder, exclude_areas)

    # Получение текстов и структуры модуля обработки
    context.gl_ep_module = get_processor_module_props(dump_folder, exclude_areas)

    # Получение текстов и структуры модулей форм
    context.gl_form_props = get_form_properties(dump_folder, exclude_areas)

    # Получение текстов и структуры общих модулей
    context.gl_common_modules_props = get_common_modules_properties(dump_folder, exclude_areas)

    # Формирование общего списка всех процедур и функций во всех модулях
    context.gl_all_funcs_desc = get_functions_description(context.gl_form_props,
                                                          context.gl_common_modules_props,
                                                          context.gl_ep_module)

    # Содержит список вызовов для каждой процедуры/функции во всех общих модулях и модулях форм
    context.gl_func_subcalls = get_functions_subcalls(context.gl_form_props,
                                                      context.gl_common_modules_props,
                                                      context.gl_ep_module,
                                                      context.gl_all_funcs_desc)

    # Изменить все локальные вызовы на обращение через общий модуль
    update_local_calls_to_common(context.gl_func_subcalls)
    return context

def add_semicolon_after_preproc(module_text):
    """
     Вставка символа точки с запятой после инструкции препроцессора #КонецЕсли.
     Это нужно для дальнейшей успешной загрузки модуля в синтаксический процессор.
     В сущности инструкции препроцессора не являются инструкциями, поэтому
     не завершаются точкой с запятой в коде 1С. Но для удобства обработки кода
     с использованием синтаксического процессора 1Сика они считаются инструкциями,
     такими же как if .. else .. endif, и поэтому должны оканчиваться точкой с запятой.
    @param module_text (str): текст содержащий инструкции препроцессора
    @return (str): новый текст, в котором после каждой завершающей инструкции препроцессора
                   добавлена точка с запятой на новой строке
    """
    pos = 0
    while True:
        pos = module_text.find('#КонецЕсли', pos)
        if pos == -1:
            break
        module_text = module_text[0:pos + 10] + '\n;' + module_text[pos + 10:]
        pos += 10 + 3;
    return module_text


def get_sub_call_list(all_funcs_set, all_funcs_set_in_lower, statements, module_type, module_name):
    '''
    По переданному описанию функции составляет список вызываемых из неё процедур и функций.
    @param proc_func (strct1c.Function): описание функций
    @param module_type (str): тип модуля: CommonModule, FormManaged, FormOrdinary
    @param module_name (str): имя общего модуля или формы
    @return (set): список вызываемый функций с полным путем к ним: CommonModule.<имя модуля>.<имя процедуры/функции>
    '''

    result = dict()
    # Возвращаются все вызовы вида: Ф(..) или ID.Ф(..).
    # Среди них могут быть встроенные функции и вызовы функий от объектов, например:
    #   НСтр(..),
    func_list = utils.get_statements_call_list(statements)
    for func_rec in func_list:
        func_name_called = func_rec[1]
        if func_name_called.find('.') > 0:
            # вызов разделенный точкой - обращение к функции другого общего модуля
            full_func_name_called = "CommonModule" + "." + func_name_called
        else:
            # обращение к функции этого модуля
            full_func_name_called = module_type + "." + module_name + "." + func_name_called
        # отбираем только функции модулей (без встроенных функций)
        if full_func_name_called.lower() in all_funcs_set_in_lower:
            for name in all_funcs_set:
                if name.lower() == full_func_name_called.lower():
                    full_func_name_called = name
                    break
            # в функции может быть несколько обращений к одной и тойже (другой) функции
            val = result.get(full_func_name_called, [])
            val.append(func_rec[0])
            result[full_func_name_called] = val
    return result
