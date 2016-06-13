# -*- coding: utf-8 -*-

UNPACK_DIR_PATH = r'unpack'

# Файл описания конфигурации - основная точка отчсчета для начала работы.
# В файле описания конфигурации содержатся ссылки на метаданные, свойства конфигурации и пр.
# Имя файла описания конфигурации (он же идентификатор конфигурации) находится в файле root
# во второй позиции, например:
#    {2, d69cd807-e587-4c8b-bb1d-fe6b7b0d6bc7,}
# здесь имя файла конфигурации это d69cd807-e587-4c8b-bb1d-fe6b7b0d6bc7

# В файле описания конфигурации можно найти идентификаторы общих модулей, форм и т.д.:
# Идентификатор начала блока общих модулей
COMMON_MODULES_ID = "0fe48980-252d-11d6-a3c7-0050bae0a776"
# Идентификатор начала блока обработок
PROCESSORS_ID = "bf845118-327b-4682-b5c6-285d2a0eb296"
# Идентификатора начала блока описания форм обработки
FORMS_BLOCK_ID = "d5b0e5ed-256d-401c-9c36-f630cafd8a62"

def get_metadata_description(text):
    """
    Фактически стаб для вызовая функции process1cTree, что бы получить структуру
    метаописания как возвращаемый результат функции.
    @param text (str): данные в виде текста
    @return (list): структура
    """
    result = []
    process1cTree(text, result)
    return result


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


def load_text_file(file_name):
    """
    Загружает файл file_name относительно каталога UNPACK_DIR_PATH.
    При загрузке используется кодировка utf-8.
    @param file_name (str): имя файла
    @return (str): содержимое файла
    """
    return open(UNPACK_DIR_PATH + "\\" + file_name, encoding='utf-8').read()

def get_child_objects_ids(metadesc_text, id):
    pos = metadesc_text.find(id)
    if pos == -1:
        raise Exception("В файле описания структуры метаданных не найдены идентификатор блока начала списка")
    objects_list = []
    process1cTree(metadesc_text, objects_list, pos=(pos - 1))
    return objects_list[2:]

def get_common_modules_ids(conf_data_text):
    pos = conf_data_text.find(COMMON_MODULES_ID)
    if pos == -1:
        raise Exception("В файле описания структуры метаданных не найдены идентификатор блока общих модулей")
    common_modules_list = []
    process1cTree(conf_data_text, common_modules_list, pos=(pos - 1))
    return common_modules_list[2:]


def get_common_modules_texts(ids):
    modules = {}  # содержит текст общих модулей, ключ - имя общего модуля, значение - текст модуля
    for id in ids:
        module_desc_list = []
        process1cTree(load_text_file(id), module_desc_list)
        # получаем "чистое" имя модуля, например: "ЗарплатныйПроектКлиент"
        module_name = module_desc_list[1][1][2]
        # загружаем текст модуля
        modules[module_name] = load_text_file(id + ".0\\text")
    return modules

def get_extprocessor_id(conf_data_text, ep_name):
    pos = conf_data_text.find(PROCESSORS_ID)
    if pos == -1:
        raise Exception("В файле описания структуры метаданных не найдены идентификатор блока обработок")
    processors_list = []
    process1cTree(conf_data_text, processors_list, pos=(pos - 1))
    objective_ep_id = None
    for id in processors_list[2:]:
        data = load_text_file(id)
        pos = data.find(id)
        if pos == -1:
            # здесь должен
            raise Exception("Ошибка формата данных")
        # В файле с именем идентификатора содержится сам идентификатор, а после него имя обработки
        # Например: ..{0,0,6ad3aa26-477a-4d51-bb8f-e409807a7a8b},"ОбменСБанком",..
        # Проверяем, что имя обработки - "ОбменСБанком"
        pos += len(id)
        pos += 3
        if ep_name == data[pos:pos + len(ep_name)]:
            objective_ep_id = id
            break
    return objective_ep_id
