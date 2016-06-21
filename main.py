# -*- coding: utf-8 -*-

import copy
import pickle
import parser1c
import preproc1c
import strct1c
import dumped_modules_handler
import utils
import os
import locsettings

# Используется для отбора среди обработок нужной
PROCESSOR_NAME = "iBank2"

# Использовать кеширование, в этом случае некоторые структуры данных будут выгружены на диск
# Для того что бы в следующий раз не вычислять их
CACHE_MODE_ON = True

TODO_DUMP_FOLDER = "dump"

FORM_MANAGED = 'FormManaged'
FORM_ORDINARY = 'FormOrdinary'
COMMON_MODULE = 'CommonModule'
APP_TYPE_MANAGED = 'managed'
APP_TYPE_ORDINARY = 'ordinary'

# Cписок вырезаемых из кода областей.
# Все остальные области остануться "как есть" с удаленными обрамлениями областей.
# todo должен параметризоваться
EXCLUDE_AREAS = ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"]

if CACHE_MODE_ON and os.path.isfile('init_stage.pickle'):
    with open('init_stage.pickle', 'rb') as f:
        (gl_app_module, gl_form_props, gl_common_modules_props, gl_all_funcs_desc, gl_func_subcalls) = pickle.load(f)
else:
##############################################################################################################
# Шаг №1. Получение текста модулей форм, общих модулей и модулей управляемого и обычного приложений.

    gl_app_module = dict()
    gl_app_module['ordinary_app_text_origin'] = open(os.path.join(TODO_DUMP_FOLDER, 'Конфигурация.МодульОбычногоПриложения.txt'), encoding='utf-8').read()
    gl_app_module['managed_app_text_origin'] = open(os.path.join(TODO_DUMP_FOLDER, 'Конфигурация.МодульУправляемогоПриложения.txt'), encoding='utf-8').read()

    gl_form_props = dumped_modules_handler.get_forms_properties(TODO_DUMP_FOLDER, 'iBank2')
    gl_common_modules_props = dumped_modules_handler.get_modules_properties(TODO_DUMP_FOLDER, 'iBank2')

##############################################################################################################
# Шаг №2. Разделение кода общих модулей на две части - для обычного и управляемого приложения.
#          Так же выполняется удаление областей и производится получение структуры модулей.

    # Препроцессинг модуля обычного приложения.
    preproc = preproc1c.Preprocessor1C(gl_app_module["ordinary_app_text_origin"])
    gl_app_module["ordinary_app_text"] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS)
    gl_app_module["ordinary_app_struct"] = parser1c.parser.parse(gl_app_module["ordinary_app_text"])

    # Препроцессинг модуля управляемого приложения.
    preproc = preproc1c.Preprocessor1C(gl_app_module["managed_app_text_origin"])
    gl_app_module["managed_app_text"] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS)
    gl_app_module["managed_app_struct"] = parser1c.parser.parse(gl_app_module["managed_app_text"])

    for form_name, form_props in gl_form_props.items():
        context = "ТонкийКлиент" if form_props['is_managed'] else "ТолстыйКлиентОбычноеПриложение"
        # Выполнить препроцессинг, избавиться от областей
        preproc = preproc1c.Preprocessor1C(form_props['text_origin'])
        new_text = preproc.execute(context, EXCLUDE_AREAS, ["НаКлиенте"])
        new_text = utils.add_semicolon_after_preproc(new_text)
        form_props['text'] = new_text
        # Получить синтаксическую структуру модуля
        form_props['struct'] = parser1c.parser.parse(new_text)

    for module_name, module_props in gl_common_modules_props.items():
        # Разрешить препроцессор, избавиться от областей
        preproc = preproc1c.Preprocessor1C(gl_common_modules_props[module_name]['text_origin'])
        try:
            module_props['text_managed'] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS, ["НаКлиенте"])
            module_props['text_managed'] = utils.add_semicolon_after_preproc(module_props['text_managed'])
            module_props['struct_managed'] = parser1c.parser.parse(module_props['text_managed'])

            module_props['text_ordinary'] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS,
                                                            ["НаКлиенте"])
            module_props['text_ordinary'] = utils.add_semicolon_after_preproc(module_props['text_ordinary'])
            module_props['struct_ordinary'] = parser1c.parser.parse(module_props['text_ordinary'])
        except:
            raise Exception("Ошибка при разборе модуля : " + module_name)

