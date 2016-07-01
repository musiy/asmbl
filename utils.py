# -*- coding: utf-8 -*-

import os

def load_forms(dump_folder, extproc_name):
    form_props = dict()
    dump_files_list = [f for f in os.listdir(dump_folder) if os.path.isfile(os.path.join(dump_folder, f))]
    for file_name in dump_files_list:
        if file_name.lower().startswith(('Обработка.'+extproc_name+'.Форма').lower()):
            form_name = file_name.split('.')[3]
            is_managed = not form_name.endswith("Обычная")
            form_text = open(os.path.join(dump_folder, file_name), encoding='utf-8').read()
            form_props[form_name] = {'text_origin': form_text,
                                     'is_managed': is_managed,
                                     'file_name': file_name}
    return form_props


def load_common_modules(dump_folder, extproc_name):
    common_modules_props = dict()
    dump_files_list = [f for f in os.listdir(dump_folder) if os.path.isfile(os.path.join(dump_folder, f))]
    for full_file_name in dump_files_list:
        if full_file_name.startswith('ОбщийМодуль'):
            module_name = full_file_name.split('.')[1]
            #if module_name.lower().find(extproc_name.lower()) == -1:
                # общие модули должны содержать в названии имя обработки
                #continue
            is_client = False
            is_server = False
            is_client_server = False
            
            if module_name.lower().find("клиентсервер") >= 0:
                is_client_server = True
            elif module_name.lower().find("клиент") >= 0:
                is_client = True
            else:
                is_server = True

            text_origin = open(os.path.join(dump_folder, full_file_name), encoding='utf-8').read()
            common_modules_props[module_name] = {'text_origin': text_origin,
                                                 'is_client': is_client,
                                                 'is_server': is_server,
                                                 'is_client_server': is_client_server,
                                                 'file_name': full_file_name}
    return common_modules_props

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
