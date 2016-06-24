# -*- coding: utf-8 -*-

from base_const import *
import copy
import collections
import custom_handlers
import strct1c
import utils

def get_move_functions_configuration_ordinary_app(context):

    dataproc_module_config = PrimaryFormConf(set(), set())

    for full_func_name in context.gl_func_subcalls[APP_TYPE_ORDINARY]:
        if full_func_name.split('.')[0] == FORM_ORDINARY:
            fill_direct_call_chain(dataproc_module_config.functions_to_move,
                                   context.gl_func_subcalls[APP_TYPE_ORDINARY],
                                   full_func_name)
            sub_calls = context.gl_func_subcalls[APP_TYPE_ORDINARY].get(full_func_name)
            for sub_called_func_name in sub_calls:
                if sub_called_func_name[0:4] != 'Form':
                    # функции, вызываемые непосредственно из обычных форм должны быть экспортными
                    dataproc_module_config.export_functions.add(sub_called_func_name)

    custom_handlers.update_functions_to_move(APP_TYPE_ORDINARY, dataproc_module_config, context)

    return dataproc_module_config

def transfer_functions_to_dataprocessor_module(context, dataproc_module_config):

    # Описание основной управляемой формы
    dataprocessor_module_struct = context.gl_ep_module['struct']

    copy_functions_to_form(APP_TYPE_ORDINARY,
                           dataprocessor_module_struct,
                           dataproc_module_config.functions_to_move,
                           dataproc_module_config.export_functions,
                           context.gl_all_funcs_desc[APP_TYPE_ORDINARY],
                           context.gl_common_modules_props)

    handle_form_module_func_proc(dataprocessor_module_struct, DATA_PROCESSOR + '.' + 'iBank2', context.gl_common_modules_props)

    # Перенос в модуль основной формы глобальных переменных.
    for gl_var_desc in context.gl_app_module[APP_TYPE_ORDINARY]['struct'].global_vars_list:
        if 'iBank2'.lower() in gl_var_desc.vars_list[0].name.lower():
            gl_var_desc_new = copy.deepcopy(gl_var_desc)
            gl_var_desc_new.directive = None
            gl_var_desc_new.vars_list[0].export = False;
            dataprocessor_module_struct.global_vars_list.append(gl_var_desc_new)

    custom_handlers.update_primary_module_after_transfer(APP_TYPE_ORDINARY, dataprocessor_module_struct)

    for form_name, form_props in context.gl_form_props.items():
        if form_props['is_managed']:
            continue
        for func_proc_desc in form_props['struct'].proc_funcs_list:
            sub_call_list = utils.get_statements_call_list(func_proc_desc.body.statements)
            # заменяем обращения к общим модулям на обращение к локальным функциям
            replace_common_module_calls(sub_call_list, context.gl_common_modules_props)

    pass


def get_move_functions_configuration(context, func_name_get_main_module):

    primary_form_config = get_functions_to_move(context)
    # Дополнить список функций переносимых в основную форму
    custom_handlers.update_functions_to_move(APP_TYPE_MANAGED, primary_form_config, context)

    secondary_forms_config = get_secondary_module_config(primary_form_config, context)
    # Дополнить список функций переносимых во вспомогательные формы
    custom_handlers.update_funcs_to_move_secondary(secondary_forms_config, primary_form_config, context)

    # Функции основной формы к которым есть обращение из вспомогательных форм должны быть экспортными
    for form_name, funcs_set in secondary_forms_config.replace_calls_to_primary_module.items():
        for full_func_name in funcs_set:
            primary_form_config.export_functions.add(full_func_name)

    if func_name_get_main_module:
        # Для доступа к основной форме используется специальная функция,
        # полное имя которой передаётся в func_name_get_main_module
        update_func_to_get_main_form(secondary_forms_config, context, func_name_get_main_module)

    return MoveConfiguration(primary_form_config, secondary_forms_config)


