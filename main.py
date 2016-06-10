# -*- coding: utf-8 -*-

import copy
import pickle
import os.path
import parser1c
import preproc1c
import strct1c

UNPACK_DIR_PATH = r'unpack'

# Идентификатор начала блока общих модулей в файле описания конфигурации (d69cd807-e587-4c8b-bb1d-fe6b7b0d6bc7)
COMMON_MODULES_ID = "0fe48980-252d-11d6-a3c7-0050bae0a776"

# Идентификатор начала блока обработок в файле описания конфигурации (d69cd807-e587-4c8b-bb1d-fe6b7b0d6bc7)
PROCESSORS_ID = "bf845118-327b-4682-b5c6-285d2a0eb296"

# Идентификатора начала блока описания форм обработки
FORMS_BLOCK_ID = "d5b0e5ed-256d-401c-9c36-f630cafd8a62"

PROCESSOR_NAME = "iBank2"

DEBUG_MODE = True

def process1cTree(text, elements, *, pos=1):
    """
    Рекурсивно обходит описание данных во внутреннем формате 1С и записывает их в структуру вложенных списков.
    Разбор начинается с произвольной позиции начала блока данных - символа '{'.

    Описание:
        Группа данных обрамляется в фигурные скобки: {<блок данных>}
        Блок данных состоит из произвольного числа элементов: строки, числа идентфикаторы,
        либо другие блоки данных, раздененные запятыми.
        Пример: {10, 09736b02-9cac-4e3f-b4f7-d3e9576ab948, "проивзольный текст",
                     {20, #base64:77u/PCFET0NUWVBFIGh0bWwgUFVC..}}

    Аргументы:
        text (str) : строка содержащая блок данных, например {2, "тест", {7}}
        elements (list) : список в который следует добавить элементы на текущем уровне разбора
        pos (int) : позиция в строке для продолжения разбора
    Возвращаемое значение:
        int : позиция закрывающейся скобки на текущем уровне разбора
    """

    def prepareElement(value):
        if value.isdigit():
            return int(token)
        else:
            return token

    token = ''
    while True:
        pos += 1
        if text[pos] == '\n':
            pass
        elif text[pos] == '{':
            subList = []
            elements.append(subList)
            pos = process1cTree(text, subList, pos=pos)
        elif text[pos] == ',':
            if (token):
                elements.append(prepareElement(token))
            token = ''
        elif text[pos] == '}':
            if (token):
                elements.append(prepareElement(token))
            return pos
        elif text[pos] == '"':
            # строки необходимо искать отдельно, т.к. могут встречаться и запятые и фигурные скобки и др.
            pos += 1
            while True:
                # Лишь одинарная кавычка означает конец блока строки.
                # Двойная кавычка это всегда экранирование.
                new_pos = text.find('"', pos)
                if new_pos == -1:
                    raise Exception("Ошибка выделения значения строки из файла описания CF")
                if text[new_pos + 1] == '"':
                    # увеличиваем токен на отрезок текста завершающийся одним символом двойной кавычки
                    token += text[pos: new_pos + 1]
                    # и смещаем позицию на символ следующий после второй кавычки
                    pos = new_pos + 2
                else:
                    # увеличиваем токен на отрезок текста исключая символ двойной кавычки
                    token += text[pos: new_pos]
                    pos = new_pos
                    break
            elements.append(token)
            token = ''
        else:
            token += text[pos]


def loadTextFile(fileName):
    return open(UNPACK_DIR_PATH + "\\" + fileName, encoding='utf-8').read()


def getModulesIds(conf_data_text):
    pos = conf_data_text.find(COMMON_MODULES_ID)
    if pos == -1:
        raise Exception("В файле описания структуры метаданных не найдены идентификатор блока общих модулей")
    common_modules_list = []
    process1cTree(conf_data_text, common_modules_list, pos=(pos - 1))
    return common_modules_list[2:]