######################################################################################################
# Шаг №3. Формирование общего списка процедур и функций во всех общих модулях и модулях форм.
#          В соотвествие имени каждой процедуры/функции ставится её описание типа strct1c.Function.
#          Этот список будет использован в дальнейшем для различных случаев, например,
#          фильтрация системных вызовов от обращений к процедурам и функций общих модулей.
#
#          Пример:
#            'CommonModule.ОбработчикиСобытийФормКлиент.ПриОткрытии': <strct1c.Function object at 0x03520810>
#            'FormManaged.Основная.ПриОткрытии': <strct1c.Function object at 0x03F64C10>

    # Содержит общий список всех процедур и функций во всех модулях
    gl_all_funcs_desc = dict()
    gl_all_funcs_desc[APP_TYPE_MANAGED] = dict()
    gl_all_funcs_desc[APP_TYPE_ORDINARY] = dict()

    # Заполнение списка процедур и функций управляемых и обычных форм
    for form_name, form_props in gl_form_props.items():
        for proc_func in form_props['struct'].proc_funcs_list:
            if form_props['is_managed']:
                form_type = FORM_MANAGED
                app_type = APP_TYPE_MANAGED
            else:
                form_type = FORM_ORDINARY
                app_type = APP_TYPE_ORDINARY
            fill_form_name = form_type + '.' + form_name + '.' + proc_func.name
            gl_all_funcs_desc[app_type][fill_form_name] = proc_func

    for module_name, module_props in gl_common_modules_props.items():
        # заполнение списка процедур и функций общих модулей управляемого приложения
        for proc_func in module_props['struct_managed'].proc_funcs_list:
            full_module_name = COMMON_MODULE + '.' + module_name + "." + proc_func.name
            gl_all_funcs_desc[APP_TYPE_MANAGED][full_module_name] = proc_func
        # заполнение списка процедур и функций общих модулей обычного приложения
        for proc_func in module_props['struct_ordinary'].proc_funcs_list:
            full_module_name = COMMON_MODULE + '.' + module_name + "." + proc_func.name
            gl_all_funcs_desc[APP_TYPE_ORDINARY][full_module_name] = proc_func

######################################################################################################
# Шаг №4. Формирование списка вызовов для каждой функции каждой формы и модуля.
#          Эти списки будут использованы на следующем этапе для формирования модулей форм.
#          Структура списка следующая:
#            имя_формы.имя_функции: {имя_локальной_функции_формы, .., имя_модуля.имя_функции}
#            имя_модуля.имя_функции: {имя_локальной_функции_модуля, .., имя_модуля.имя_функции}

    # Содержит список вызовов для каждой процедуры/функции во всех общих модулях и модулях форм
    gl_func_subcalls = dict()
    gl_func_subcalls[APP_TYPE_MANAGED] = dict()
    gl_func_subcalls[APP_TYPE_ORDINARY] = dict()

    all_funcs_desc_lower = dict()
    all_funcs_desc_lower[APP_TYPE_MANAGED] = set()
    all_funcs_desc_lower[APP_TYPE_ORDINARY] = set()
    for app_type, funcs_desc in gl_all_funcs_desc.items():
        all_funcs_desc_lower[app_type] = [full_func_name.lower() for full_func_name in funcs_desc]

    # цикл заполняет gl_func_subcalls по процедурам и функциями форм
    for form_name, form_props in gl_form_props.items():
        for proc_func in form_props['struct'].proc_funcs_list:
            if form_props['is_managed']:
                form_type = FORM_MANAGED
                app_type = APP_TYPE_MANAGED
            else:
                form_type = FORM_ORDINARY
                app_type = APP_TYPE_ORDINARY
            sub_calls_dict = utils.get_sub_call_list(gl_all_funcs_desc[app_type], all_funcs_desc_lower[app_type],
                                                     proc_func.body.statements, form_type, form_name)
            full_func_name = form_type + '.' + form_name + '.' + proc_func.name
            gl_func_subcalls[app_type][full_func_name] = sub_calls_dict

    # цикл заполняет gl_func_subcalls по процедурам и функциями общих модулей
    for module_name, module_props in gl_common_modules_props.items():
        for proc_func in module_props['struct_managed'].proc_funcs_list:
            sub_calls_dict = utils.get_sub_call_list(gl_all_funcs_desc[APP_TYPE_MANAGED], all_funcs_desc_lower[app_type],
                                                     proc_func.body.statements, COMMON_MODULE, module_name)
            full_func_name = COMMON_MODULE + '.' + module_name + '.' + proc_func.name
            gl_func_subcalls[APP_TYPE_MANAGED][full_func_name] = sub_calls_dict
        for proc_func in module_props['struct_ordinary'].proc_funcs_list:
            sub_calls_dict = utils.get_sub_call_list(gl_all_funcs_desc[APP_TYPE_ORDINARY], all_funcs_desc_lower[app_type],
                                                     proc_func.body.statements, COMMON_MODULE, module_name)
            full_func_name = COMMON_MODULE + '.' + module_name + '.' + proc_func.name
            gl_func_subcalls[APP_TYPE_ORDINARY][full_func_name] = sub_calls_dict


