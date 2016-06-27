# -*- coding: utf-8 -*-

def get_statements_call_list(statements, obj_type = "function", filter = set()):
    """
    Обходит список инструкций (statements) и получает список вызываемых функций.
    Составляется общий список всех обращений к функциям во всех инструкциях.

    @param statements (struct.<инструкция верхнего уровня>): инструкции из процедуры/функции для обхода
    @return (list): список обращений к функциям, где каждый элемент - кортеж.
                    Каждый кортеж состоит из двух элементов: ссылка на структуру вызова, строка вызова.
                    Например: (<strct1c.DottedExpression object at 0x05BB74F0>,
                              'Subsys_СопоставлениеКлиентСервер.ПолучитьЦветТекстаРучнойКорректировки')

    """
    result = []
    for st in statements:
        func_list = st.get_tokens_list(obj_type, filter)
        result += func_list
    return result
