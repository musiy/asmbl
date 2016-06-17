# -*- coding: utf-8 -*-

import copy
import pickle
import parser1c
import preproc1c
import strct1c
import dumped_modules_handler
import utils
import os

# Используется для отбора среди обработок нужной
PROCESSOR_NAME = "iBank2"

# Использовать кеширование, в этом случае некоторые структуры данных будут выгружены на диск
# Для того что бы в следующий раз не вычислять их
CACHE_MODE_ON = True

TODO_DUMP_FOLDER = "dump"

FORM_MANAGED = 'formmanaged'
FORM_ORDINARY = 'formordinary'
COMMON_MODULE = 'commonmodule'

# Cписок вырезаемых из кода областей.
# Все остальные области остануться "как есть" с удаленными обрамлениями областей.
# todo должен параметризоваться
EXCLUDE_AREAS = ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"]

##############################################################################################################
# Первый этап - получение текста модулей форм, общих модулей и модулей управляемого и обычного приложений
#

gl_app_module = dict()
gl_app_module['ordinary_app_text_origin'] = open(os.path.join(TODO_DUMP_FOLDER, 'Конфигурация.МодульОбычногоПриложения.txt'), encoding='utf-8').read()
gl_app_module['managed_app_text_origin'] = open(os.path.join(TODO_DUMP_FOLDER, 'Конфигурация.МодульУправляемогоПриложения.txt'), encoding='utf-8').read()

gl_form_props = dumped_modules_handler.get_forms_properties('dump', 'iBank2')
gl_common_modules_props = dumped_modules_handler.get_modules_properties('dump', 'iBank2')

##############################################################################################################
# Шаг №1. Разделение кода общих модулей на две части - для обычного и управляемого приложения.
#          Так же выполняется удаление областей и производится получение структуры модулей.

# препроцессинг модуля обычного приложения
preproc = preproc1c.Preprocessor1C(gl_app_module["ordinary_app_text_origin"])
gl_app_module["ordinary_app_text"] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS)
gl_app_module["ordinary_app_struct"] = parser1c.parser.parse(gl_app_module["ordinary_app_text"])

# препроцессинг модуля управляемого приложения
preproc = preproc1c.Preprocessor1C(gl_app_module["managed_app_text_origin"])
gl_app_module["managed_app_text"] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS)
gl_app_module["managed_app_struct"] = parser1c.parser.parse(gl_app_module["managed_app_text"])

if CACHE_MODE_ON and os.path.isfile('gl_form_props_parse.pickle'):
    with open('gl_form_props_parse.pickle', 'rb') as f:
        gl_form_props = pickle.load(f)
else:
    for form_name, form_props in gl_form_props.items():
        context = "ТонкийКлиент" if form_props['is_managed'] else "ТолстыйКлиентОбычноеПриложение"
        # Выполнить препроцессинг, избавиться от областей
        preproc = preproc1c.Preprocessor1C(form_props['text_origin'])
        new_text = preproc.execute(context, EXCLUDE_AREAS, ["НаКлиенте"])
        new_text = utils.add_semicolon_after_preproc(new_text)
        form_props['text'] = new_text
        # Получить синтаксическую структуру модуля
        form_props['struct'] = parser1c.parser.parse(new_text)
    if CACHE_MODE_ON:
        with open('gl_form_props_parse.pickle', 'wb') as f:
            pickle.dump(gl_form_props, f)

if CACHE_MODE_ON and os.path.isfile('gl_common_modules_props.pickle'):
    with open('gl_common_modules_props.pickle', 'rb') as f:
        gl_common_modules_props = pickle.load(f)
else:
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

    if CACHE_MODE_ON:
        with open('gl_common_modules_props.pickle', 'wb') as f:
            pickle.dump(gl_common_modules_props, f)