##############################################################################################################
# Шаг 4а. Изменить все локальные вызовы на обращение через общий модуль.
    #strct1c.get_owner('')
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


    if CACHE_MODE_ON:
        with open('init_stage.pickle', 'wb') as f:
            pickle.dump((gl_app_module, gl_form_props, gl_common_modules_props, gl_all_funcs_desc, gl_func_subcalls), f)

##############################################################################################
# Шаг 5. Формирование списка процедур и функций общих модулей для переноса в основную форму.
#        Этот список состоит из таких пр./ф которые непосредственно учавствуют в цепочке вызова,
#        а так же учавствуют в цепочке вызова косвенно, например через вызов Выполнить(..).
#

# Содержит список функций для переноса в основную форму / модуль
# todo сперва перенос в основную управляемую форму
gl_funcs_to_move_primary = set()

for full_func_name in gl_func_subcalls[APP_TYPE_MANAGED]:
    parts = full_func_name.split('.')
    if parts[0] == FORM_MANAGED and parts[1].lower() == 'основная':
        utils.fill_main_module_calls(gl_funcs_to_move_primary, gl_func_subcalls[APP_TYPE_MANAGED], full_func_name)

###################################################################################################
# Шаг 5а. Некоторые процедуры/функции вызываются особым образом через фукнкции
#         ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
#         Например:
#           СоздатьОбъектОписанияОповещения("ВызватьФункцию", "Subsys_ОбщегоНазначенияКлиент")
#         Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
#         переносимых в основную форму.
#         Кроме того, из за способа вызова эти функции должны оставаться экспортными.

gl_funcs_to_move_primary_spec = utils.find_spec_calls(gl_func_subcalls[APP_TYPE_MANAGED], gl_funcs_to_move_primary)

for full_func_name in gl_funcs_to_move_primary_spec:
    if not full_func_name in gl_funcs_to_move_primary:
        gl_funcs_to_move_primary.add(full_func_name)
        utils.fill_main_module_calls(gl_funcs_to_move_primary, gl_func_subcalls[APP_TYPE_MANAGED], full_func_name)

###################################################################################################
# Шаг 6. Формирование списка процедур и функций для переноса во вспомогательные формы.
#        Порядок перенося процедур и функций следующий:
#         - безусловно переносятся все чисто серверные процедуры и функции
#         - клиентские процедуры и функции переносятся если не вызываются в основной форме,
#           если вызываются - вызов будет заменен на обращение к основной форме
#         - клиент-серверные процедуры и функции переносятся если есть только во вспомогательной форме
#           либо есть хотя бы один вызов из серверного контекста, если вызов такой процедуры или функции
#           присутствует в основной форме и при этом не вызывается из серверного контекста,
#           то вызов заменяется на обращение к основной форме.
#
#         На данном шаге заполняются две глобальные переменные:
#           gl_all_funcs_desc_to_move_secondary - процедуры и функции для переноса
#           gl_replace_calls_to_main_module - выполнять обращение через основную форму
#           gl_wrapper_for_client_server_funcs - клиент-серверный процедуры и функции для которых необходимо создать врапперы
#