def getModules(ids):
    modules = {}  # содержит текст общих модулей, ключ - имя общего модуля, значение - текст модуля
    for id in ids:
        module_desc_list = []
        process1cTree(loadTextFile(id), module_desc_list)
        # получаем "чистое" имя модуля, например: "ЗарплатныйПроектКлиент"
        module_name = module_desc_list[1][1][2]
        # загружаем текст модуля
        modules[module_name] = loadTextFile(id + ".0\\text")
    return modules


def getObjectiveEpId(conf_data_text):
    pos = conf_data_text.find(PROCESSORS_ID)
    if pos == -1:
        raise Exception("В файле описания структуры метаданных не найдены идентификатор блока обработок")
    processors_list = []
    process1cTree(conf_data_text, processors_list, pos=(pos - 1))
    objective_ep_id = None
    for id in processors_list[2:]:
        data = loadTextFile(id)
        pos = data.find(id)
        if pos == -1:
            # здесь должен
            raise Exception("Ошибка формата данных")
        # В файле с именем идентификатора содержится сам идентификатор, а после него имя обработки
        # Например: ..{0,0,6ad3aa26-477a-4d51-bb8f-e409807a7a8b},"ОбменСБанком",..
        # Проверяем, что имя обработки - "ОбменСБанком"
        pos += len(id)
        pos += 3
        if PROCESSOR_NAME == data[pos:pos + len(PROCESSOR_NAME)]:
            objective_ep_id = id
            break
    return objective_ep_id


def getSubobjects(ep_metadata, id):
    pos = ep_metadata.find(id)
    if pos == -1:
        raise Exception("В файле описания структуры метаданных не найдены идентификатор блока начала списка")
    objects_list = []
    process1cTree(ep_metadata, objects_list, pos=(pos - 1))
    return objects_list[2:]


################################################################################
## Первый этап - получение текста общих модулей и модулей форм конфигурации.
## Модули можно загрузить различными способами - либо с использованием стандартной
## выгрузки 1С:Предприятия, либо через unpack.
## Ниже используется решение через структуру unpack.

# Файл root содержит идентификатор файла с описанием конфигурации
root_list = []
process1cTree(loadTextFile("root"), root_list)
# rootList[1] - идентификатор файла с описанием конфигурации
conf_data_text = loadTextFile(root_list[1])

conf_data_list = []
process1cTree(conf_data_text, conf_data_list)
# идентификатор конфигурации
conf_id = conf_data_list[3][1][1][1][1][1][2]

gl_app_module = dict()
gl_app_module['ordinary_app_text'] = loadTextFile(conf_id + ".0\\text")
gl_app_module['managed_app_text'] = loadTextFile(conf_id + ".6\\text")

modules_ids = getModulesIds(conf_data_text)

# содержимое общих модулей
common_modules = getModules(modules_ids)
gl_common_modules_props = {}

for name in common_modules:
    if name.lower().find("test") >= 0:
        continue
    is_client = False
    is_server = False
    is_client_server = False
    # todo определять в каком контексте выполняется модуль следует по файлу описания модуля
    if name.lower().find("клиентсервер") >= 0:
        is_client_server = True
    elif name.lower().find("клиент") >= 0:
        is_client = True
    else:
        is_server = True

    gl_common_modules_props[name] = {'text': common_modules[name],
                                     'is_client': is_client,
                                     'is_server': is_server,
                                     'is_client_server': is_client_server}

# Получение идентификатора обработки.
objective_ep_id = getObjectiveEpId(conf_data_text)

# Информацию о структуре обработки можно найти в файле с именем этого идентификатора.
ep_metadata = loadTextFile(objective_ep_id)

# Идентификаторы форм объектов
objective_ep_forms_ids = getSubobjects(ep_metadata, FORMS_BLOCK_ID)

## Получение текстов модулей форм

if DEBUG_MODE and os.path.isfile('map_form_id_to_name.pickle'):
    with open('map_form_id_to_name.pickle', 'rb') as f:
        map_form_id_to_name = pickle.load(f)
    with open('gl_form_props.pickle', 'rb') as f:
        gl_form_props = pickle.load(f)