######################################################################################################
# Шаг №2. Формирование общего списка процедур и функций во всех общих модулях и модулях форм.
#          В соотвествие имени каждой процедуры/функции ставится её описание типа strct1c.Function.
#          Этот список будет использован в дальнейшем для различных случаев, например,
#          фильтрация системных вызовов от обращений к процедурам и функций общих модулей.
#
#          Пример:
#            'CommonModule.ОбработчикиСобытийФормКлиент.ПриОткрытии': <strct1c.Function object at 0x03520810>
#            'FormManaged.Основная.ПриОткрытии': <strct1c.Function object at 0x03F64C10>


# Содержит общий список всех процедур и функций во всех модулях
gl_all_proc_funcs_managed = dict()
gl_all_proc_funcs_ordinary = dict()

# Заполнение списка процедур и функций управляемых и обычных форм
for form_name, form_props in gl_form_props.items():
    for proc_func in form_props['struct'].proc_func_list:
        key = form_name + '.' + proc_func.name
        if form_props['is_managed']:
            key = FORM_MANAGED + '.' + key
            gl_all_proc_funcs_managed[key.lower()] = proc_func
        else:
            key = FORM_ORDINARY + '.' + key
            gl_all_proc_funcs_ordinary[key.lower()] = proc_func

# заполнение списка процедур и функций общих модулей управляемого приложения
for module_name, module_props in gl_common_modules_props.items():
    for proc_func in module_props['struct_managed'].proc_func_list:
        key = COMMON_MODULE + '.' + module_name + "." + proc_func.name
        gl_all_proc_funcs_managed[key.lower()] = proc_func

# заполнение списка процедур и функций общих модулей обычного приложения
for module_name, module_props in gl_common_modules_props.items():
    for proc_func in module_props['struct_ordinary'].proc_func_list:
        key = COMMON_MODULE + '.' + module_name + "." + proc_func.name
        gl_all_proc_funcs_ordinary[key.lower()] = proc_func

######################################################################################################
# Шаг №3. Формирование списка вызовов для каждой функции каждой формы и модуля.
#          Эти списки будут использованы на следующем этапе для формирования модулей форм.
#          Структура списка следующая:
#            имя_формы.имя_функции: {имя_локальной_функции_формы, .., имя_модуля.имя_функции}
#            имя_модуля.имя_функции: {имя_локальной_функции_модуля, .., имя_модуля.имя_функции}

# Содержит список вызовов для каждой процедуры/функции во всех общих модулях и модулях форм
gl_func_calls = dict()
gl_func_calls_ordinary = dict()

if CACHE_MODE_ON and os.path.isfile('gl_func_calls.pickle'):
    with open('gl_func_calls.pickle', 'rb') as f:
        gl_func_calls = pickle.load(f)
else:
    # цикл заполняет gl_func_calls по процедурам и функциями форм
    for form_name, form_props in gl_form_props.items():
        for proc_func in form_props['struct'].proc_func_list:
            if form_props['is_managed']:
                key = FORM_MANAGED + '.' + form_name + '.' + proc_func.name
                sub_calls_dict = utils.get_proc_func_call_list(gl_all_proc_funcs_managed, proc_func, FORM_MANAGED, form_name)
                gl_func_calls[key.lower()] = sub_calls_dict
            else:
                key = FORM_ORDINARY + '.' + form_name + '.' + proc_func.name
                sub_calls_dict = utils.get_proc_func_call_list(gl_all_proc_funcs_ordinary, proc_func, FORM_ORDINARY, form_name)
                gl_func_calls_ordinary[key.lower()] = sub_calls_dict

    # цикл заполняет gl_func_calls по процедурам и функциями общих модулей
    for module_name, module_props in gl_common_modules_props.items():

        for proc_func in module_props['struct_managed'].proc_func_list:
            key = COMMON_MODULE + '.' + module_name + '.' + proc_func.name
            sub_calls_dict = utils.get_proc_func_call_list(gl_all_proc_funcs_managed, proc_func, COMMON_MODULE, module_name)
            gl_func_calls[key.lower()] = sub_calls_dict
        for proc_func in module_props['struct_ordinary'].proc_func_list:
            key = COMMON_MODULE + '.' + module_name + '.' + proc_func.name
            sub_calls_dict = utils.get_proc_func_call_list(gl_all_proc_funcs_ordinary, proc_func, COMMON_MODULE, module_name)
            gl_func_calls_ordinary[key.lower()] = sub_calls_dict

    if CACHE_MODE_ON:
        with open('gl_func_calls.pickle', 'wb') as f:
            pickle.dump(gl_func_calls, f)

