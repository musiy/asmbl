from epfcomp.base_const import *
from random import random
import re


# адресное пространство идентификаторов обфускации - 0..999999, т.е. идентификаторы i0-i999999
MAX_ID_COUNT = 999999

# при получении нового идентификатора обфускации он заносится в gl_ofuscation_ids для исключения дублирования
gl_ofuscation_ids = set()
def get_obf_id():
    while True:
        id = int(random() * MAX_ID_COUNT)
        if id not in gl_ofuscation_ids:
            gl_ofuscation_ids.add(id)
            break
    return 'i' + str(id)


def do_obfuscate(context, dataproc_module_config, params, form_handlers_replacements, debug):

    log('Подготовка идентификаторов для обфускации')

    # Идентификаторы заменяемые через замену текста.
    overall_ids_list = set()
    replacements_dict = dict()

    # заполнение идентификаторов замен названиями процедур и функций модуля объекта
    for func_desc in context.gl_ep_module['struct'].proc_funcs_list:
        overall_ids_list.add(func_desc.name)
    # функции составляющие изначальную прямую цепочку вызова из модуля объекта были вынесены из модуля при формировании текста модуля
    for full_func_name in dataproc_module_config.dp_module_chain:
        overall_ids_list.add(full_func_name.split('.')[2])

    # заполнение идентификаторов замен именами глобальных переменных модуля объекта
    for var_decl in context.gl_ep_module['struct'].global_vars_list:
        for var_desc in var_decl.vars_list:
            overall_ids_list.add(var_desc.name)

    # заполнение идентификаторов замен названиями процедур и функций модулей форм
    for form_name, forp_prop in context.gl_form_props.items():
        for func_desc in forp_prop['struct'].proc_funcs_list:
            if debug and func_desc.name in form_handlers_replacements[form_name]:
                continue
            overall_ids_list.add(func_desc.name)

    # добавление идентификаторов предложенных к замене в параметрах
    for id_name in params['force']:
        overall_ids_list.add(id_name)

    # удаление идентификаторов, исключаемых из замены
    for id_name in params['except']:
        try:
            overall_ids_list.remove(id_name)
        except:
            except_text = 'Идентификатор "' + id_name + '" не найден среди имен идентификаторов к обфускации'
            if debug:
                log(except_text)
            else:
                raise Exception(except_text)

    for id in overall_ids_list:
        replacements_dict[id.lower()] = get_obf_id()

    # Заполняем идентификаторов для замен обработчиков в форме
    for form_name, form_handlers in form_handlers_replacements.items():
        for handler_name in form_handlers:
            form_handlers[handler_name] = replacements_dict.get(handler_name.lower(), None)

    log('Обфускация модуля объекта обработки')

    # замены в модуле объекта
    context.gl_ep_module['text'] = replace_ids(context.gl_ep_module['text'], replacements_dict)

    # замены в модулях форм
    for full_form_name, form_prop in context.gl_form_props.items():
        log('Обфускация модуля формы: ' + full_form_name)
        form_prop['text'] = replace_ids(form_prop['text'], replacements_dict)

    return replacements_dict

def replace_ids(text, replacements_dict):
    regex_rule = '|'.join(replacements_dict)
    regex = re.compile(r'\b(' + regex_rule + r')\b', re.IGNORECASE)

    match = regex.search(text, 0)
    while match:
        old_value = text[match.start():match.end()]
        new_value = replacements_dict.get(old_value.lower(), '<<идентификатор замены не найден>>')
        text = text[:match.start()] + new_value + text[match.end():]
        pos = match.end() - (len(old_value) - len(new_value))
        match = regex.search(text, pos)
    return text