else:
    # хранит соотвествие имени формы её идентификатору
    map_form_id_to_name = {id: None for id in objective_ep_forms_ids}
    # Свойства формы - текст и признак того, является ли она управляемой/обычной
    gl_form_props = {}

    for form_id in objective_ep_forms_ids:
        form_meta = []
        # загрузка описания формы
        process1cTree(loadTextFile(form_id), form_meta)

        # имя формы
        form_name = form_meta[1][1][1][1][2]

        # запись {'ид формы': 'имя формы'}
        map_form_id_to_name[form_id] = form_name

        # Опытным путём установлено, что признаком является ли форма управляемой или обычной
        # является значение свойства [1][1][1][3] - если 1 то это управляемая форма, иначе обычная.
        # Примечание. Косвенным признаком, является ли форма управляемой или обычной может служить
        # имя формы, которое зависит от разработчика конфигурации.
        is_managed = form_meta[1][1][1][3] == 1
        if is_managed:
            form_struct = []
            # Метаданные и код управляемой формы можно получить из файла id+'.0'
            pos = process1cTree(loadTextFile(form_id + '.0'), form_struct)
            form_text = form_struct[2]
        else:
            # Код обычной формы можно получить из файла id+'.0/module'
            form_text = loadTextFile(form_id + '.0/module')
        gl_form_props[form_name] = {'text': form_text, 'is_managed': is_managed}

    if DEBUG_MODE:
        with open('map_form_id_to_name.pickle', 'wb') as f:
            pickle.dump(map_form_id_to_name, f)
        with open('gl_form_props.pickle', 'wb') as f:
            pickle.dump(gl_form_props, f)


############################################################################################
## На даном этапе модули загружены и следущий большой этап - преобразование и перенос текста
## из общих модулей в модули форм.

# Шаг №1. Вставка символа точки с запятой после инструкции препроцессора #КонецЕсли.
#          Это нужно для дальнейшей успешной загрузки модуля в синтаксический процессор.
#          В сущности инструкции препроцессора не являются инструкциями, поэтому
#          не завершаются точкой с запятой в коде 1С. Но для удобства обработки кода
#          с использованием синтаксического процессора 1Сика они считаются инструкциями,
#          такими же как if .. else .. endif, и поэтому должны оканчиваться точкой с запятой.

def addSemicolonAfterPreproc(module_text):
    pos = 0
    while True:
        pos = module_text.find('#КонецЕсли', pos)
        if pos == -1:
            break
        module_text = module_text[0:pos + 10] + '\n;' + module_text[pos + 10:]
        pos += 10 + 3;
    return module_text


for name in gl_form_props:
    gl_form_props[name]['text'] = addSemicolonAfterPreproc(gl_form_props[name]['text'])

for name in gl_common_modules_props:
    gl_common_modules_props[name]['text'] = addSemicolonAfterPreproc(gl_common_modules_props[name]['text'])

# Шаг №2. Разделение кода на две части - под обычное и управляемое приложение.
#          Так же выполняется удаление областей.
#          Тут же проивзодится получение синтаксической структуры модулей (см. parse).

# todo список вырезаемых областей типа ["DEBUG"] должен параметризоваться
EXCLUDE_AREAS = ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"]

preproc = preproc1c.Preprocessor1C(gl_app_module["ordinary_app_text"])
gl_app_module["ordinary_app_text"] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS)
gl_app_module["ordinary_app_struct"] = parser1c.parser.parse(gl_app_module["ordinary_app_text"])

preproc = preproc1c.Preprocessor1C(gl_app_module["managed_app_text"])
gl_app_module["managed_app_text"] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS)
gl_app_module["managed_app_struct"] = parser1c.parser.parse(gl_app_module["managed_app_text"])