# TODO изменить все локальные вызовы на обращение через общий модуль

##############################################################################################
# Шаг 4. Формирование списка процедур и функций общих модулей для переноса в основную форму.
#        Этот список состоит из таких пр./ф которые непосредственно учавствуют в цепочке вызова.
#        А так же учавствуют в цепочке вызова косвенно, например через вызов Выполнить(..).
#

# Содержит список функций для переноса в основную форму / модуль
# todo сперва перенос в основную управляемую форму
gl_all_proc_funcs_to_move_primary = set()

for func_name in gl_func_calls:
    parts = func_name.split('.')
    if parts[0] == FORM_MANAGED and parts[1].lower() == 'основная':
        utils.fill_main_module_calls(gl_all_proc_funcs_to_move_primary, gl_func_calls, func_name)

###################################################################################################
# Шаг 4а. Некоторые процедуры/функции вызываются особым образом через фукнкции
#         ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
#         Например:
#           СоздатьОбъектОписанияОповещения("ВызватьФункцию", "Subsys_ОбщегоНазначенияКлиен")
#         Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
#         переносимых в основную форму.
#         Кроме того, из за способа вызова эти функции должны оставаться экспортными.

# todo список особых процедур и функций необходимо параметризовать в файле конфигурации
gl_spec_replace_params = {"ПолучитьОписаниеОповещенияСВызовомФункции", "СоздатьОбъектОписанияОповещения"}
gl_spec_replace_params = {name.lower() for name in gl_spec_replace_params}

# Нельзя снимать признак экспортности с функций, которые вызываются через Выполнить(..).
# Переменная будет использована далее при изменении свойства экспортности при переносе функции в основную форму.
gl_func_to_add_spec = set()
utils.add_special_proc_funcs(gl_func_to_add_spec, gl_func_calls, gl_spec_replace_params, gl_all_proc_funcs_to_move_primary)

for full_func_name in gl_func_to_add_spec:
    if not full_func_name in gl_all_proc_funcs_to_move_primary:
        gl_all_proc_funcs_to_move_primary.add(full_func_name)
        utils.fill_main_module_calls(gl_all_proc_funcs_to_move_primary, gl_func_calls, full_func_name)

###################################################################################################
# Шаг 5. Формирование списка процедур и функций для переноса во вспомогательные формы.
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
#           gl_all_proc_funcs_to_move_secondary - процедуры и функции для переноса
#           gl_replace_calls_to_main_module - выполнять обращение через основную форму
#           gl_wrapper_for_client_server_funcs - клиент-серверный процедуры и функции для которых необходимо создать врапперы
#

