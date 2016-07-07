# -*- coding: utf-8 -*-

from epfcomp.base_const import *
from epfcomp import locsettings
from epfcomp import move_funcs
from epfcomp import strct1c
from epfcomp import utils
import os.path

def get_main_form_func_name():
    '''
    Для обращения к процедурам и функциям основной формы в модуле вспомогательной формы должна присутствовать
    функция, которая бы вернула саму основную форму. Функция эта должна быть написана разработчиком самостоятельно.

    &НаКлиенте
    Функция ПолучитьОсновногоВладельцаФормы(Форма)
        ОсновнаяФормаНайдена = Ложь;
        ОсновнаяФорма = Форма;
        Пока ОсновнаяФорма <> Неопределено Цикл
            Попытка
                ОсновнаяФормаНайдена = ОсновнаяФорма.ЭтоОсновнаяФорма();
                Прервать;
            Исключение
            КонецПопытки;
            ОсновнаяФорма = ОсновнаяФорма.ВладелецФормы;
        КонецЦикла;
        Возврат ОсновнаяФорма;
    КонецФункции

    При переносе такая функция будет дополнена до:

    &НаКлиенте
    Функция ПолучитьОсновногоВладельцаФормы(Форма)
        Если __ОсновнаяФорма <> Неопределено Тогда    <----- оптимизация на случай множественных обращений
            Возврат __ОсновнаяФорма;     <------ в кода модуля формы будет добавлена переменная __ОсновнаяФорма
        КонецЕсли;
        ОсновнаяФормаНайдена = Ложь;
        ОсновнаяФорма = Форма;
        Пока ОсновнаяФорма <> Неопределено Цикл
            Попытка
                ОсновнаяФормаНайдена = ОсновнаяФорма.ЭтоОсновнаяФорма();
                Прервать;
            Исключение
            КонецПопытки;
            ОсновнаяФорма = ОсновнаяФорма.ВладелецФормы;
        КонецЦикла;
        __ОсновнаяФорма = ОсновнаяФорма;    <----- код будет добавлен механизмом сборки автоматически
        Возврат ОсновнаяФорма;
    КонецФункции

    @return (str): полный путь к функции, например:
                    'CommonModule.Subsys_ОбщегоНазначенияКлиент.ПолучитьОсновногоВладельцаФормы'
    '''
    return 'CommonModule.iBank2_ОбщегоНазначенияКлиент.ПолучитьОсновногоВладельцаФормы'
    #raise Exception('Не определена функция для обращения к общей форме')

def update_functions_to_move_primary_module(app_type, primary_module_config, context):

    # Некоторые функции вызываются неявно через Выполнить(..) - заполним их вручную
    functions_to_move_spec = find_spec_calls(primary_module_config.functions_to_move,
                                             context.gl_func_subcalls[app_type])

    for full_func_name in functions_to_move_spec:
        primary_module_config.export_functions.add(full_func_name)
        if full_func_name not in primary_module_config.functions_to_move:
            primary_module_config.functions_to_move.add(full_func_name)
            move_funcs.fill_direct_call_chain(primary_module_config.functions_to_move,
                                              context.gl_func_subcalls[app_type],
                                              full_func_name)

    if app_type == APP_TYPE_MANAGED:
        # некоторые функции содержат в названии префикс "гл_" - это признак того, что функцию
        # следует перенести в основную форму
        for full_func_name in context.gl_all_funcs_desc['managed']:
            if full_func_name.split('.')[2].lower().startswith("гл_") and \
                            full_func_name not in primary_module_config.functions_to_move:
                primary_module_config.functions_to_move.add(full_func_name)
                move_funcs.fill_direct_call_chain(primary_module_config.functions_to_move,
                                                  context.gl_func_subcalls[app_type],
                                                  full_func_name)
    pass


gl_special_calls = {"ПолучитьОписаниеОповещенияСВызовомФункции", "СоздатьОбъектОписанияОповещения"}
gl_special_calls = {name.lower() for name in gl_special_calls}

def find_spec_calls(functions_to_move, func_subcalls):
    """
    Некоторые процедуры/функции вызываются особым образом через фукнкции
    ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
    Например:
        СоздатьОбъектОписанияОповещения("ВызватьФункцию", "Subsys_ОбщегоНазначенияКлиент")
    Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
    переносимых в основную форму.
    Кроме того, из за способа вызова эти функции должны оставаться экспортными.
    @param gl_context: базовый контекст
    @param functions_to_move (set): список функций для перемещения в основную форму
    @return:
    """

    def fill_implicit_called_funcs(funcs_to_check):
        nonlocal implicit_called_funcs
        nonlocal func_subcalls
        global gl_special_calls
        for full_func_name in funcs_to_check:
            for called_func_name, calls_list in func_subcalls[full_func_name].items():
                called_func_name_short = called_func_name.split(".")[2]
                if called_func_name_short.lower() in gl_special_calls:
                    # Если вызывамая функция - это одна из тех что указаны в special_calls,
                    # требуется перенести ещё функцию указанную в параметре.
                    for call in calls_list:
                        if isinstance(call, strct1c.DottedExpression):
                            func_name = call.properties_list[1].param_list[0].value[0]
                            module_name = call.properties_list[1].param_list[1].value[0]
                        else:
                            # к данному моменту обращения к локальным функциям были заменены
                            # на обращения к функциям общего модуля
                            raise Exception("Необработанный вызов : " + call)
                        sub_call_full_name = "CommonModule." + module_name + "." + func_name
                        for full_name_correct in func_subcalls:
                            # задаем корректное имя функции, "по описанию"
                            if full_name_correct.lower() == sub_call_full_name.lower():
                                sub_call_full_name = full_name_correct
                        if not sub_call_full_name in implicit_called_funcs:
                            implicit_called_funcs.add(sub_call_full_name)
                            fill_implicit_called_funcs([sub_call_full_name])

    implicit_called_funcs = set()
    fill_implicit_called_funcs(functions_to_move)
    return implicit_called_funcs