for name in gl_form_props:
    context = "ТонкийКлиент" if gl_form_props[name]['is_managed'] else "ТолстыйКлиентОбычноеПриложение"
    # Разрешить препроцессор, избавиться от областей
    preproc = preproc1c.Preprocessor1C(gl_form_props[name]['text'])
    new_text = preproc.execute(context, EXCLUDE_AREAS, ["НаКлиенте"])
    gl_form_props[name]['text'] = new_text
    # Получить синтаксическую структуру модуля
    gl_form_props[name]['struct'] = parser1c.parser.parse(new_text)

if DEBUG_MODE and os.path.isfile('gl_common_modules_props.pickle'):
    with open('gl_common_modules_props.pickle', 'rb') as f:
        gl_common_modules_props = pickle.load(f)
else:
    for name in gl_common_modules_props:
        # Разрешить препроцессор, избавиться от областей
        preproc = preproc1c.Preprocessor1C(gl_common_modules_props[name]['text'])
        try:
            module = gl_common_modules_props[name]
            module['text_managed'] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS, ["НаКлиенте"])
            module['text_ordinary'] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS, ["НаКлиенте"])

            module['struct_managed'] = parser1c.parser.parse(module['text_managed'])
            module['struct_ordinary'] = parser1c.parser.parse(module['text_ordinary'])
        except:
            raise Exception("Ошибка при разборе модуля : " + name)

    if DEBUG_MODE:
        with open('gl_common_modules_props.pickle', 'wb') as f:
            pickle.dump(gl_common_modules_props, f)


# Шаг №3. Формирование списка вызовов для каждой функции каждой формы и модуля
#          Эти списки будут использованы на следующем этапе для формирования модулей форм.
#          Структура списка следующая:
#            имя_формы.имя_функции: {имя_локальной_функции_формы, .., имя_модуля.имя_функции}
#            имя_модуля.имя_функции: {имя_локальной_функции_модуля, .., имя_модуля.имя_функции}

# exit (0)

def getStatementCallList(statements, obj_type = "function", filter = set()):
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


# todo переносить вручную функции
# мсвИменаФункций.Добавить("СоздатьОбъектОписанияОповещения");
# мсвИменаФункций.Добавить("ПолучитьОписаниеОповещенияСВызовомФункции");

# Общий список всех процедур и функций во всех модулях.
# В соотвествии имени каждой функции ставится её описание (структура) - для дальнейшей обработки и переноса в форму.
gl_proc_funcs = {}

# заполнене списка процедур и функций для общих модулей
for name in gl_common_modules_props:
    # todo сперва для управляемого приложения
    struct = gl_common_modules_props[name]['struct_managed']
    for proc_func in struct.proc_func_list:
        key = "CommonModule." + name + "." + proc_func.name
        gl_proc_funcs[key] = proc_func

# заполнене списка процедур и функций для форм
for form_name in gl_form_props:
    # todo сперва для управляемого приложения
    struct = gl_form_props[form_name]['struct']
    if form_name.lower().find("обычная") >= 0:
        continue
    for proc_func in struct.proc_func_list:
        key = "FormManaged." + form_name + "." + proc_func.name
        gl_proc_funcs[key] = proc_func


def get_proc_func_call_list(proc_func, module_type, module_name):
    '''
    По переданному описанию функции составляет список вызываемых из неё процедур и функций.
    @param proc_func (strct1c.Function): описание функций
    @param module_type (str): тип модуля: CommonModule, FormManaged, FormOrdinary
    @param module_name (str): имя общего модуля или формы
    @return (set): список вызываемый функций с полным путем к ним: CommonModule.<имя модуля>.<имя процедуры/функции>
    '''
    global gl_proc_funcs
    # todo удалить
    if proc_func.name.find('ИнициализоватьТаблицыФормы') >= 0:
        a = 1

    # все функции, в т.ч. встроенные и функции объектов
    func_list = getStatementCallList(proc_func.body.statements)
    result = dict()
    for func_rec in func_list:
        func_name = func_rec[1]
        if func_name.find('.') >= 0:
            # вызов разделенный точкой - обращение к функции другого общего модуля
            full_name = "CommonModule" + "." + func_name
        else:
            # обращение к функции этого модуля
            full_name = module_type + "." + module_name + "." + func_name
        # отбираем только функции модулей (без встроенных функций)
        if gl_proc_funcs.get(full_name, None):
            # в функции может быть несколько обращений к одной и тойже (другой) функции
            val = result.get(full_name, [])
            val.append(func_rec[0])
            result[full_name] = val
    return result