def fill_secondary_form_calls(form_name, full_func_name, force_move_to_form):
    """
    Вычисляет процедуры и функции для переноса во вспомогательную форму.
    При этом, заполняет gl_all_proc_funcs_to_move_secondary - список функций для переноса.
    А так же заполняет gl_replace_calls_to_main_module - список функций для обращения через основной модуль.
    и gl_wrapper_for_client_server_funcs - список процедур и функций доступ к которым из воспомогательных форм
    будет производитсья через враппер.

    @param form_name (str): имя обрабатываемой формы
    @param full_func_name (str): функция из цепочки вызовов, на основе контекста модуля будет определяться
                                 следует ли переносить её во вспомогательную форму или заменять вызов
                                 на обращение к основной форме:
                                    клиентская - переносить, если нет в основной форме
                                    клиент-серверная - переносить, если нет в основной форме
                                    серверная - переносить всегда
    @param force_move_to_form (bool): признак безусловного перемещения процедуры/функции во второстепенную форму.
    @return:
    """
    if form_name == "FormManaged.ВыборБюджета" and full_func_name.find('ЭтоУТ_10_3') >= 0:
        a = 1
    if force_move_to_form:
        if full_func_name in gl_all_proc_funcs_to_move_secondary[form_name]:
            # если функция уже отмечена к переносу во вспомогательную форму - не продолжаем, что бы не зациклиться
            return
        # для серверной цепочки безусловно переносим процедуру/функцию во вспомогательную форму
        # это важно для клиент-серверных вызовов
        gl_all_proc_funcs_to_move_secondary[form_name].add(full_func_name)
        # безусловно помечаем все последующие вызовы
        new_force_move_to_form = force_move_to_form
    else:
        # Цепочка вызовов - клиентская, поэтому определяем по контексту и наличию в основной форме, переносить ли её.
        parts = full_func_name.split(".")
        module_props = gl_common_modules_props[parts[1]]
        new_force_move_to_form = module_props['is_server'] or module_props['is_client_server']
        if (module_props['is_client'] or module_props['is_client_server']) and full_func_name in gl_all_proc_funcs_to_move_primary:
            # если функция клиентская и при этом переносится в основную форму,
            # значит следует переадресовать вызов к основной форме
            gl_replace_calls_to_main_module[form_name].add(full_func_name)

            if module_props['is_client_server']:
                # при этом, если функция клиент-серверная, то для нее необходимо делать клиентский враппер
                gl_wrapper_for_client_server_funcs[form_name].add(full_func_name)
            # не имеет смысла просматривать дальше вызовы из функции, т.к. они уже есть в основной форме
            return
        else:
            # функция серверная, или клиентская/клиент серверная, и при этом не перенесена в основную форму
            if full_func_name in gl_all_proc_funcs_to_move_secondary[form_name]:
                # уходим от зацикливания
                return
            gl_all_proc_funcs_to_move_secondary[form_name].add(full_func_name)
    sub_call_list = gl_func_calls.get(full_func_name)
    for sub_call in sub_call_list:
        # sub_call это обращение к функции, например:
        #   CommonModule.System_ЗарплатныйПроект.ВыборПлатежногоПоручения_ПриСозданииНаСервере
        fill_secondary_form_calls(form_name, sub_call, new_force_move_to_form)


if CACHE_MODE_ON and os.path.isfile('gl_all_proc_funcs_to_move_secondary.pickle') \
        and os.path.isfile('gl_replace_calls_to_main_module.pickle') \
        and os.path.isfile('gl_wrapper_for_client_server_funcs.pickle'):
    with open('gl_all_proc_funcs_to_move_secondary.pickle', 'rb') as f:
        gl_all_proc_funcs_to_move_secondary = pickle.load(f)
    with open('gl_replace_calls_to_main_module.pickle', 'rb') as f:
        gl_replace_calls_to_main_module = pickle.load(f)
    with open('gl_wrapper_for_client_server_funcs.pickle', 'rb') as f:
        gl_wrapper_for_client_server_funcs = pickle.load(f)