def get_functions_to_move(context):
    """
    Формирование списка процедур и функций общих модулей для переноса в основную форму.
    Этот список состоит из таких пр./ф которые непосредственно учавствуют в цепочке вызова,
    а так же учавствуют в цепочке вызова косвенно, например через вызов Выполнить(..).
    @param context: контекст загруженных модулей
    @return (set): набор функций для переноса в основную форму
    """

    primary_form_config = PrimaryFormConf(set(), set())

    for full_func_name in context.gl_func_subcalls[APP_TYPE_MANAGED]:
        parts = full_func_name.split('.')
        if parts[0] == FORM_MANAGED and parts[1].lower() == 'основная':
            fill_direct_call_chain(primary_form_config.functions_to_move,
                                                context.gl_func_subcalls[APP_TYPE_MANAGED],
                                                full_func_name)
    return primary_form_config

def fill_direct_call_chain(module_funcs_set, func_subcalls, full_func_name):
    """
    Рекурсивно обходит всё дерево вызовов из переданной full_func_name и добавляет каждый вызов в module_funcs_set.
    На самом верхнем уровне функция вызывается для каждой процедуры/функции модуля формы.
    Далее вызов продолжается для каждого дочернего вызова и т.д. до последнего вызова.
    @param full_func_name (str): имя процедуры/функции в формате CommonModule.<ИмяМодуля>.<ИмяПроцедурыФункции>
    @return: None
    """
    # получить вызовы из full_func_name
    sub_calls = func_subcalls.get(full_func_name)

    for func_name in sub_calls:
        if func_name in module_funcs_set:
            # если подвызов уже добавлен в функции для переноса - пропускаем, что бы избежать зацикливания
            pass
        else:
            if func_name[0:4] != "Form":
                # не нужно добавлять в список процедуры и функций, которые уже есть в модуле
                module_funcs_set.add(func_name)
            fill_direct_call_chain(module_funcs_set, func_subcalls, func_name)
    pass

def get_secondary_module_config(primary_form_config, context):

    # functions_to_move_dict:
    # Список процедур и функция для переноса во вспомогательные формы.
    #   ключ - имя формы
    #   значение - список функций для переноса
    #
    # replace_calls_to_primary_module:
    # Содержит список обращений к функциям, вызовы к которым необходимо заменить на обращение к основной форме:
    # Например, вызов
    #   System_ОбщегоНазначениеКлиентСервер.СообщитьПользователю(..)
    # Будет заменен в итоговой форме на:
    #   ОсновнаяФорма.СообщитьПользователю(..)
    # Структура переменной:
    #   ключ - имя формы
    #   значение - имя функции которую следует заменить
    #
    # wrapper_calls:
    # экспортные клиент-сервеные процедуры и функции не могут вызываться из основной формы, поэтому
    # необходимо делать экспортные врапперы таких процедур и функций, которые выполняются в клиентском контексте
    #
    # export_functions:
    # Список функций, которые должны оставаться экспортными

    secondary_forms_config = SecondaryFuncs(dict(), dict(), dict(), dict())

    # Основная функция заполняющая список функций для переноса во вспомогательные формы
    fill_secondary_forms_config(secondary_forms_config, primary_form_config, context)

    return secondary_forms_config


