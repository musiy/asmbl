from base_const import *
import move_funcs
import strct1c
import utils

def update_funcs_to_move_primary(move_config, gl_context):

    # Некоторые функции вызываются неявно через Выполнить(..) - заполним их вручную
    gl_funcs_to_move_primary_spec = find_spec_calls(gl_context, move_config.gl_funcs_to_move_primary)
    for full_func_name in gl_funcs_to_move_primary_spec:
        move_config.gl_main_module_export_functions.add(full_func_name)
        if full_func_name not in move_config.gl_funcs_to_move_primary:
            move_config.gl_funcs_to_move_primary.add(full_func_name)
            move_funcs.fill_main_module_calls(move_config.gl_funcs_to_move_primary,
                                              gl_context.gl_func_subcalls[APP_TYPE_MANAGED],
                                              full_func_name)
    # некоторые функции содержат в названии префикс "гл_" - это признак того, что функцию
    # следует перенести в основную форму
    for full_func_name in gl_context.gl_all_funcs_desc['managed']:
        if full_func_name.split('.')[2].lower().startswith("гл_") and \
                        full_func_name not in move_config.gl_funcs_to_move_primary:
            move_config.gl_funcs_to_move_primary.add(full_func_name)
            move_funcs.fill_main_module_calls(move_config.gl_funcs_to_move_primary,
                                              gl_context.gl_func_subcalls[APP_TYPE_MANAGED],
                                              full_func_name)
    pass

gl_spec_calls = {"ПолучитьОписаниеОповещенияСВызовомФункции", "СоздатьОбъектОписанияОповещения"}
gl_spec_calls = {name.lower() for name in gl_spec_calls}

def find_spec_calls(gl_context, gl_funcs_to_move_primary):
    """
    Некоторые процедуры/функции вызываются особым образом через фукнкции
    ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
    Например:
        СоздатьОбъектОписанияОповещения("ВызватьФункцию", "Subsys_ОбщегоНазначенияКлиент")
    Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
    переносимых в основную форму.
    Кроме того, из за способа вызова эти функции должны оставаться экспортными.
    @param gl_context: базовый контекст
    @param gl_funcs_to_move_primary (set): список функций для перемещения в основную форму
    @return:
    """

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

    func_subcalls = gl_context.gl_func_subcalls[APP_TYPE_MANAGED]
    implicit_called_funcs = set()
    fill_implicit_called_funcs(gl_funcs_to_move_primary)
    return implicit_called_funcs

def update_funcs_to_move_secondary(gl_move_config, gl_context):
    """
     Некоторые процедуры/функции вызываются особым образом через фукнкции
     ПолучитьОписаниеОповещенияСВызовомФункции и СоздатьОбъектОписанияОповещения.
     Например:
       СоздатьОбъектОписанияОповещения("ВызватьФункцию", "ОбщегоНазначенияКлиент")
     Поэтому, их и их подвызовы необходимо вручную добавить в список процедур и функций
     переносимых в основную форму.
     Кроме того, из за способа вызова эти функции должны оставаться экспортными.
     """
    for form_name, funcs_to_move in gl_move_config.gl_all_funcs_desc_to_move_secondary.items():
        funcs_to_move_spec = find_spec_calls(gl_context, funcs_to_move)
        for called_func_name in funcs_to_move_spec:
            if not called_func_name in funcs_to_move:
                if not gl_move_config.gl_secondary_module_export_functions.get(form_name):
                    gl_move_config.gl_secondary_module_export_functions[form_name] = set()
                gl_move_config.gl_secondary_module_export_functions[form_name].add(called_func_name)
                move_funcs.update_secondary_form_calls(form_name, called_func_name, False,
                                                       gl_context, gl_move_config)
    pass


def handle_form_module_func_proc(func_proc_desc, sub_call_list):
    """
    Pаменяет второй параметр в вызове функций ПолучитьОписаниеОповещенияСВызовомФункции,
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
        if called_func_name_short.lower() in gl_spec_calls:
            if isinstance(call, strct1c.DottedExpression):
                call.properties_list[1].param_list[1] = strct1c.Identifier('ЭтотОбъект')
            else:
                raise Exception("Необработанный вызов : " + call)
    pass


def update_main_module_struct(main_form_struct):
    """
    Выполняет дополнение модуля основной формы после того как в неё были перенесены функции.
    @param main_form_struct: стуктура основной формы
    @return:
    """

    # Замена ссылок на некоторые глобальные переменные на обращения особого вида
    # Например, гл_Subsys_ИмяФайлаОбработки => Объект.КэшДанных.ИмяОбработки

    replacements = {"гл_iBank2_ИмяФайлаОбработки": "Объект.КэшДанных.ИмяОбработки",
                    "гл_iBank2_РежимРаботы": "Объект.КэшДанных.РежимРаботы"}

    replacements = {key.lower(): val for key, val in replacements.items()}
    filter = {x for x in replacements}

    id_call_list = []
    for func_proc_desc in main_form_struct.proc_funcs_list:
        id_call_list += utils.get_statements_call_list(func_proc_desc.body.statements, obj_type="id", filter=filter)

    for rec in id_call_list:
        id_name = rec[1]
        if id_name.lower() in replacements and isinstance(rec[0], strct1c.Identifier):
            rec[0].id = replacements[id_name.lower()]
    pass