else:
    # Список процедур и функция для переноса во вспомогательные формы.
    #   ключ - имя формы
    #   значение - список функций для переноса
    gl_all_proc_funcs_to_move_secondary = dict()

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

    for full_func_name in gl_func_calls:
        parts = full_func_name.split(".")
        if parts[0] != "FormManaged" or parts[1].lower() == "основная":
            # отбираем только вспомогательные формы
            continue

        force_move_to_form = False
        directive = gl_all_proc_funcs[full_func_name].directive.lower()
        if directive == "&насервере" or directive == "&насерверебезконтекста":
            # это "чистый" серверный вызов - все клиент-серверные процедуры
            # и функции необходимо переносить в форму
            force_move_to_form = True

        # имя формы, например "FormManaged.Письма"
        form_name = parts[0] + "." + parts[1]

        if form_name == "FormManaged.ВыборДоговора":
            a = 1

        # инициализция списка для формы в gl_all_proc_funcs_to_move_secondary
        val = gl_all_proc_funcs_to_move_secondary.get(form_name, None)
        if val == None:
            gl_all_proc_funcs_to_move_secondary[form_name] = set()
            gl_replace_calls_to_main_module[form_name] = set()
            gl_wrapper_for_client_server_funcs[form_name] = set()

        for sub_call in gl_func_calls[full_func_name]:
            fill_secondary_form_calls(form_name, sub_call, force_move_to_form)

        # Одна и та же клиент-серверная процедура/функция может быть добавлена и в
        # gl_all_proc_funcs_to_move_secondary и в gl_replace_calls_to_main_module
        # Это может происходить в ситуациях, когда она:
        #   А) есть в основной форме
        #   Б) есть в клиенской цепочке вызова вспомогательной формы
        #   В) есть в серверной цепочке вызова вспомогательной формы
        # Такие процедуры/функции необходимо удалить из gl_replace_calls_to_main_module.
        for func_proc_name in gl_all_proc_funcs_to_move_secondary[form_name]:
            if func_proc_name in gl_replace_calls_to_main_module[form_name]:
                gl_replace_calls_to_main_module[form_name].remove(func_proc_name)

    if CACHE_MODE_ON:
        with open('gl_all_proc_funcs_to_move_secondary.pickle', 'wb') as f:
            pickle.dump(gl_all_proc_funcs_to_move_secondary, f)
        with open('gl_replace_calls_to_main_module.pickle', 'wb') as f:
            pickle.dump(gl_replace_calls_to_main_module, f)
        with open('gl_wrapper_for_client_server_funcs.pickle', 'wb') as f:
            pickle.dump(gl_wrapper_for_client_server_funcs, f)

###############################################################################################
# Шаг 6а. Процедуры и функции использующиеся во вспомогательных формах остаются только в
#         основной форме. Это сделано для сокращения числа переносимого кода во вспомогательные формы.
#         Такие процедуры и функции основной формы необходимо оставить экспортными.

# Функции из основной формы которые должны оставаться экспортными,
# так как к ним есть обращение из вспомогательных форм.
gl_main_module_export_functions = set()
for form_name in gl_replace_calls_to_main_module:
    for full_func_name in gl_replace_calls_to_main_module[form_name]:
        gl_main_module_export_functions.add(full_func_name)

# Некоторые процедуры и функции вспомогательных формы должны остаться экспортными потому что
# к ним проивзодится обращение через инструкцию Выполнить(..)
# Например:
#   Выполнить("Форма.КакаяТоПроцедура")
for full_func_name in gl_func_to_add_spec:
    gl_main_module_export_functions.add(full_func_name)

# todo для универсальности должно параметризоваться и вычисляться подвызовы
call_name = 'CommonModule.iBank2_ОбщегоНазначенияКлиент.ПолучитьОсновногоВладельцаФормы'

st = strct1c.JumpStatemets('Возврат', strct1c.Identifier("__ОсновнаяФорма"))
st_ifelse_cond = strct1c.BinaryExpr(strct1c.Identifier('__ОсновнаяФорма'), strct1c.Undefined(), "<>")
st_ifelse = strct1c.IfElseStatement(st_ifelse_cond, [st], [])
st_asgn = strct1c.StatementAssignment(strct1c.Identifier('__ОсновнаяФорма'), strct1c.Identifier('ОсновнаяФорма'))

statements = gl_all_proc_funcs[call_name].body.statements
statements.insert(0, st_ifelse)
statements.insert(len(statements) - 1, st_asgn)