def fill_secondary_forms_config(secondary_forms_config, primary_form_config, context):
    """
    Формирование списка процедур и функций для переноса во вспомогательные формы.
    Порядок перенося процедур и функций следующий:
     - безусловно переносятся все чисто серверные процедуры и функции
     - клиентские процедуры и функции переносятся если не вызываются в основной форме,
       если вызываются - вызов будет заменен на обращение к основной форме
     - клиент-серверные процедуры и функции переносятся если есть только во вспомогательной форме
       либо есть хотя бы один вызов из серверного контекста, если вызов такой процедуры или функции
       присутствует в основной форме и при этом не вызывается из серверного контекста,
       то вызов заменяется на обращение к основной форме.
    """

    for full_func_name, sub_calls in context.gl_func_subcalls[APP_TYPE_MANAGED].items():
        # full_func_name = 'FormManaged.СписокДоверенныхПолучателей.ДоверенныеПолучатели_ЭкземплярСистемыПриИзменении'
        # sub_calls = gl_func_subcalls[APP_TYPE_MANAGED].get(full_func_name)
        parts = full_func_name.split(".")
        if parts[0] != FORM_MANAGED or parts[1].lower() == "основная":
            # отбираем только вспомогательные формы
            continue

        if parts[0] == FORM_MANAGED and parts[1].lower() == "историядокумента":
            a = 1

        force_move_to_form = False
        directive = context.gl_all_funcs_desc[APP_TYPE_MANAGED][full_func_name].directive.lower()
        if directive == "&насервере" or directive == "&насерверебезконтекста":
            # это "чистый" серверный вызов - все клиент-серверные процедуры
            # и функции необходимо переносить в форму
            force_move_to_form = True

        # имя формы, например "FormManaged.Письма"
        form_name = parts[0] + "." + parts[1]

        # инициализция списка для формы в functions_to_move_dict
        if None==secondary_forms_config.functions_to_move_dict.get(form_name, None):
            secondary_forms_config.functions_to_move_dict[form_name] = set()
            secondary_forms_config.replace_calls_to_primary_module[form_name] = set()
            secondary_forms_config.wrapper_calls[form_name] = set()

        for called_func_name in sub_calls:
            update_secondary_form_calls(form_name, called_func_name, force_move_to_form,
                                        context, secondary_forms_config,
                                        primary_form_config.functions_to_move)

        # Одна и та же клиент-серверная процедура/функция может быть добавлена и в
        # functions_to_move_dict и в replace_calls_to_primary_module
        # Это может происходить в ситуациях, когда она:
        #   А) есть в основной форме
        #   Б) есть в клиенской цепочке вызова вспомогательной формы
        #   В) есть в серверной цепочке вызова вспомогательной формы
        # Такие процедуры/функции необходимо удалить из replace_calls_to_primary_module.
        for func_proc_name in secondary_forms_config.functions_to_move_dict[form_name]:
            if func_proc_name in secondary_forms_config.replace_calls_to_primary_module[form_name]:
                secondary_forms_config.replace_calls_to_primary_module[form_name].remove(func_proc_name)
    pass

