import strct1c
import copy

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


def get_statements_call_list(statements, obj_type = "function", filter = set()):
    """
    Обходит список инструкций (statements) и получает список вызываемых функций.
    Составляется общий список всех обращений к функциям во всех инструкциях.

    @param statements (struct.<инструкция верхнего уровня>): инструкции из процедуры/функции для обхода
    @return (list): список обращений к функциям, где каждый элемент - кортеж.
                    Каждый кортеж состоит из двух элементов: ссылка на структуру вызова, строка вызова.
                    Например: (<strct1c.DottedExpression object at 0x05BB74F0>,
                              'iBank2_СопоставлениеКлиентСервер.ПолучитьЦветТекстаРучнойКорректировки')

    """
    result = []
    for st in statements:
        func_list = st.get_tokens_list(obj_type, filter)
        result += func_list
    return result

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
    func_list = get_statements_call_list(statements)
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


def fill_main_module_calls(main_module_new_funcs, func_subcalls, full_func_name):
    """
    Рекурсивно обходит всё дерево вызовов из переданной full_func_name и добавляет
    каждый вызов в main_module_new_funcs.
    На самом верхнем уровне функция вызывается для каждой процедуры/функции модуля формы.
    Далее вызов продолжается для каждого дочернего вызова и т.д. до последнего вызова.
    @param full_func_name (str): имя процедуры/функции в формате CommonModule.<ИмяМодуля>.<ИмяПроцедурыФункции>
    @return: None
    """
    # получить вызовы из full_func_name
    sub_calls = func_subcalls.get(full_func_name)

    for func_name in sub_calls:
        if func_name in main_module_new_funcs:
            # если подвызов уже добавлен в функции для переноса - пропускаем, что бы избежать зацикливания
            pass
        else:
            if func_name.split('.')[0] != "FormManaged":
                # не нужно добавлять в список процедуры и функций, которые уже есть в модуле
                main_module_new_funcs.add(func_name)
            fill_main_module_calls(main_module_new_funcs, func_subcalls, func_name)


# todo список особых процедур и функций необходимо параметризовать в файле конфигурации
gl_spec_calls = {"ПолучитьОписаниеОповещенияСВызовомФункции", "СоздатьОбъектОписанияОповещения"}
gl_spec_calls = {name.lower() for name in gl_spec_calls}

def find_spec_calls(func_subcalls, funcs_to_copy):

    def fill_implicit_called_funcs(funcs_to_check):
        nonlocal implicit_called_funcs
        nonlocal func_subcalls
        for full_func_name in funcs_to_check:
            for called_func_name, calls_list in func_subcalls[full_func_name].items():
                called_func_name_short = called_func_name.split(".")[2]
                if called_func_name_short.lower() in gl_spec_calls:
                    # Если вызывамая функция - это одна из тех что указаны в gl_spec_calls,
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
    fill_implicit_called_funcs(funcs_to_copy)
    return implicit_called_funcs


