import strct1c

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

def get_proc_func_call_list(all_proc_funcs, proc_func, module_type, module_name):
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
    func_list = get_statements_call_list(proc_func.body.statements)
    for func_rec in func_list:
        func_name = func_rec[1]
        if func_name.find('.') >= 0:
            # вызов разделенный точкой - обращение к функции другого общего модуля
            full_name = "commonmodule" + "." + func_name
        else:
            # обращение к функции этого модуля
            full_name = module_type + "." + module_name + "." + func_name
        full_name = full_name.lower()
        # отбираем только функции модулей (без встроенных функций)
        if all_proc_funcs.get(full_name):
            # в функции может быть несколько обращений к одной и тойже (другой) функции
            val = result.get(full_name, [])
            val.append(func_rec[0])
            result[full_name] = val
    return result


def fill_main_module_calls(main_module_new_funcs, func_calls, full_func_name):
    """
    Рекурсивно обходит всё дерево вызовов из переданной full_func_name и добавляет
    каждый вызов в main_module_new_funcs.
    На самом верхнем уровне функция вызывается для каждой процедуры/функции модуля формы.
    Далее вызов продолжается для каждого дочернего вызова и т.д. до последнего вызова.
    @param full_func_name (str): имя процедуры/функции в формате CommonModule.<ИмяМодуля>.<ИмяПроцедурыФункции>
    @return: None
    """
    # получить вызовы из full_func_name
    sub_calls = func_calls.get(full_func_name)

    for func_name in sub_calls:
        if func_name in main_module_new_funcs:
            # если подвызов уже добавлен в функции для переноса - пропускаем, что бы избежать зацикливания
            pass
        else:
            if func_name.split('.')[0] != "formmanaged":
                # не нужно добавлять в список процедуры и функций, которые уже есть в модуле
                main_module_new_funcs.add(func_name)
            fill_main_module_calls(main_module_new_funcs, func_calls, func_name)

def add_special_proc_funcs(gl_func_to_add_spec, gl_func_calls, gl_spec_replace_params, proc_func_to_move_list):
    for full_func_name in proc_func_to_move_list:
        sub_call_list = gl_func_calls[full_func_name]
        for called_func_name, calls in sub_call_list.items():
            called_func_name_short = called_func_name.split(".")[2]
            if called_func_name_short in gl_spec_replace_params:
                # Если вызывамая функция - это одна из тех что указаны в gl_spec_replace_params,
                # требуется перенести ещё функцию указанную в параметре.
                for call in calls:
                    if isinstance(call, strct1c.FuncCall):
                        func_name = call.param_list[0].value[0]
                        module_name = call.param_list[1].value[0]
                    elif isinstance(call, strct1c.DottedExpression):
                        func_name = call.properties_list[1].param_list[0].value[0]
                        module_name = call.properties_list[1].param_list[1].value[0]
                    else:
                        raise Exception("Необработанный вызов : " + call)
                    sub_call_full_name = ("CommonModule." + module_name + "." + func_name).lower()
                    if not sub_call_full_name in gl_func_to_add_spec:
                        # так же
                        gl_func_to_add_spec.add(sub_call_full_name)
                        add_special_proc_funcs(gl_func_to_add_spec, gl_func_calls, gl_spec_replace_params, [sub_call_full_name])