# Содержит список вызовов для каждой процедуры/функции во всех модулях и во всех формах
gl_func_calls = {}

# цикл заполняет gl_func_calls по процедурам и функциями общих модулей
for module_name in gl_common_modules_props:
    # todo сперва для управляемого приложения
    struct = gl_common_modules_props[module_name]['struct_managed']
    for proc_func in struct.proc_func_list:
        key = "CommonModule." + module_name + "." + proc_func.name
        sub_calls_dict = get_proc_func_call_list(proc_func, "CommonModule", module_name)
        gl_func_calls[key] = sub_calls_dict

# цикл заполняет gl_func_calls по процедурам и функциями форм
for form_name in gl_form_props:
    if form_name.lower().find("обычная") >= 0:
        # это управляемая форма todo
        continue
    form_struct = gl_form_props[form_name]['struct']
    for proc_func in form_struct.proc_func_list:
        key = "FormManaged." + form_name + "." + proc_func.name
        sub_calls_dict = get_proc_func_call_list(proc_func, "FormManaged", form_name)
        gl_func_calls[key] = sub_calls_dict

# Шаг 4. Перенос функций из общих модулей в модули формы.
#        todo сперва перенос в основную управляемую форму

# Содержит список функций для переноса в освновную форму / модуль
gl_proc_funcs_to_move_primary = set()

key_managed_main_form = "FormManaged.Основная"


def fill_main_module_calls(full_func_name):
    """
    Рекурсивно обходит всё дерево вызовов из переданной full_func_name и добавляет
    каждый вызов в gl_proc_funcs_to_move_primary.
    На самом верхнем уровне функция вызывается для каждой процедуры/функции модуля формы.
    Далее вызов продолжается для каждого дочернего вызова и т.д. до последнего вызова.
    @param full_func_name (str): имя процедуры/функции в формате CommonModule.<ИмяМодуля>.<ИмяПроцедурыФункции>
    @return: None
    """
    # объявить переменную как глобальную, т.к. производится модификация
    global gl_proc_funcs_to_move_primary

    # получить вызовы из full_func_name
    sub_calls = gl_func_calls.get(full_func_name)

    for func_name in sub_calls:
        if func_name in gl_proc_funcs_to_move_primary:
            # если подвызов уже добавлен в функции для переноса - пропускаем, что бы не было зацикливания
            pass
        else:
            if func_name[:len(key_managed_main_form)] != key_managed_main_form:
                # не нужно добавлять в список процедуры и функций, которые уже есть в модуле
                gl_proc_funcs_to_move_primary.add(func_name)
            fill_main_module_calls(func_name)
    pass


for full_func_name in gl_func_calls:
    if full_func_name[:len(key_managed_main_form)] == key_managed_main_form:
        fill_main_module_calls(full_func_name)

###################################################################################################
# Необходимо обновить список переносимых функций вызываемых особым образом, через Выполнить()
# Для этого необходимо проверить все обращения к функциям ПолучитьОписаниеОповещенияСВызовомФункции
# и СоздатьОбъектОписанияОповещения и собрать их названия.
# Кроме того, из за способа вызова эти функции должны оставаться экспортными.

spec_replace_params = {"ПолучитьОписаниеОповещенияСВызовомФункции", "СоздатьОбъектОписанияОповещения"}
spec_replace_params = {name.lower() for name in spec_replace_params}

# Функций, которые вызываются через Выполнить(..).
# Для них нельзя снимать признак экспортности.
gl_func_to_add_spec = set()