if CACHE_MODE_ON and os.path.isfile('secondary_forms_move.pickle'):
    with open('secondary_forms_move.pickle', 'rb') as f:
        (gl_all_funcs_desc_to_move_secondary, gl_replace_calls_to_main_module, gl_wrapper_for_client_server_funcs) = pickle.load(f)
else:
    # Список процедур и функция для переноса во вспомогательные формы.
    #   ключ - имя формы
    #   значение - список функций для переноса
    gl_all_funcs_desc_to_move_secondary = dict()

    # Содержит список обращений к функциям, вызовы к которым необходимо заменить на обращение к основной форме:
    # Например, вызов
    #   System_ОбщегоНазначениеКлиентСервер.СообщитьПользователю(..)
    # Будет заменен в итоговой форме на:
    #   ОсновнаяФорма.СообщитьПользователю(..)
    # Структура переменной:
    #   ключ - имя формы
    #   значение - имя функции которую следует заменить
    gl_replace_calls_to_main_module = dict()

    # экспортные клиент-сервеные процедуры и функции не могут вызываться из основной формы, поэтому
    # необходимо делать экспортные врапперы таких процедур и функций, которые выполняются в клиентском контексте
    gl_wrapper_for_client_server_funcs = dict()

    for full_func_name, sub_calls in gl_func_subcalls[APP_TYPE_MANAGED].items():
        # full_func_name = 'FormManaged.СписокДоверенныхПолучателей.ДоверенныеПолучатели_ЭкземплярСистемыПриИзменении'
        # sub_calls = gl_func_subcalls[APP_TYPE_MANAGED].get(full_func_name)
        parts = full_func_name.split(".")
        if parts[0] != "FormManaged" or parts[1].lower() == "основная":
            # отбираем только вспомогательные формы
            continue

        force_move_to_form = False
        directive = gl_all_funcs_desc[APP_TYPE_MANAGED][full_func_name].directive.lower()
        if directive == "&насервере" or directive == "&насерверебезконтекста":
            # это "чистый" серверный вызов - все клиент-серверные процедуры
            # и функции необходимо переносить в форму
            force_move_to_form = True

        # имя формы, например "FormManaged.Письма"
        form_name = parts[0] + "." + parts[1]

        # инициализция списка для формы в gl_all_funcs_desc_to_move_secondary
        val = gl_all_funcs_desc_to_move_secondary.get(form_name, None)
        if val == None:
            gl_all_funcs_desc_to_move_secondary[form_name] = set()
            gl_replace_calls_to_main_module[form_name] = set()
            gl_wrapper_for_client_server_funcs[form_name] = set()

        for called_func_name in sub_calls:
            utils.update_secondary_form_calls(form_name, called_func_name, force_move_to_form,
                                              gl_common_modules_props,
                                              gl_func_subcalls[APP_TYPE_MANAGED],
                                              gl_funcs_to_move_primary,
                                              gl_all_funcs_desc_to_move_secondary,
                                              gl_replace_calls_to_main_module,
                                              gl_wrapper_for_client_server_funcs)

        # Одна и та же клиент-серверная процедура/функция может быть добавлена и в
        # gl_all_funcs_desc_to_move_secondary и в gl_replace_calls_to_main_module
        # Это может происходить в ситуациях, когда она:
        #   А) есть в основной форме
        #   Б) есть в клиенской цепочке вызова вспомогательной формы
        #   В) есть в серверной цепочке вызова вспомогательной формы
        # Такие процедуры/функции необходимо удалить из gl_replace_calls_to_main_module.
        for func_proc_name in gl_all_funcs_desc_to_move_secondary[form_name]:
            if func_proc_name in gl_replace_calls_to_main_module[form_name]:
                gl_replace_calls_to_main_module[form_name].remove(func_proc_name)

    if CACHE_MODE_ON:
        with open('secondary_forms_move.pickle', 'wb') as f:
            pickle.dump((gl_all_funcs_desc_to_move_secondary, gl_replace_calls_to_main_module,
             gl_wrapper_for_client_server_funcs), f)