for form_name, funcs_to_move in gl_all_proc_funcs_to_move_secondary.items():
    # todo для универсальности должно параметризоваться и вычисляться подвызовы
    call_name = 'CommonModule.iBank2_ОбщегоНазначенияКлиент.ПолучитьОсновногоВладельцаФормы'
    force_move_to_form = False
    directive = gl_all_proc_funcs[call_name].directive.lower()
    if directive == "&насервере" or directive == "&насерверебезконтекста" \
            or directive == "&наклиентенасервере" or directive == "&наклиентенасерверебезконтекста":
        force_move_to_form = True
    funcs_to_move.add(call_name)
    for sub_call in gl_func_calls[call_name]:
        fill_secondary_form_calls(form_name, sub_call, force_move_to_form)

###################################################################################################
# Шаг 7. Перенос процедур и функций в основную форму. Перенос осуществляется через добавление
#        в структуру кода основной формы (proc_func_list) процедур и функций отмеченных к переносу,
#        а так же удаление обращений к общим модулям.
#

def copy_functions_to_form(form_struct, proc_funcs_to_copy, export_proc_funcs):
    """
    Выполняет перенос процедур и функций отмеченных для переноса в форму.
    При копировании добавляется директива, а также убирается признак экспортности для локальных процедур и функций.
    @param form_struct (strct1c.Module): описание модуля формы, в которую будет скопирована функция
    @param proc_funcs_to_copy (set): набор функций для копирования в форму
    @param export_proc_funcs (set): набор процедур и функций, которые должны оставаться экспортными
    @return: None
    """
    global gl_all_proc_funcs
    global gl_common_modules_props
    for full_func_name in proc_funcs_to_copy:
        # Копируем описание процедуры/функции, что бы не повредить его,
        # т.к.может использоваться для копирования в другие формы
        func_proc_desc = copy.deepcopy(gl_all_proc_funcs[full_func_name])

        parts = full_func_name.split(".")
        # Директива зависит от контекста исполнения общего модуля:
        #   клиент        - &НаКлиенте
        #   сервер        - &НаСервереБезКонтекста
        #   клиент-сервер - &НаКлиентеНаСервереБезКонтекста
        module_properties = gl_common_modules_props[parts[1]]
        if module_properties['is_client']:
            func_proc_desc.directive = "&НаКлиенте"
        elif module_properties['is_server']:
            func_proc_desc.directive = "&НаСервереБезКонтекста"
        elif module_properties['is_client_server']:
            func_proc_desc.directive = "&НаКлиентеНаСервереБезКонтекста"
        else:
            raise Exception("Не определен контекст вызова функции общего модуля: " + full_func_name)
        if not full_func_name in export_proc_funcs:
            # нет обращения из вспомогательной формы, т.е. есть только в основной форме
            func_proc_desc.is_export = False
        # собственно эта инструкция и выполняет перенос ;)
        form_struct.proc_func_list.append(func_proc_desc)