for full_func_name in gl_proc_funcs_to_move_primary:
    func_proc_desc = gl_proc_funcs[full_func_name]
    parts = full_func_name.split(".")
    sub_call_list = get_proc_func_call_list(func_proc_desc, parts[0], parts[1])

    for called_func_name, calls in sub_call_list.items():
        called_func_name_short = called_func_name.split(".")[2]
        if called_func_name_short.lower() in spec_replace_params:
            for call in calls:
                if isinstance(call, strct1c.FuncCall):
                    func_name = call.param_list[0].value[0]
                    module_name = call.param_list[1].value[0]
                elif isinstance(call, strct1c.DottedExpression):
                    func_name = call.properties_list[1].param_list[0].value[0]
                    module_name = call.properties_list[1].param_list[1].value[0]
                else:
                    raise Exception("Необработанный вызов : " + call)
                gl_func_to_add_spec.add("CommonModule." + module_name + "." + func_name)

for full_func_name in gl_func_to_add_spec:
    if not full_func_name in gl_proc_funcs_to_move_primary:
        gl_proc_funcs_to_move_primary.add(full_func_name)
        fill_main_module_calls(full_func_name)

###################################################################################################
# Cодержит список функций для переноса во вспомогательные формы
#   ключ - имя формы,
#   значение - список функций для переноса
gl_proc_funcs_to_move_secondary = {}

# Содержит список обращений к функциям, вызовы к которым необходимо заменить на обращение к основной форме:
# Например, вызов
#   System_ОбщегоНазначениеКлиентСервер.СообщитьПользователю(..)
# Будет заменен в итоговой форме на:
#   ПолучитьОсновногоВладельцаФормы(ЭтаФорма).СообщитьПользователю(..)
# Структура переменной:
#   ключ - имя формы
#   значение - имя функции которую следует заменить
gl_replace_calls_to_main_module = {}


def fill_secondary_form_calls(form_name, full_func_name, is_server_chain=False):
    """
    Вычисляет процедуры и функции для переноса во вспомогательную форму.
    При этом, заполняет gl_proc_funcs_to_move_secondary - список функций для переноса.
    А так же заполняет gl_replace_calls_to_main_module - список функций для обращения через основной модуль.

    @param form_name (str): ключ для работы с gl_proc_funcs_to_move_secondary
    @param full_func_name (str): функция из цепочки вызовов, на основе контекста модуля будет определяться
                                 следует ли переносить её во вспомогательную форму или заменять вызов
                                 на обращение к основной форме:
                                    клиентская - переносить, если нет в основной форме
                                    клиент-серверная - переносить, если нет в основной форме
                                    серверная - переносить всегда
    @param is_server_chain (bool): признак обработки цепочки серверного вызова.
                                   Если True, то необходимо переносить все клиент-серверные процедуры и функции
                                   безусловно во вспомогательную форму (серверные вызовы и так будут перенесены,
                                   а клиентских вызовов из серверного быть не может).
    @return:
    """
    sub_call_list = gl_func_calls.get(full_func_name)
    if is_server_chain:
        # для серверной цепочки безусловно переносим процедуру/функцию во вспомогательную форму
        if full_func_name in gl_proc_funcs_to_move_secondary[form_name]:
            return
        gl_proc_funcs_to_move_secondary[form_name].add(full_func_name)
        new_is_server_chain = is_server_chain
    else:
        # если цепочка не серверная - определяем по контексту функции куда её переносить
        parts = full_func_name.split(".")
        module_props = gl_common_modules_props[parts[1]]
        new_is_server_chain = module_props['is_server']
        if (module_props['is_client'] or module_props['is_client_server']) \
                and full_func_name in gl_proc_funcs_to_move_primary:
            if full_func_name in gl_replace_calls_to_main_module[form_name]:
                return
            gl_replace_calls_to_main_module[form_name].add(full_func_name)
        else:
            # если функция серверная, или клиентская/клиент серверная но не переносится в основную форму
            if full_func_name in gl_proc_funcs_to_move_secondary[form_name]:
                return
            gl_proc_funcs_to_move_secondary[form_name].add(full_func_name)
    for sub_call in sub_call_list:
        # sub_call это обращение к функции, например:
        #   CommonModule.System_ЗарплатныйПроект.ВыборПлатежногоПоручения_ПриСозданииНаСервере
        fill_secondary_form_calls(form_name, sub_call, new_is_server_chain)