###################################################################################################
# Шаг 6а. Некоторые процедуры/функции вызываются особым образом через фукнкции
#         ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
#         Например:
#           СоздатьОбъектОписанияОповещения("ВызватьФункцию", "ОбщегоНазначенияКлиент")
#         Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
#         переносимых в основную форму.
#         Кроме того, из за способа вызова эти функции должны оставаться экспортными.

gl_secondary_module_export_functions = dict()

for form_name, funcs_to_move in gl_all_funcs_desc_to_move_secondary.items():
    funcs_to_move_spec = utils.find_spec_calls(gl_func_subcalls[APP_TYPE_MANAGED], funcs_to_move)
    for called_func_name in funcs_to_move_spec:
        if not called_func_name in funcs_to_move:
            if not gl_secondary_module_export_functions.get(form_name):
                gl_secondary_module_export_functions[form_name] = set()
            gl_secondary_module_export_functions[form_name].add(called_func_name)
            utils.update_secondary_form_calls(form_name, called_func_name, False,
                                              gl_common_modules_props,
                                              gl_func_subcalls[APP_TYPE_MANAGED],
                                              gl_funcs_to_move_primary,
                                              gl_all_funcs_desc_to_move_secondary,
                                              gl_replace_calls_to_main_module,
                                              gl_wrapper_for_client_server_funcs)

###############################################################################################
# Шаг 6б. Процедуры и функции использующиеся во вспомогательных формах остаются только в
#         основной форме. Это сделано для сокращения числа переносимого кода во вспомогательные формы.
#         Такие процедуры и функции основной формы необходимо оставить экспортными.


# Функции из основной формы которые должны оставаться экспортными,
# так как к ним есть обращение из вспомогательных форм.
gl_main_module_export_functions = set()
for form_name, funcs_set in gl_replace_calls_to_main_module.items():
    for full_func_name in funcs_set:
        gl_main_module_export_functions.add(full_func_name)

# Некоторые процедуры и функции вспомогательных формы должны остаться экспортными потому что
# к ним проивзодится обращение через инструкцию Выполнить(..)
# Например:
#   Выполнить("Форма.КакаяТоПроцедура")
for full_func_name in gl_funcs_to_move_primary_spec:
    gl_main_module_export_functions.add(full_func_name)

# todo для универсальности должно параметризоваться и вычисляться подвызовы
func_name_get_main_module = 'CommonModule.iBank2_ОбщегоНазначенияКлиент.ПолучитьОсновногоВладельцаФормы'

st = strct1c.JumpStatemets('Возврат', strct1c.Identifier("__ОсновнаяФорма"))
st_ifelse_cond = strct1c.BinaryExpr(strct1c.Identifier('__ОсновнаяФорма'), strct1c.Undefined(), "<>")
st_ifelse = strct1c.IfElseStatement(st_ifelse_cond, [st], [])
st_asgn = strct1c.StatementAssignment(strct1c.Identifier('__ОсновнаяФорма'), strct1c.Identifier('ОсновнаяФорма'))

statements = gl_all_funcs_desc[APP_TYPE_MANAGED][func_name_get_main_module].body.statements
statements.insert(0, st_ifelse)
statements.insert(len(statements) - 1, st_asgn)

for form_name, funcs_to_move in gl_all_funcs_desc_to_move_secondary.items():
    funcs_to_move.add(func_name_get_main_module)
    # for sub_call_func_name in gl_func_subcalls[APP_TYPE_MANAGED][func_name_get_main_module]:
    #     utils.update_secondary_form_calls(form_name, sub_call_func_name, False,
    #                                         gl_common_modules_props,
    #                                         gl_func_subcalls[APP_TYPE_MANAGED],
    #                                         gl_funcs_to_move_primary,
    #                                         gl_all_funcs_desc_to_move_secondary,
    #                                         gl_replace_calls_to_main_module,
    #                                         gl_wrapper_for_client_server_funcs)