def handle_form_module_func_proc(form_struct, full_form_name):
    def replace_common_module_calls(call_list):
        """
        Выполняет замену обращений к общим модулям на вызовы локальных процедур/функций.
        Например:
            "Subsys_ОбщегоНазначенияКлиентСервер.Проверить(..)" => "Проверить(..)"
        @param call_list (list): список обращений к процедурам и функциям общих модулей для замены
        @return: None
        """
        for (call, func_name) in call_list:
            parts = func_name.split(".")
            if len(parts) == 2 and parts[0] in gl_common_modules_props:
                if isinstance(call, strct1c.DottedExpression):
                    call.properties_list.pop(0)
                elif isinstance(call, strct1c.PropertyIndexed):
                    raise Exception("Вызов f()[expr] не обработан: " + called_func_name)

    def replace_calls_to_main_form(call_list, full_form_name):
        def get_main_owner_func_call():
            id_param = strct1c.Identifier('ЭтаФорма')
            return strct1c.FuncCall("ПолучитьОсновногоВладельцаФормы", [id_param])
        result = False
        if not gl_replace_calls_to_main_module.get(full_form_name):
            return result
        # todo короткие имена это плохо, т.к. нужно вручную поддерживать уникальность имён
        replace_calls_to_main_module_short_names = {x.split('.')[2] for x in gl_replace_calls_to_main_module[full_form_name]}
        wrapper_for_client_server_funcs__short_names = {x.split('.')[2] for x in gl_wrapper_for_client_server_funcs[full_form_name]}
        for (call, func_name) in call_list:
            if isinstance(call, strct1c.DottedExpression):
                # только если DottedExpression уже сокращено до одного элемента
                if len(call.properties_list) == 1:
                    name = call.properties_list[0].get_name()
                    # если нужно заменить обращение к основной форме
                    if name in replace_calls_to_main_module_short_names:
                        # если нужно при этом заменить обращение на враппер
                        if name in wrapper_for_client_server_funcs__short_names:
                            call.properties_list[0].set_name(name+"_wrapper")
                        call.properties_list.insert(0, get_main_owner_func_call())
                        result = True
            else:
                if call.get_name() in replace_calls_to_main_module_short_names:
                    # todo по хорошему нужно изменить сам объект вызова через владельца
                    if call.get_name() in wrapper_for_client_server_funcs__short_names:
                        call.set_name(call.get_name()+"_wrapper")
                    call.name = "ПолучитьОсновногоВладельцаФормы(ЭтаФорма)." + call.name
                    result = True
        return result


    for func_proc_desc in form_struct.proc_func_list:
        # Важно! Снова получаем список вызовов процедур и функций на основе нового описания функции.
        # Это нужно для того что бы заменить обращения к общим модулям на локальные вызовы
        # и при этом не трогать старое описание.
        sub_call_list = get_statements_call_list(func_proc_desc.body.statements)

        for (call, called_func_name) in sub_call_list:
            # Шаг 7б.  Если среди обращений к функциям есть специальные -
            # ПолучитьОписаниеОповещенияСВызовомФункции, СоздатьОбъектОписанияОповещения
            # то подменяем параметры на сборочные.
            parts = called_func_name.split(".")
            called_func_name_short = parts[0] if len(parts) == 1 else parts[1]
            if called_func_name_short.lower() in gl_spec_replace_params:
                if isinstance(call, strct1c.FuncCall):
                    call.param_list[1] = strct1c.Identifier('ЭтаФорма')
                else:
                    call.properties_list[1].param_list[1] = strct1c.Identifier('ЭтаФорма')

        # заменяем обращения к общим модулям на обращение к локальным функциям
        replace_common_module_calls(sub_call_list)

        # некоторые функции должны вызываться из основной формы
        replace_calls_to_main_form(sub_call_list, full_form_name)

# Список процедур и функций основной управляемой формы
main_form_struct = gl_form_props['Основная']['struct']

if CACHE_MODE_ON and os.path.isfile('main_form_struct_after_copy_funcs.pickle'):
    with open('main_form_struct_after_copy_funcs.pickle', 'rb') as f:
        gl_form_props['Основная']['struct'] = pickle.load(f)
        main_form_struct = gl_form_props['Основная']['struct']
else:
    copy_functions_to_form(main_form_struct, gl_all_proc_funcs_to_move_primary, gl_main_module_export_functions)
    handle_form_module_func_proc(main_form_struct, 'FormManaged.Основная')
    if CACHE_MODE_ON:
        with open('main_form_struct_after_copy_funcs.pickle', 'wb') as f:
            pickle.dump(main_form_struct, f)

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
for func_proc_desc in main_form_struct.proc_func_list:
    if func_proc_desc.name in make_wrapper_set:
        func_proc_desc.is_export = False
        wrapper = copy.deepcopy(wrapper_func if func_proc_desc.is_function else wrapper_proc)
        wrapper.name = func_proc_desc.name + "_wrapper"
        wrapper.vars_list = copy.deepcopy(func_proc_desc.vars_list)
        st = wrapper.body.statements[0]
        fc = st.second_param if func_proc_desc.is_function else st.func_call_path
        fc.name = func_proc_desc.name
        for var_decl in wrapper.vars_list:
            fc.param_list.append(strct1c.Identifier(var_decl.var_name))
        main_form_struct.proc_func_list.append(wrapper)