KEY_FORM_MANAGED = "FormManaged"
for full_func_name in gl_func_calls:

    parts = full_func_name.split(".")
    if parts[0] != KEY_FORM_MANAGED or parts[1].lower() == "основная":
        # отбираем только вспомогательные формы
        continue

    is_server_chain = False
    directive = gl_proc_funcs[full_func_name].directive.lower()
    if directive == "&насервере" or directive == "&насерверебезконтекста":
        # это "чистый" серверный вызов - все клиент-серверные процедуры
        # и функции необходимо переносить в форму
        is_server_chain = True

    # имя формы, например "Письма"
    form_name = parts[1]

    # инициализция списка для формы в gl_proc_funcs_to_move_secondary
    val = gl_proc_funcs_to_move_secondary.get(form_name, None)
    if val == None:
        gl_proc_funcs_to_move_secondary[form_name] = set()
        gl_replace_calls_to_main_module[form_name] = set()

    for sub_call in gl_func_calls[full_func_name]:
        fill_secondary_form_calls(form_name, sub_call, is_server_chain)

    # Одна и та же клиент-серверная процедура/функция может быть добавлена и в
    # gl_proc_funcs_to_move_secondary и в gl_replace_calls_to_main_module
    # Это может происходить в ситуациях, когда она:
    #   А) есть в основной форме
    #   Б) есть в клиенской цепочке вызова вспомогательной формы
    #   В) есть в серверной цепочке вызова вспомогательной формы
    # Такие процедуры/функции необходимо удалить из gl_replace_calls_to_main_module.
    for func_proc_name in gl_proc_funcs_to_move_secondary[form_name]:
        if func_proc_name in gl_replace_calls_to_main_module[form_name]:
            gl_replace_calls_to_main_module[form_name].remove(func_proc_name)
    pass

# Функции из основной формы которые должны оставаться экспортными,
# так как к ним есть обращение из вспомогательных форм.
gl_main_module_export_functions = set()
for form_name in gl_replace_calls_to_main_module:
    for full_func_name in gl_replace_calls_to_main_module[form_name]:
        gl_main_module_export_functions.add(full_func_name)

for full_func_name in gl_func_to_add_spec:
    gl_main_module_export_functions.add(full_func_name)

def replace_common_module_calls(call_list):
    """
    Выполняет замену обращений к общим модулям в функции full_func_name на вызовы локальных процедур/функций.
    Например:
        "Subsys_ОбщегоНазначенияКлиентСервер.Проверить(..)" => "Проверить(..)"
    @param call_list (str): список для замены
    @return: None
    """
    for called_func_name, call_list in call_list.items():
        # из функции может быть несколько обращений к другой функции
        for call in call_list:
            if isinstance(call, strct1c.DottedExpression):
                call.properties_list.pop(0)
            elif isinstance(call, strct1c.PropertyIndexed):
                # todo обработать ситуацию f()[1][2]
                raise Exception("Вызов f()[expr] не обработан: " + called_func_name)

# Описание основной управляемой формы
main_form_proc_func_list = gl_form_props['Основная']['struct'].proc_func_list

# Удаление обращений из процедур/функций формы (обработчиков)
for func_proc_desc in main_form_proc_func_list:
    full_func_name = key_managed_main_form + "." + func_proc_desc.name
    sub_call_list = gl_func_calls[full_func_name]
    replace_common_module_calls(sub_call_list)