def update_funcs_to_move_secondary(secondary_forms_config, primary_form_config, context):
    """
     Некоторые процедуры/функции вызываются особым образом через фукнкции
     ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
     Например:
       СоздатьОбъектОписанияОповещения("ВызватьФункцию", "ОбщегоНазначенияКлиент")
     Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
     переносимых в основную форму.
     Кроме того, из за способа вызова эти функции должны оставаться экспортными.
     """
    for form_name, funcs_to_move in secondary_forms_config.functions_to_move_dict.items():
        funcs_to_move_spec = find_spec_calls(funcs_to_move, context.gl_func_subcalls[APP_TYPE_MANAGED])
        for called_func_name in funcs_to_move_spec:
            if not called_func_name in funcs_to_move:
                if not secondary_forms_config.export_functions.get(form_name):
                    secondary_forms_config.export_functions[form_name] = set()
                secondary_forms_config.export_functions[form_name].add(called_func_name)
                move_funcs.update_secondary_form_calls(form_name, called_func_name, False,
                                                       context,
                                                       secondary_forms_config,
                                                       primary_form_config.functions_to_move)
    pass


def handle_form_module_func_proc(func_proc_desc, sub_call_list):
    """
    Заменяет второй параметр в вызове функций ПолучитьОписаниеОповещенияСВызовомФункции,
    СоздатьОбъектОписанияОповещения на ЭтотОбъект.
    @param func_proc_desc:
    @param sub_call_list:
    @return:
    """
    for (call, called_func_name) in sub_call_list:
        # Если среди обращений к функциям есть специальные -
        # ПолучитьОписаниеОповещенияСВызовомФункции, СоздатьОбъектОписанияОповещения
        # то подменяем параметры на сборочные.
        parts = called_func_name.split(".")
        called_func_name_short = parts[0] if len(parts) == 1 else parts[1]
        if called_func_name_short.lower() in gl_special_calls:
            if isinstance(call, strct1c.DottedExpression):
                call.properties_list[1].param_list[1] = strct1c.Identifier('ЭтотОбъект')
            else:
                raise Exception("Необработанный вызов : " + call)
    pass


def update_primary_module_after_transfer(app_mode, module_struct):
    """
    Выполняет дополнение модуля основной формы после того как в неё были перенесены функции.
    @param module_struct: стуктура основной управляемой формы или модуля обработки
    @return:
    """

    # Замена ссылок на некоторые глобальные переменные на обращения особого вида
    # Например, гл_Subsys_ИмяФайлаОбработки => Объект.КэшДанных.ИмяОбработки

    if app_mode == APP_TYPE_MANAGED:
        replacements = {'гл_iBank2_ИмяФайлаОбработки': 'Объект.КэшДанных.ИмяОбработки',
                        'гл_iBank2_РежимРаботы': 'Объект.КэшДанных.РежимРаботы'}
    else:
        replacements = {'гл_iBank2_ИмяФайлаОбработки': 'ЭтотОбъект.КэшДанных.ИмяОбработки',
                        'гл_iBank2_РежимРаботы': 'ЭтотОбъект.КэшДанных.РежимРаботы'}

    replacements = {key.lower(): val for key, val in replacements.items()}
    filter = {x for x in replacements}

    id_call_list = []
    for func_proc_desc in module_struct.proc_funcs_list:
        id_call_list += utils.get_statements_call_list(func_proc_desc.body.statements, obj_type="id", filter=filter)

    for rec in id_call_list:
        id_name = rec[1]
        if id_name.lower() in replacements and isinstance(rec[0], strct1c.Identifier):
            rec[0].id = replacements[id_name.lower()]
    pass

def update_context(context):

    if os.path.isfile('Localization_3_5_RU.xml'):
        # выполнение локализации
        loc_dict = locsettings.get_localization_settings('ru')
        for form_name, form_props in context.gl_form_props.items():
           module_text = form_props['text']
           for loc_key, loc_val in loc_dict.items():
               module_text = module_text.replace("{"+loc_key+"}", loc_val)
           form_props['text'] = module_text

        module_text = context.gl_ep_module['text']
        for loc_key, loc_val in loc_dict.items():
            module_text = module_text.replace("{" + loc_key + "}", loc_val)
        context.gl_ep_module['text'] = module_text