#########################################################################################################
# Шаг 7в. Замена ссылок на некоторые глобальные переменные на обращения особого вида
#         Например, гл_Subsys_ИмяФайлаОбработки => Объект.КэшДанных.ИмяОбработки
#

# todo соотвествие для замен брать из файла настроек
replacements = {"гл_iBank2_ИмяФайлаОбработки": "Объект.КэшДанных.ИмяОбработки",
                "гл_iBank2_РежимРаботы": "Объект.КэшДанных.РежимРаботы"}

replacements = { key.lower(): val for key, val in replacements.items()}
filter={x for x in replacements}

id_call_list = []
for func_proc_desc in main_form_struct.proc_func_list:
    id_call_list += get_statements_call_list(func_proc_desc.body.statements, obj_type="id", filter=filter)

for rec in id_call_list:
    id_name = rec[1]
    if id_name.lower() in replacements and isinstance(rec[0], strct1c.Identifier):
        rec[0].id = replacements[id_name.lower()]

########################################################################################################
# Шаг 7г. Перенос в модуль основной формы глобальных переменных.

for gl_var_desc in gl_app_module["managed_app_struct"].global_vars:
    if PROCESSOR_NAME.lower() in gl_var_desc.vars_list[0].name.lower():
        gl_var_desc_new = copy.deepcopy(gl_var_desc)
        gl_var_desc_new.directive = "&НаКлиенте"
        gl_form_props['Основная']['struct'].global_vars.append(gl_var_desc_new)

gl_form_props['Основная']['text'] = strct1c.get_text(gl_form_props['Основная']['struct'])

##############################################################################################
# Шаг. 8. Перенос во вспомогательные формы

if CACHE_MODE_ON and os.path.isfile('gl_form_props_after_make_module_text.pickle'):
    with open('gl_form_props_after_make_module_text.pickle', 'rb') as f:
        gl_form_props = pickle.load(f)
else:
    for full_form_name, funcs_set in gl_all_proc_funcs_to_move_secondary.items():
        form_name = full_form_name.split(".")[1]
        form_props = gl_form_props[form_name]
        if not form_props['is_managed']:
            continue
        form_struct = form_props['struct']
        # todo вместо третьего параметра set() нужно передать набор функций которые должны
        # оставаться экспортными - см. особые случаи типа СоздатьОбъектОписанияОповещения
        if 'FormManaged.ВыборДоговора' == full_form_name:
            a = 1

        var_desc = strct1c.VarDesc("__ОсновнаяФорма", False)
        var_declaration = strct1c.VariablesDeclaration([var_desc], '&НаКлиенте')
        form_struct.global_vars.append(var_declaration)

        copy_functions_to_form(form_struct, funcs_set, set())
        handle_form_module_func_proc(form_struct, full_form_name)

        new_form_text = strct1c.get_text(form_struct)

        for gl_var_desc in gl_app_module["managed_app_struct"].global_vars:
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

#loc_dict = locsettings.get_localization_settings('ru')
#for form_name, form_props in gl_form_props.items():
#    # todo пока только управляемые формы
#    if not form_props['is_managed']:
#        continue
#    module_text = form_props['text']
#    for loc_key, loc_val in loc_dict.items():
#        module_text = module_text.replace("{"+loc_key+"}", loc_val)
#    form_props['text'] = module_text

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
# gl_all_proc_funcs_to_move_secondary
# gl_replace_calls_to_main_module

# Во вспомогательных управляемых формах
# а) добавить переменную модуля формы ОсновнаяФорма
# б) в обработчик ПриОткрытии (должен быть добавлен во все формы) добавить вызов ОсновнаяФорма = ПолучитьОсновнуюФорму() (вместо ПолучитьОсновногоВладельцаФормы)
# в) во обращениях к основной форме вместо ПолучитьОсновногоВладельцаФормы() использовать ОсновнаяФорма