#########################################################################################################
# Перенос в основную форму.
# При переносе функций во вспомогательную форму необходимо добавить директиву.
# Директива зависит от контекста исполнения общего модуля:
#   клиент        - &НаКлиенте
#   сервер        - &НаСервереБезКонтекста
#   клиент-сервер - &НаКлиентеНаСервереБезКонтекста

for full_func_name in gl_proc_funcs_to_move_primary:
    func_proc_desc = copy.deepcopy(gl_proc_funcs[full_func_name])

    parts = full_func_name.split(".")
    module_properties = gl_common_modules_props[parts[1]]

    if module_properties['is_client']:
        func_proc_desc.directive = "&НаКлиенте"
    elif module_properties['is_server']:
        func_proc_desc.directive = "&НаСервереБезКонтекста"
    elif module_properties['is_client_server']:
        func_proc_desc.directive = "&НаКлиентеНаСервереБезКонтекста"
    else:
        raise Exception("Не определен контекст вызова функции общего модуля: " + full_func_name)

    if not full_func_name in gl_main_module_export_functions:
        # нет обращения из вспомогательной формы, т.е. есть только в основной форме
        func_proc_desc.is_export = False
    main_form_proc_func_list.append(func_proc_desc)
    if parts[2] == "ОткрытьФормуПлатежногоПоручения":
        a = 1
    sub_call_list = get_proc_func_call_list(func_proc_desc, parts[0], parts[1])
    replace_common_module_calls(sub_call_list)
    for called_func_name, calls in sub_call_list.items():
        called_func_name_short = called_func_name.split(".")[2]
        if called_func_name_short.lower() in spec_replace_params:
            for call in calls:
                if isinstance(call, strct1c.FuncCall):
                    call.param_list[1] = strct1c.Identifier('ЭтаФорма')
                else:
                    call.properties_list[0].param_list[1] = strct1c.Identifier('ЭтаФорма')

    pass

#########################################################################################################
# Замена ссылок на некоторые глобальные переменные из
# todo соотвествие для замен брать из файла настроек

replacements = {"гл_iBank2_ИмяФайлаОбработки": "Объект.КэшДанных.ИмяОбработки",
                "гл_iBank2_РежимРаботы": "Объект.КэшДанных.РежимРаботы"}

replacements = { var.lower(): replace_str for var, replace_str in replacements.items()}
filter={x for x in replacements}

id_call_list = []
for func_proc_desc in main_form_proc_func_list:
    id_call_list += getStatementCallList(func_proc_desc.body.statements, obj_type="id", filter=filter)

for rec in id_call_list:
    id_name = rec[1]
    if id_name.lower() in replacements and isinstance(rec[0], strct1c.Identifier):
        rec[0].id = replacements[id_name.lower()]

########################################################################################################
# перенести в модуль основной формы глобальные переменные
for gl_var_desc in gl_app_module["managed_app_struct"].global_vars:
    if PROCESSOR_NAME.lower() in gl_var_desc.vars_list[0].name.lower():
        gl_var_desc_new = copy.deepcopy(gl_var_desc)
        gl_var_desc_new.directive = "&НаКлиенте"
        gl_form_props['Основная']['struct'].global_vars.append(gl_var_desc_new)

main_form_text = strct1c.get_text(gl_form_props['Основная']['struct'])

##############################################################################################
# Перенос во вспомогательную основную форму.
# При переносе функций во вспомогательную форму необходимо удалить признак экспортной функции.
# gl_proc_funcs_to_move_secondary
# gl_replace_calls_to_main_module

# Во вспомогательных управляемых формах
# а) добавить переменную модуля формы ОсновнаяФорма
# б) в обработчик ПриОткрытии (должен быть добавлен во все формы) добавить вызов ОсновнаяФорма = ПолучитьОсновнуюФорму() (вместо ПолучитьОсновногоВладельцаФормы)
# в) во обращениях к основной форме вместо ПолучитьОсновногоВладельцаФормы() использовать ОсновнаяФорма

pass