def update_secondary_form_calls(form_name,
                                full_func_name,
                                force_move_to_form,
                                context,
                                secondary_forms_config,
                                primary_module_funcs):
    """
    Вычисляет процедуры и функции для переноса во вспомогательную форму.
    При этом, заполняет functions_to_move_dict - список функций для переноса.
    А так же заполняет replace_calls_to_primary_module - список функций для обращения через основной модуль.
    и wrapper_calls - список процедур и функций доступ к которым из воспомогательных форм
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

    if full_func_name in secondary_forms_config.functions_to_move_dict[form_name]:
        # если функция уже отмечена к переносу во вспомогательную форму - не продолжаем, что бы не зациклиться
        return

    if force_move_to_form:
        # для серверной цепочки безусловно переносим процедуру/функцию во вспомогательную форму
        # это важно для клиент-серверных вызовов
        secondary_forms_config.functions_to_move_dict[form_name].add(full_func_name)
        # безусловно помечаем все последующие вызовы
        new_force_move_to_form = force_move_to_form
    else:
        # Цепочка вызовов - клиентская, поэтому определяем по контексту и наличию в основной форме, переносить ли её.
        parts = full_func_name.split(".")
        module_props = context.gl_common_modules_props[parts[1]]

        if (module_props['is_client'] or module_props['is_client_server']) \
                and full_func_name in primary_module_funcs \
                and len(context.gl_func_subcalls[APP_TYPE_MANAGED][full_func_name]) > 0:
            # если функция клиентская/клиент-серверная и при этом переносится в основную форму,
            # значит следует переадресовать вызов к основной форме
            secondary_forms_config.replace_calls_to_primary_module[form_name].add(full_func_name)

            if module_props['is_client_server']:
                # при этом, если функция клиент-серверная, то для нее необходимо делать клиентский враппер
                secondary_forms_config.wrapper_calls[form_name].add(full_func_name)
            # не имеет смысла просматривать дальше вызовы из функции, т.к. они уже есть в основной форме
            return
        else:
            secondary_forms_config.functions_to_move_dict[form_name].add(full_func_name)
            new_force_move_to_form = module_props['is_server'] or module_props['is_client_server']
    sub_call_list = context.gl_func_subcalls[APP_TYPE_MANAGED].get(full_func_name)
    for sub_called_func_name in sub_call_list:
        # sub_call это обращение к функции, например:
        #   CommonModule.System_ЗарплатныйПроект.ВыборПлатежногоПоручения_ПриСозданииНаСервере
        update_secondary_form_calls(form_name, sub_called_func_name, new_force_move_to_form,
                                    context, secondary_forms_config, primary_module_funcs)

    pass

def update_func_to_get_main_form(secondary_forms_config, context, func_name_get_main_module):
    """
    Если в конфигурации есть функция для определения основной формы - необходимо перенести её во вспомогательную форму.
    @param move_config:
    @param context:
    @param func_name_get_main_module:
    @return:
    """
    st = strct1c.JumpStatemets('Возврат', strct1c.Identifier("__ОсновнаяФорма"))
    st_ifelse_cond = strct1c.BinaryExpr(strct1c.Identifier('__ОсновнаяФорма'), strct1c.Undefined(), "<>")
    st_ifelse = strct1c.IfElseStatement(st_ifelse_cond, [st], [])
    st_asgn = strct1c.StatementAssignment(strct1c.Identifier('__ОсновнаяФорма'), strct1c.Identifier('ОсновнаяФорма'))

    statements = context.gl_all_funcs_desc[APP_TYPE_MANAGED][func_name_get_main_module].body.statements
    statements.insert(0, st_ifelse)
    statements.insert(len(statements) - 1, st_asgn)

    for form_name, funcs_to_move in secondary_forms_config.functions_to_move_dict.items():
        funcs_to_move.add(func_name_get_main_module)
    pass

def make_wrappers(move_config, main_form_struct):
    """
    Создает врапперы для клиент-серверных функций
    @param move_config:
    @param main_form_struct:
    @return:
    """
    make_wrapper_set = set()
    for form_name, funcs_set in move_config.secondary_forms_config.wrapper_calls.items():
        for full_func_name in funcs_set:
            if full_func_name in move_config.secondary_forms_config.replace_calls_to_primary_module[form_name]:
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
    pass


def transfer_functions_to_main_form(context, move_config, key_word):
    """
    Перенос процедур и функций в основную форму. Перенос осуществляется через добавление
    в структуру кода основной формы (proc_funcs_list) процедур и функций отмеченных к переносу,
    а так же удаление обращений к общим модулям.
    @param context:
    @param move_config:
    @param key_word:
    @return:
    """

    # Описание основной управляемой формы
    main_form_struct = context.gl_form_props["Основная"]['struct']

    copy_functions_to_form(APP_TYPE_MANAGED,
                           main_form_struct,
                           move_config.primary_form_config.functions_to_move,
                           move_config.primary_form_config.export_functions,
                           context.gl_all_funcs_desc[APP_TYPE_MANAGED],
                           context.gl_common_modules_props)

    handle_form_module_func_proc(main_form_struct, FORM_MANAGED + '.' + 'Основная', context.gl_common_modules_props)

    # Перенос в модуль основной формы глобальных переменных.
    for gl_var_desc in context.gl_app_module[APP_TYPE_MANAGED]['struct'].global_vars_list:
        if key_word.lower() in gl_var_desc.vars_list[0].name.lower():
            gl_var_desc_new = copy.deepcopy(gl_var_desc)
            gl_var_desc_new.directive = "&НаКлиенте"
            main_form_struct.global_vars_list.append(gl_var_desc_new)

    # Создать в основной форме врапперы для клиент-серверных функций, к которым есть обращения из вспомогательных форм
    make_wrappers(move_config, main_form_struct)

    custom_handlers.update_primary_module_after_transfer(APP_TYPE_MANAGED, main_form_struct)
    pass

def transfer_functions_to_secondary_form(context, move_config, key_word, func_name_get_main_module):
    """
    Перенос во вспомогательные формы.
    @param context:
    @param move_config:
    @return:
    """
    # список глобальных переменных, которые переносятся в основной модуль
    vars_list = set()
    for gl_var_desc in context.gl_app_module[APP_TYPE_ORDINARY]['struct'].global_vars_list:
        if key_word.lower() in gl_var_desc.vars_list[0].name.lower():
            vars_list.add(gl_var_desc.vars_list[0].name.lower())

    # Готовим конструкцию для замены обращения к глобальной переменной.
    # Например, в модуле управляемого приложения была перменная гл_Subsys_НастройкиПрограммы,
    # она перенеслась в модуль основной формы, а для обращения из вспомогательных форм производится
    # обращение: ПолучитьОсновнуюФорму(ЭтотОбъект).гл_Subsys_НастройкиПрограммы
    func_name_get_main_form_short = func_name_get_main_module.split('.')[2]
    func_call_get_main_form = strct1c.FuncCall(func_name_get_main_form_short, [strct1c.Identifier('ЭтотОбъект')])
    global_vars_replace_call = strct1c.DottedExpression(func_call_get_main_form)
    global_vars_replace_call.append(None)

    for full_form_name, funcs_to_move in move_config.secondary_forms_config.functions_to_move_dict.items():
        form_name = full_form_name.split(".")[1]
        form_props = context.gl_form_props[form_name]
        if not form_props['is_managed']:
            continue
        form_struct = form_props['struct']

        var_desc = strct1c.VarDesc("__ОсновнаяФорма", False)
        var_declaration = strct1c.VariablesDeclaration([var_desc], '&НаКлиенте')
        form_struct.global_vars_list.append(var_declaration)

        copy_functions_to_form(APP_TYPE_MANAGED,
                               form_struct,
                               funcs_to_move,
                               move_config.secondary_forms_config.export_functions.get(full_form_name, set()),
                               context.gl_all_funcs_desc[APP_TYPE_MANAGED],
                               context.gl_common_modules_props)

        handle_form_module_func_proc(form_struct,
                                     full_form_name,
                                     context.gl_common_modules_props,
                                     move_config.secondary_forms_config.replace_calls_to_primary_module,
                                     move_config.secondary_forms_config.wrapper_calls,
                                     func_name_get_main_form_short)

        # Для обращения к глобальным переменным из вспомогательных форм необходимо обратиться к основной форме
        id_call_list = []
        for func_proc_desc in form_struct.proc_funcs_list:
            id_call_list += utils.get_statements_call_list(func_proc_desc.body.statements, obj_type="id", filter=vars_list)

        for id_call, alias in id_call_list:
            #сейчас нельзя выполнить замену, т.к. нельзя найти владельца по выражению
            #что бы найти владельца нужно принудительно делать set_owner после deepcopy.
            # в функции set_owner добавить параметр recursive что бы заполнить владельца
            # по всей структуре вызова
            if isinstance(id_call, strct1c.Identifier):
                new_call = copy.deepcopy(global_vars_replace_call)
                new_call.properties_list[1] = id_call
                owner = strct1c.get_owner(id_call)
                owner.replace_obj(id_call, new_call)
                strct1c.set_owner(id_call, new_call)
            elif isinstance(id_call, strct1c.DottedExpression):
                func_copy = copy.deepcopy(func_call_get_main_form)
                id_call.properties_list.insert(0, func_copy)
                strct1c.set_owner(func_copy, id_call)
            else:
                raise Exception("Не обработан вызов: " + alias)
    pass


def copy_functions_to_form(app_type, module_struct, functions_to_move, export_functions, all_funcs_desc, common_modules_props):
    """
    Выполняет перенос процедур и функций отмеченных для переноса в форму.
    При копировании добавляется директива, а также убирается признак экспортности для локальных процедур и функций.
    @param module_struct (strct1c.Module): описание модуля, в который будет скопирована функция
    @param functions_to_move (set): набор функций для копирования в форму
    @param export_functions (set): набор процедур и функций, которые должны оставаться экспортными
    @param all_funcs_desc (set): описание всех процедур и функций
    @param common_modules_props (set): описание всех модулей
    @return: None
    """
    for full_func_name in functions_to_move:

        # Копируем описание процедуры/функции, что бы оставить оригинал для переноса в другие формы,
        # т.к.может использоваться для копирования в другие формы
        func_proc_desc = copy.deepcopy(all_funcs_desc[full_func_name])

        strct1c.set_owner(func_proc_desc.body, func_proc_desc, True)
        strct1c.set_owner(func_proc_desc.vars_list, func_proc_desc, True)

        # Директива компиляции устанавливается только при переносе в модуль управляемой формы
        if app_type == APP_TYPE_MANAGED:
            parts = full_func_name.split(".")
            # Директива зависит от контекста исполнения общего модуля:
            #   клиент        - &НаКлиенте
            #   сервер        - &НаСервереБезКонтекста
            #   клиент-сервер - &НаКлиентеНаСервереБезКонтекста
            module_properties = common_modules_props[parts[1]]
            if module_properties['is_client']:
                func_proc_desc.directive = "&НаКлиенте"
            elif module_properties['is_server']:
                func_proc_desc.directive = "&НаСервереБезКонтекста"
            elif module_properties['is_client_server']:
                func_proc_desc.directive = "&НаКлиентеНаСервереБезКонтекста"
            else:
                raise Exception("Не определен контекст вызова функции общего модуля: " + full_func_name)

        # Установка признака экспортности
        func_proc_desc.is_export = True if full_func_name in export_functions else False

        # собственно эта инструкция и выполняет перенос ;)
        module_struct.proc_funcs_list.append(func_proc_desc)
    pass

def handle_form_module_func_proc(module_struct, full_form_name, gl_common_modules_props,
                                 replace_calls_to_primary_module = None,
                                 wrapper_calls = None,
                                 func_name_get_main_form_short = None):

    def replace_calls_to_main_form(call_list, full_form_name):
        """
        Вызывается только для вспомогательных форм.
        Заменяет обращения к функциям основной формы на обращение через
        @param call_list:
        @param full_form_name:
        @return:
        """
        def get_main_owner_func_call():
            nonlocal func_name_get_main_form_short
            id_param = strct1c.Identifier('ЭтотОбъект')
            return strct1c.FuncCall(func_name_get_main_form_short, [id_param])
        nonlocal func_name_get_main_form_short
        result = False
        if not full_form_name in replace_calls_to_primary_module:
            return result
        # todo короткие имена это плохо, т.к. нужно вручную поддерживать уникальность имён
        replace_calls_to_primary_module_short_names = {x.split('.')[2] for x in replace_calls_to_primary_module[full_form_name]}
        wrapper_calls__short_names = {x.split('.')[2] for x in wrapper_calls[full_form_name]}
        for (call, func_name) in call_list:
            if isinstance(call, strct1c.DottedExpression):
                # только если DottedExpression уже сокращено до одного элемента
                name = call.properties_list[0].get_name()
                # если нужно заменить обращение к основной форме
                if name in replace_calls_to_primary_module_short_names:
                    # если нужно при этом заменить обращение на враппер
                    if name in wrapper_calls__short_names:
                        call.properties_list[0].set_name(name+"_wrapper")
                    call.properties_list.insert(0, get_main_owner_func_call())
                    result = True
            else:
                if call.get_name() in replace_calls_to_primary_module_short_names:
                    # todo по хорошему нужно изменить сам объект вызова через владельца
                    if call.get_name() in wrapper_calls__short_names:
                        call.set_name(call.get_name()+"_wrapper")
                    call.name = func_name_get_main_form_short + "(ЭтотОбъект)." + call.name
                    result = True
        return result

    for func_proc_desc in module_struct.proc_funcs_list:
        # Важно! Снова получаем список вызовов процедур и функций на основе нового описания функции.
        # Это нужно для того что бы заменить обращения к общим модулям на локальные вызовы
        # и при этом не трогать старое описание.
        sub_call_list = utils.get_statements_call_list(func_proc_desc.body.statements)

        # дополнительная обработка
        custom_handlers.handle_form_module_func_proc(func_proc_desc, sub_call_list)

        # заменяем обращения к общим модулям на обращение к локальным функциям
        replace_common_module_calls(sub_call_list, gl_common_modules_props)

        if replace_calls_to_primary_module:
            # некоторые функции должны вызываться из основной формы
            replace_calls_to_main_form(sub_call_list, full_form_name)
    pass


def replace_common_module_calls(call_list, gl_common_modules_props):
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
            else:
                raise Exception("Вызов f() не обработан: " + func_name)