###################################################################################################
# Шаг 7. Перенос процедур и функций в основную форму. Перенос осуществляется через добавление
#        в структуру кода основной формы (proc_funcs_list) процедур и функций отмеченных к переносу,
#        а так же удаление обращений к общим модулям.
#

# Список процедур и функций основной управляемой формы
main_form_struct = gl_form_props['Основная']['struct']

utils.copy_functions_to_form(main_form_struct, gl_funcs_to_move_primary,
                             gl_main_module_export_functions, gl_all_funcs_desc[APP_TYPE_MANAGED],
                             gl_common_modules_props)
utils.handle_form_module_func_proc(main_form_struct, 'FormManaged.Основная', gl_common_modules_props)

##############################################################################################################
# Шаг 7а. Добавление врапперов для клиент-серверных функций

make_wrapper_set = set()
for form_name, proc_func_set in gl_wrapper_for_client_server_funcs.items():
    for full_func_name in proc_func_set:
        if full_func_name in gl_replace_calls_to_main_module[form_name]:
            make_wrapper_set.add(full_func_name.split(".")[2])

# Подготовим два шаблона врапера - для вызова процедуры и вызова функции
fc = strct1c.FuncCall('<origin_proc_name>', [])
st_func_call = strct1c.StatementFuncCall(fc)
proc_body = strct1c.FuncBody([], [st_func_call])
wrapper_proc = strct1c.Function(False, True, '&НаКлиенте', '<origin_proc_name>_wrapper', [], proc_body)
# &НаКлиенте
# Процедура <origin_proc_name>_wrapper() Экспорт
#     <origin_proc_name>();
# КонецПроцедуры

st_return = strct1c.JumpStatemets('Возврат', fc)
func_body = strct1c.FuncBody([], [st_return])
wrapper_func = strct1c.Function(True, True, '&НаКлиенте', '<origin_func_name>_wrapper', [], func_body)
# &НаКлиенте
# Функция <origin_func_name>_wrapper() Экспорт
#     Возврат <origin_proc_name>();
# КонецФункции

# Отыскиваем в основной форме процедуры и функции, для которых нужно сделать враппер
# и создаем его, на основе параметров функции.
for func_proc_desc in main_form_struct.proc_funcs_list:
    if func_proc_desc.name in make_wrapper_set:
        func_proc_desc.is_export = False
        wrapper = copy.deepcopy(wrapper_func if func_proc_desc.is_function else wrapper_proc)
        wrapper.name = func_proc_desc.name + "_wrapper"
        wrapper.vars_list = copy.deepcopy(func_proc_desc.vars_list)
        st = wrapper.body.statements[0]
        fc = st.second_param if func_proc_desc.is_function else st.statement
        fc.name = func_proc_desc.name
        for var_decl in wrapper.vars_list:
            fc.param_list.append(strct1c.Identifier(var_decl.var_name))
        main_form_struct.proc_funcs_list.append(wrapper)

#########################################################################################################
# Шаг 7б. Замена ссылок на некоторые глобальные переменные на обращения особого вида
#         Например, гл_Subsys_ИмяФайлаОбработки => Объект.КэшДанных.ИмяОбработки
#

# todo соотвествие для замен брать из файла настроек
replacements = {"гл_iBank2_ИмяФайлаОбработки": "Объект.КэшДанных.ИмяОбработки",
                "гл_iBank2_РежимРаботы": "Объект.КэшДанных.РежимРаботы"}

replacements = { key.lower(): val for key, val in replacements.items()}
filter={x for x in replacements}

id_call_list = []
for func_proc_desc in main_form_struct.proc_funcs_list:
    id_call_list += utils.get_statements_call_list(func_proc_desc.body.statements, obj_type="id", filter=filter)

for rec in id_call_list:
    id_name = rec[1]
    if id_name.lower() in replacements and isinstance(rec[0], strct1c.Identifier):
        rec[0].id = replacements[id_name.lower()]

########################################################################################################
# Шаг 7г. Перенос в модуль основной формы глобальных переменных.