def update_secondary_form_calls(form_name, full_func_name, force_move_to_form,
                                            gl_common_modules_props,
                                            gl_func_subcalls,
                                            gl_funcs_to_move_primary,
                                            gl_all_funcs_desc_to_move_secondary,
                                            gl_replace_calls_to_main_module,
                                            gl_wrapper_for_client_server_funcs):
    """
    Вычисляет процедуры и функции для переноса во вспомогательную форму.
    При этом, заполняет gl_all_funcs_desc_to_move_secondary - список функций для переноса.
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

    if full_func_name in gl_all_funcs_desc_to_move_secondary[form_name]:
        # если функция уже отмечена к переносу во вспомогательную форму - не продолжаем, что бы не зациклиться
        return

    if force_move_to_form:
        # для серверной цепочки безусловно переносим процедуру/функцию во вспомогательную форму
        # это важно для клиент-серверных вызовов
        gl_all_funcs_desc_to_move_secondary[form_name].add(full_func_name)
        # безусловно помечаем все последующие вызовы
        new_force_move_to_form = force_move_to_form
    else:
        # Цепочка вызовов - клиентская, поэтому определяем по контексту и наличию в основной форме, переносить ли её.
        parts = full_func_name.split(".")
        module_props = gl_common_modules_props[parts[1]]

        if (module_props['is_client'] or module_props['is_client_server']) \
                and full_func_name in gl_funcs_to_move_primary \
                and len(gl_func_subcalls[full_func_name]) > 0:
            # если функция клиентская/клиент-серверная и при этом переносится в основную форму,
            # значит следует переадресовать вызов к основной форме
            gl_replace_calls_to_main_module[form_name].add(full_func_name)

            if module_props['is_client_server']:
                # при этом, если функция клиент-серверная, то для нее необходимо делать клиентский враппер
                gl_wrapper_for_client_server_funcs[form_name].add(full_func_name)
            # не имеет смысла просматривать дальше вызовы из функции, т.к. они уже есть в основной форме
            return
        else:
            gl_all_funcs_desc_to_move_secondary[form_name].add(full_func_name)
            new_force_move_to_form = module_props['is_server'] or module_props['is_client_server']
    sub_call_list = gl_func_subcalls.get(full_func_name)
    for sub_called_func_name in sub_call_list:
        # sub_call это обращение к функции, например:
        #   CommonModule.System_ЗарплатныйПроект.ВыборПлатежногоПоручения_ПриСозданииНаСервере
        update_secondary_form_calls(form_name, sub_called_func_name, new_force_move_to_form,
                                        gl_common_modules_props,
                                        gl_func_subcalls,
                                        gl_funcs_to_move_primary,
                                        gl_all_funcs_desc_to_move_secondary,
                                        gl_replace_calls_to_main_module,
                                        gl_wrapper_for_client_server_funcs)


def copy_functions_to_form(form_struct, gl_funcs_to_move_primary,
                           gl_main_module_export_functions,
                           gl_all_funcs_desc,
                           gl_common_modules_props):
    """
    Выполняет перенос процедур и функций отмеченных для переноса в форму.
    При копировании добавляется директива, а также убирается признак экспортности для локальных процедур и функций.
    @param form_struct (strct1c.Module): описание модуля формы, в которую будет скопирована функция
    @param gl_funcs_to_move_primary (set): набор функций для копирования в форму
    @param gl_main_module_export_functions (set): набор процедур и функций, которые должны оставаться экспортными
    @param gl_all_funcs_desc (set): описание всех процедур и функций
    @param gl_common_modules_props (set): описание всех модулей
    @return: None
    """
    for full_func_name in gl_funcs_to_move_primary:

        if full_func_name.find('ЗарплатныйПроект_УстановитьДоступностьЭлементов')>=0:
            a = 1
        # Копируем описание процедуры/функции, что бы не повредить его,
        # т.к.может использоваться для копирования в другие формы
        func_proc_desc = copy.deepcopy(gl_all_funcs_desc[full_func_name])

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
        if full_func_name in gl_main_module_export_functions:
            # нет обращения из вспомогательной формы, т.е. есть только в основной форме
            func_proc_desc.is_export = True
        else:
            func_proc_desc.is_export = False
        # собственно эта инструкция и выполняет перенос ;)
        form_struct.proc_funcs_list.append(func_proc_desc)


def handle_form_module_func_proc(form_struct, full_form_name, gl_common_modules_props,
                                 gl_replace_calls_to_main_module = None,
                                 gl_wrapper_for_client_server_funcs = None):
    def replace_common_module_calls(call_list):
        """
        Выполняет замену обращений к общим модулям на вызовы локальных процедур/функций.
        Например:
            "Subsys_ОбщегоНазначенияКлиентСервер.Проверить(..)" => "Проверить(..)"
        @param call_list (list): список обращений к процедурам и функциям общих модулей для замены
        @return: None
        """
        nonlocal gl_common_modules_props
        for (call, func_name) in call_list:
            parts = func_name.split(".")
            if len(parts) == 2 and parts[0] in gl_common_modules_props:
                if isinstance(call, strct1c.DottedExpression):
                    call.properties_list.pop(0)
                else:
                    raise Exception("Вызов f() не обработан: " + called_func_name)

    def replace_calls_to_main_form(call_list, full_form_name):
        def get_main_owner_func_call():
            id_param = strct1c.Identifier('ЭтаФорма')
            return strct1c.FuncCall("ПолучитьОсновногоВладельцаФормы", [id_param])
        result = False
        if not full_form_name in gl_replace_calls_to_main_module:
            return result
        # todo короткие имена это плохо, т.к. нужно вручную поддерживать уникальность имён
        replace_calls_to_main_module_short_names = {x.split('.')[2] for x in gl_replace_calls_to_main_module[full_form_name]}
        wrapper_for_client_server_funcs__short_names = {x.split('.')[2] for x in gl_wrapper_for_client_server_funcs[full_form_name]}
        for (call, func_name) in call_list:
            if isinstance(call, strct1c.DottedExpression):
                # только если DottedExpression уже сокращено до одного элемента
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

    for func_proc_desc in form_struct.proc_funcs_list:
        # Важно! Снова получаем список вызовов процедур и функций на основе нового описания функции.
        # Это нужно для того что бы заменить обращения к общим модулям на локальные вызовы
        # и при этом не трогать старое описание.
        sub_call_list = get_statements_call_list(func_proc_desc.body.statements)

        for (call, called_func_name) in sub_call_list:
            # Если среди обращений к функциям есть специальные -
            # ПолучитьОписаниеОповещенияСВызовомФункции, СоздатьОбъектОписанияОповещения
            # то подменяем параметры на сборочные.
            parts = called_func_name.split(".")
            called_func_name_short = parts[0] if len(parts) == 1 else parts[1]
            if called_func_name_short.lower() in gl_spec_calls:
                if isinstance(call, strct1c.DottedExpression):
                    call.properties_list[1].param_list[1] = strct1c.Identifier('ЭтотОбъект')
                else:
                    raise Exception("Необработанный вызов : " + call)

        # заменяем обращения к общим модулям на обращение к локальным функциям
        replace_common_module_calls(sub_call_list)

        if gl_replace_calls_to_main_module:
            # некоторые функции должны вызываться из основной формы
            replace_calls_to_main_form(sub_call_list, full_form_name)