for gl_var_desc in gl_app_module["managed_app_struct"].global_vars_list:
    if PROCESSOR_NAME.lower() in gl_var_desc.vars_list[0].name.lower():
        gl_var_desc_new = copy.deepcopy(gl_var_desc)
        gl_var_desc_new.directive = "&НаКлиенте"
        gl_form_props['Основная']['struct'].global_vars_list.append(gl_var_desc_new)

gl_form_props['Основная']['text'] = strct1c.get_text(gl_form_props['Основная']['struct'])

##############################################################################################
# Шаг. 8. Перенос во вспомогательные формы

if CACHE_MODE_ON and os.path.isfile('gl_form_props_after_make_module_text.pickle'):
    with open('gl_form_props_after_make_module_text.pickle', 'rb') as f:
        gl_form_props = pickle.load(f)
else:
    for full_form_name, funcs_to_move in gl_all_funcs_desc_to_move_secondary.items():
        form_name = full_form_name.split(".")[1]
        form_props = gl_form_props[form_name]
        if not form_props['is_managed']:
            continue
        form_struct = form_props['struct']

        var_desc = strct1c.VarDesc("__ОсновнаяФорма", False)
        var_declaration = strct1c.VariablesDeclaration([var_desc], '&НаКлиенте')
        form_struct.global_vars_list.append(var_declaration)

        # todo вместо третьего параметра set() нужно передать набор функций которые должны
        # оставаться экспортными - см. особые случаи типа СоздатьОбъектОписанияОповещения
        utils.copy_functions_to_form(form_struct, funcs_to_move, gl_secondary_module_export_functions.get(full_form_name, set()),
                                     gl_all_funcs_desc[APP_TYPE_MANAGED],
                                     gl_common_modules_props)

        utils.handle_form_module_func_proc(form_struct, full_form_name, gl_common_modules_props,
                                           gl_replace_calls_to_main_module,
                                           gl_wrapper_for_client_server_funcs)

        new_form_text = strct1c.get_text(form_struct)

        for gl_var_desc in gl_app_module["managed_app_struct"].global_vars_list:
            if PROCESSOR_NAME.lower() in gl_var_desc.vars_list[0].name.lower():
                var_name = gl_var_desc.vars_list[0].name;
                new_func_call_text = "ПолучитьОсновногоВладельцаФормы(ЭтаФорма)." + var_name
                new_form_text = new_form_text.replace(var_name, new_func_call_text)

        gl_form_props[form_name]['text'] = new_form_text

    if CACHE_MODE_ON:
        with open('gl_form_props_after_make_module_text.pickle', 'wb') as f:
            pickle.dump(gl_form_props, f)

#######################################################################################################
# Шаг 9. Локализация.

loc_dict = locsettings.get_localization_settings('ru')
for form_name, form_props in gl_form_props.items():
   # todo пока только управляемые формы
   if not form_props['is_managed']:
       continue
   module_text = form_props['text']
   for loc_key, loc_val in loc_dict.items():
       module_text = module_text.replace("{"+loc_key+"}", loc_val)
   form_props['text'] = module_text

# выгрузка подготовленных текстов на диск
for form_name, form_props in gl_form_props.items():
    if form_props['is_managed']:
        file_name = form_props['file_name']
        text = form_props['text']
        file = open(os.path.join('dump.new', file_name), 'w', encoding='utf-8')
        file.write(u'\ufeff')
        file.write(text)
    else:
        pass

# При переносе функций во вспомогательную форму необходимо удалить признак экспортной функции.
# gl_all_funcs_desc_to_move_secondary
# gl_replace_calls_to_main_module

# Во вспомогательных управляемых формах
# а) добавить переменную модуля формы ОсновнаяФорма
# б) в обработчик ПриОткрытии (должен быть добавлен во все формы) добавить вызов ОсновнаяФорма = ПолучитьОсновнуюФорму() (вместо ПолучитьОсновногоВладельцаФормы)
# в) во обращениях к основной форме вместо ПолучитьОсновногоВладельцаФормы() использовать ОсновнаяФорма


