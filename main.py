# -*- coding: utf-8 -*-

import copy
import pickle
import os.path
import parser1c
import preproc1c
import strct1c
import utilscf

# Используется для отбора среди обработок нужной
PROCESSOR_NAME = "iBank2"

# Использовать кеширование, в этом случае некоторые структуры данных будут выгружены на диск
# Для того что бы в следующий раз не вычислять их
CACHE_MODE_ON = True

################################################################################
# Первый этап - получение текста общих модулей, модулей управляемого и обычного
# приложения, а так же модулей форм обработки конфигурации.
# Модули можно загрузить различными способами - либо с использованием стандартной
# выгрузки 1С:Предприятия, либо через unpack.
# Ниже используется решение через структуру unpack.

# Файл root содержит идентификатор файла с описанием конфигурации
root_data = utilscf.get_metadata_description(utilscf.load_text_file("root"))

# rootList[1] - идентификатор файла с описанием конфигурации
# conf_desc_text содержит текст описания метаданных конфигурации (ссылки на все метаданные)
conf_desc_text = utilscf.load_text_file(root_data[1])
conf_data = utilscf.get_metadata_description(conf_desc_text)

# идентификатор объекта описания модулей приложения конфигурации
app_module_id = conf_data[3][1][1][1][1][1][2]

# в подкаталогах <conf_id>+".0" и <conf_id>+".6" находятся тексты модулей обычного и управляемого приложений
gl_app_module = dict()
gl_app_module['ordinary_app_text_origin'] = utilscf.load_text_file(app_module_id + ".0\\text")
gl_app_module['managed_app_text_origin'] = utilscf.load_text_file(app_module_id + ".6\\text")

# идентификаторы общих модулей
modules_ids = utilscf.get_common_modules_ids(conf_desc_text)

# содержимое общих модулей
common_modules = utilscf.get_common_modules_texts(modules_ids)

gl_common_modules_props = {}
for name in common_modules:
    if name.lower().find("test") >= 0:
        # пропускаем тестовые общие модули, хотя правильнее не выгружать их через conf_robber
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

    gl_common_modules_props[name] = {'text_origin': common_modules[name],
                                     'is_client': is_client,
                                     'is_server': is_server,
                                     'is_client_server': is_client_server}


# Этап №2. Получение текстов модулей форм.

# Получение идентификатора обработки
objective_ep_id = utilscf.get_extprocessor_id(conf_desc_text, PROCESSOR_NAME)
# Информацию о структуре обработки можно найти в файле с именем этого идентификатора.
ep_metadesc_text = utilscf.load_text_file(objective_ep_id)
# Идентификаторы форм обработки
ep_forms_ids = utilscf.get_child_objects_ids(ep_metadesc_text, utilscf.FORMS_BLOCK_ID)

## Получение текстов модулей форм

if CACHE_MODE_ON and os.path.isfile('map_form_id_to_name.pickle'):
    with open('map_form_id_to_name.pickle', 'rb') as f:
        map_form_id_to_name = pickle.load(f)
    with open('gl_form_props.pickle', 'rb') as f:
        gl_form_props = pickle.load(f)
else:
    # хранит соотвествие имени формы её идентификатору
    map_form_id_to_name = dict()
    # Свойства формы - текст и признак того, является ли она управляемой/обычной
    gl_form_props = {}

    for form_id in ep_forms_ids:
        # загрузка описания формы
        form_meta = utilscf.get_metadata_description(utilscf.load_text_file(form_id))
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
            # Метаданные и код управляемой формы можно получить из файла id+'.0'
            form_struct = utilscf.get_metadata_description(utilscf.load_text_file(form_id + '.0'))
            form_text = form_struct[2]
        else:
            # Код обычной формы можно получить из файла id+'.0/module'
            form_text = utilscf.load_text_file(form_id + '.0/module')
        gl_form_props[form_name] = {'text_origin': form_text, 'is_managed': is_managed}

    if CACHE_MODE_ON:
        with open('map_form_id_to_name.pickle', 'wb') as f:
            pickle.dump(map_form_id_to_name, f)
        with open('gl_form_props.pickle', 'wb') as f:
            pickle.dump(gl_form_props, f)


############################################################################################
## На даном этапе модули загружены и следущий большой этап - преобразование и перенос текста
## из общих модулей в модули форм.

#####################################################################################################
# Шаг №1. Вставка символа точки с запятой после инструкции препроцессора #КонецЕсли.
#          Это нужно для дальнейшей успешной загрузки модуля в синтаксический процессор.
#          В сущности инструкции препроцессора не являются инструкциями, поэтому
#          не завершаются точкой с запятой в коде 1С. Но для удобства обработки кода
#          с использованием синтаксического процессора 1Сика они считаются инструкциями,
#          такими же как if .. else .. endif, и поэтому должны оканчиваться точкой с запятой.

def add_semicolon_after_preproc(module_text):
    pos = 0
    while True:
        pos = module_text.find('#КонецЕсли', pos)
        if pos == -1:
            break
        module_text = module_text[0:pos + 10] + '\n;' + module_text[pos + 10:]
        pos += 10 + 3;
    return module_text

for name in gl_form_props:
    gl_form_props[name]['text_origin'] = add_semicolon_after_preproc(gl_form_props[name]['text_origin'])
for name in gl_common_modules_props:
    gl_common_modules_props[name]['text_origin'] = add_semicolon_after_preproc(gl_common_modules_props[name]['text_origin'])

#####################################################################################################
# Шаг №2. Разделение кода общих модулей на две части - для обычного и управляемого приложения.
#          Так же выполняется удаление областей и производится получение структуры модулей (см. parse).

# Cписок вырезаемых из кода областей.
# Все остальные области остануться "как есть" с удаленными обрамлениями областей.
# todo должен параметризоваться
EXCLUDE_AREAS = ["DEBUG", "FILE_OPERATIONS_LOAD", "PRODUCT_UA", "DEBUG_FOR_CONF_DEBUGGING", "TEST"]

# препроцессинг модуля обычного приложения
preproc = preproc1c.Preprocessor1C(gl_app_module["ordinary_app_text_origin"])
gl_app_module["ordinary_app_text"] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS)
gl_app_module["ordinary_app_struct"] = parser1c.parser.parse(gl_app_module["ordinary_app_text"])

# препроцессинг модуля управляемого приложения
preproc = preproc1c.Preprocessor1C(gl_app_module["managed_app_text_origin"])
gl_app_module["managed_app_text"] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS)
gl_app_module["managed_app_struct"] = parser1c.parser.parse(gl_app_module["managed_app_text"])

for name in gl_form_props:
    context = "ТонкийКлиент" if gl_form_props[name]['is_managed'] else "ТолстыйКлиентОбычноеПриложение"
    # Выполнить препроцессинг, избавиться от областей
    preproc = preproc1c.Preprocessor1C(gl_form_props[name]['text_origin'])
    new_text = preproc.execute(context, EXCLUDE_AREAS, ["НаКлиенте"])
    gl_form_props[name]['text'] = new_text
    # Получить синтаксическую структуру модуля
    gl_form_props[name]['struct'] = parser1c.parser.parse(new_text)

if CACHE_MODE_ON and os.path.isfile('gl_common_modules_props.pickle'):
    with open('gl_common_modules_props.pickle', 'rb') as f:
        gl_common_modules_props = pickle.load(f)
else:
    for module_name in gl_common_modules_props:
        # Разрешить препроцессор, избавиться от областей
        preproc = preproc1c.Preprocessor1C(gl_common_modules_props[module_name]['text_origin'])
        try:
            module = gl_common_modules_props[module_name]
            module['text_managed'] = preproc.execute("ТонкийКлиент", EXCLUDE_AREAS, ["НаКлиенте"])
            module['struct_managed'] = parser1c.parser.parse(module['text_managed'])

            module['text_ordinary'] = preproc.execute("ТолстыйКлиентОбычноеПриложение", EXCLUDE_AREAS, ["НаКлиенте"])
            module['struct_ordinary'] = parser1c.parser.parse(module['text_ordinary'])
        except:
            raise Exception("Ошибка при разборе модуля : " + module_name)

    if CACHE_MODE_ON:
        with open('gl_common_modules_props.pickle', 'wb') as f:
            pickle.dump(gl_common_modules_props, f)


######################################################################################################
# Шаг №3. Формирование общего списка процедур и функций во всех общих модулях и модулях форм.
#          В соотвествие имени каждой процедуры/функции ставится её описание типа strct1c.Function.
#          Этот список будет использован в дальнейшем для различных случаев, например,
#          фильтрация системных вызовов от обращений к процедурам и функций общих модулей.
#
#          Пример:
#            'CommonModule.ОбработчикиСобытийФормКлиент.ПриОткрытии': <strct1c.Function object at 0x03520810>
#            'FormManaged.Основная.ПриОткрытии': <strct1c.Function object at 0x03F64C10>

# Содержит общий список всех процедур и функций во всех модулях
gl_all_proc_funcs = dict()

# Заполнение списка процедур и функций для форм
for form_name, form_props in gl_form_props.items():
    # todo сперва для управляемого приложения
    if not form_props['is_managed']:
        continue
    for proc_func in form_props['struct'].proc_func_list:
        key = "FormManaged." + form_name + "." + proc_func.name
        gl_all_proc_funcs[key] = proc_func

# заполнене списка процедур и функций для общих модулей
for module_name, module_props in gl_common_modules_props.items():
    # todo сперва для управляемого приложения
    for proc_func in module_props['struct_managed'].proc_func_list:
        key = "CommonModule." + module_name + "." + proc_func.name
        gl_all_proc_funcs[key] = proc_func

######################################################################################################
# Шаг №4. Формирование списка вызовов для каждой функции каждой формы и модуля.
#          Эти списки будут использованы на следующем этапе для формирования модулей форм.
#          Структура списка следующая:
#            имя_формы.имя_функции: {имя_локальной_функции_формы, .., имя_модуля.имя_функции}
#            имя_модуля.имя_функции: {имя_локальной_функции_модуля, .., имя_модуля.имя_функции}

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

def get_proc_func_call_list(proc_func, module_type, module_name):
    '''
    По переданному описанию функции составляет список вызываемых из неё процедур и функций.
    @param proc_func (strct1c.Function): описание функций
    @param module_type (str): тип модуля: CommonModule, FormManaged, FormOrdinary
    @param module_name (str): имя общего модуля или формы
    @return (set): список вызываемый функций с полным путем к ним: CommonModule.<имя модуля>.<имя процедуры/функции>
    '''
    global gl_all_proc_funcs

    # все функции, в т.ч. встроенные и функции объектов
    func_list = get_statements_call_list(proc_func.body.statements)
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
        if gl_all_proc_funcs.get(full_name, None):
            # в функции может быть несколько обращений к одной и тойже (другой) функции
            val = result.get(full_name, [])
            val.append(func_rec[0])
            result[full_name] = val
    return result

# Содержит список вызовов для каждой процедуры/функции во всех общих модулях и модулях форм
gl_func_calls = dict()

# цикл заполняет gl_func_calls по процедурам и функциями форм
for form_name, from_props in gl_form_props.items():
    if not from_props['is_managed']:
        # todo добавить обработку для обычных форм
        continue
    for proc_func in from_props['struct'].proc_func_list:
        key = "FormManaged." + form_name + "." + proc_func.name
        sub_calls_dict = get_proc_func_call_list(proc_func, "FormManaged", form_name)
        gl_func_calls[key] = sub_calls_dict

# цикл заполняет gl_func_calls по процедурам и функциями общих модулей
for module_name, module_props in gl_common_modules_props.items():
    # todo сперва для управляемого приложения
    for proc_func in module_props['struct_managed'].proc_func_list:
        key = "CommonModule." + module_name + "." + proc_func.name
        sub_calls_dict = get_proc_func_call_list(proc_func, "CommonModule", module_name)
        gl_func_calls[key] = sub_calls_dict

##############################################################################################
# Шаг 5. Формирование списка процедур и функций общих модулей для переноса в основную форму.
#        Этот список состоит из таких пр./ф которые непосредственно учавствуют в цепочке вызова.
#        А так же учавствуют в цепочке вызова косвенно, через вызов инструкции выполнить.
#

# Содержит список функций для переноса в основную форму / модуль
# todo сперва перенос в основную управляемую форму
gl_all_proc_funcs_to_move_primary = set()

def fill_main_module_calls(full_func_name):
    """
    Рекурсивно обходит всё дерево вызовов из переданной full_func_name и добавляет
    каждый вызов в gl_all_proc_funcs_to_move_primary.
    На самом верхнем уровне функция вызывается для каждой процедуры/функции модуля формы.
    Далее вызов продолжается для каждого дочернего вызова и т.д. до последнего вызова.
    @param full_func_name (str): имя процедуры/функции в формате CommonModule.<ИмяМодуля>.<ИмяПроцедурыФункции>
    @return: None
    """
    # объявить переменную как глобальную, т.к. производится модификация
    global gl_all_proc_funcs_to_move_primary

    # получить вызовы из full_func_name
    sub_calls = gl_func_calls.get(full_func_name)

    for func_name in sub_calls:
        if func_name in gl_all_proc_funcs_to_move_primary:
            # если подвызов уже добавлен в функции для переноса - пропускаем, что бы избежать зацикливания
            pass
        else:
            if func_name.split('.')[0] != "FormManaged":
                # не нужно добавлять в список процедуры и функций, которые уже есть в модуле
                gl_all_proc_funcs_to_move_primary.add(func_name)
            fill_main_module_calls(func_name)

for func_name in gl_func_calls:
    parts = func_name.split('.')
    if parts[0] == 'FormManaged' and parts[1].lower() == 'основная':
        fill_main_module_calls(func_name)

###################################################################################################
# Шаг 5а. Некоторые процедуры/функции вызываются особым образом через фукнкции
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

for full_func_name in gl_all_proc_funcs_to_move_primary:
    func_proc_desc = gl_all_proc_funcs[full_func_name]
    parts = full_func_name.split(".")
    sub_call_list = get_proc_func_call_list(func_proc_desc, parts[0], parts[1])
    # todo заменить на обращение к gl_func_calls

    for called_func_name, calls in sub_call_list.items():
        called_func_name_short = called_func_name.split(".")[2]
        if called_func_name_short.lower() in gl_spec_replace_params:
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
    if not full_func_name in gl_all_proc_funcs_to_move_primary:
        gl_all_proc_funcs_to_move_primary.add(full_func_name)
        fill_main_module_calls(full_func_name)

###################################################################################################
# Шаг 6. Формирование списка процедур и функций для переноса во вспомогательные формы.
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
#

# Список процедур и функция для переноса во вспомогательные формы.
#   ключ - имя формы
#   значение - список функций для переноса
gl_all_proc_funcs_to_move_secondary = {}

# Содержит список обращений к функциям, вызовы к которым необходимо заменить на обращение к основной форме:
# Например, вызов
#   System_ОбщегоНазначениеКлиентСервер.СообщитьПользователю(..)
# Будет заменен в итоговой форме на:
#   ОсновнаяФорма.СообщитьПользователю(..)
# Структура переменной:
#   ключ - имя формы
#   значение - имя функции которую следует заменить
gl_replace_calls_to_main_module = {}

def fill_secondary_form_calls(form_name, full_func_name, is_server_chain=False):
    """
    Вычисляет процедуры и функции для переноса во вспомогательную форму.
    При этом, заполняет gl_all_proc_funcs_to_move_secondary - список функций для переноса.
    А так же заполняет gl_replace_calls_to_main_module - список функций для обращения через основной модуль.

    @param form_name (str): имя обрабатываемой формы
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
    if is_server_chain:
        if full_func_name in gl_all_proc_funcs_to_move_secondary[form_name]:
            # если функция уже отмечена к переносу во вспомогательную форму - не продолжаем, что бы не зациклиться
            return
        # для серверной цепочки безусловно переносим процедуру/функцию во вспомогательную форму
        # это важно для клиент-серверных вызовов
        gl_all_proc_funcs_to_move_secondary[form_name].add(full_func_name)
        # безусловно помечаем все последующие вызовы
        new_is_server_chain = is_server_chain
    else:
        # Цепочка вызовов - клиентская, поэтому определяем по контексту и наличию в основной формы, переносить ли её.
        parts = full_func_name.split(".")
        module_props = gl_common_modules_props[parts[1]]
        new_is_server_chain = module_props['is_server']
        if (module_props['is_client'] or module_props['is_client_server']) \
                and full_func_name in gl_all_proc_funcs_to_move_primary:
            # если функция клиентская или клиент-серверная и при этом переносится в основную форму,
            # значит следует переадресовать вызов к основной форме
            if not full_func_name in gl_replace_calls_to_main_module[form_name]:
                gl_replace_calls_to_main_module[form_name].add(full_func_name)
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
        fill_secondary_form_calls(form_name, sub_call, new_is_server_chain)


for full_func_name in gl_func_calls:
    parts = full_func_name.split(".")
    if parts[0] != "FormManaged" or parts[1].lower() == "основная":
        # отбираем только вспомогательные формы
        continue

    is_server_chain = False
    directive = gl_all_proc_funcs[full_func_name].directive.lower()
    if directive == "&насервере" or directive == "&насерверебезконтекста":
        # это "чистый" серверный вызов - все клиент-серверные процедуры
        # и функции необходимо переносить в форму
        is_server_chain = True

    # имя формы, например "FormManaged.Письма"
    form_name = parts[0] + "." + parts[1]

    # инициализция списка для формы в gl_all_proc_funcs_to_move_secondary
    val = gl_all_proc_funcs_to_move_secondary.get(form_name)
    if not val:
        gl_all_proc_funcs_to_move_secondary[form_name] = set()
        gl_replace_calls_to_main_module[form_name] = set()

    for sub_call in gl_func_calls[full_func_name]:
        fill_secondary_form_calls(form_name, sub_call, is_server_chain)

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
# к ном проивзодится обращение через инструкцию Выполнить(..)
# Например:
#   Выполнить("Форма.КакаяТоПроцедура")
for full_func_name in gl_func_to_add_spec:
    gl_main_module_export_functions.add(full_func_name)

###################################################################################################
# Шаг 7. Перенос процедур и функций в основную форму. Перенос осуществляется через добавление
#        в структуру кода основной формы (proc_func_list) процедур и функций отмеченных к переносу,
#        а так же удаление обращений к общим модулям.
#


###################################################################################################
# Шаг 7а. Удаление обращений к общим модулям

def replace_common_module_calls(call_list):
    """
    Выполняет замену обращений к общим модулям на вызовы локальных процедур/функций.
    Например:
        "Subsys_ОбщегоНазначенияКлиентСервер.Проверить(..)" => "Проверить(..)"
    @param call_list (list): список обращений к процедурам и функциям общих модулей для замены
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

# Список процедур и функций основной управляемой формы
main_form_proc_func_list = gl_form_props['Основная']['struct'].proc_func_list

key_managed_main_form = "FormManaged.Основная"
# Удаление обращений из процедур/функций формы (обработчиков)
for func_proc_desc in main_form_proc_func_list:
    full_func_name = key_managed_main_form + "." + func_proc_desc.name
    sub_calls_list = gl_func_calls[full_func_name]
    replace_common_module_calls(sub_calls_list)

#########################################################################################################
# Шан 7б. Перенос в основную форму.
# При переносе функции в форму необходимо добавить директиву.
# Директива зависит от контекста исполнения общего модуля:
#   клиент        - &НаКлиенте
#   сервер        - &НаСервереБезКонтекста
#   клиент-сервер - &НаКлиентеНаСервереБезКонтекста

for full_func_name in gl_all_proc_funcs_to_move_primary:
    # копируем описание функции, что бы не повредить его - может так же использоваться
    # для копирования во второстепенную форму
    func_proc_desc = copy.deepcopy(gl_all_proc_funcs[full_func_name])
    # установка директивы
    parts = full_func_name.split(".")

    if parts[2] == 'ПриОткрытии_Основная':
        a = 1
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

    # собственно эта инструкция и выполняет перенос ;)
    main_form_proc_func_list.append(func_proc_desc)

    # Важно! Снова получаем список вызовов процедур и функций на основе нового описания функции.
    # Это нужно для того что бы заменить обращения к общим модулям на локальные вызовы
    # и при этом не трогать старое описание.
    sub_call_list = get_proc_func_call_list(func_proc_desc, parts[0], parts[1])

    # заменяем обращения к общим модулям на обращение к локальным функциям
    replace_common_module_calls(sub_call_list)

    # Шаг 7в.  Если среди обращений к функциям есть специальные -
    # ПолучитьОписаниеОповещенияСВызовомФункции, СоздатьОбъектОписанияОповещения
    # то подменяем параметры на сборочные.
    for called_func_name, calls in sub_call_list.items():
        called_func_name_short = called_func_name.split(".")[2]
        if called_func_name_short.lower() in gl_spec_replace_params:
            for call in calls:
                if isinstance(call, strct1c.FuncCall):
                    call.param_list[1] = strct1c.Identifier('ЭтаФорма')
                else:
                    call.properties_list[0].param_list[1] = strct1c.Identifier('ЭтаФорма')

#########################################################################################################
# Шаг 7г. Замена ссылок на некоторые глобальные переменные на обращения особого вида
#         Например, гл_Subsys_ИмяФайлаОбработки => Объект.КэшДанных.ИмяОбработки
#

# todo соотвествие для замен брать из файла настроек
replacements = {"гл_iBank2_ИмяФайлаОбработки": "Объект.КэшДанных.ИмяОбработки",
                "гл_iBank2_РежимРаботы": "Объект.КэшДанных.РежимРаботы"}

replacements = { key.lower(): val for key, val in replacements.items()}
filter={x for x in replacements}

id_call_list = []
for func_proc_desc in main_form_proc_func_list:
    id_call_list += get_statements_call_list(func_proc_desc.body.statements, obj_type="id", filter=filter)

for rec in id_call_list:
    id_name = rec[1]
    if id_name.lower() in replacements and isinstance(rec[0], strct1c.Identifier):
        rec[0].id = replacements[id_name.lower()]

########################################################################################################
# Шаг 7д. Перенос в модуль основной формы глобальных переменных.

for gl_var_desc in gl_app_module["managed_app_struct"].global_vars:
    if PROCESSOR_NAME.lower() in gl_var_desc.vars_list[0].name.lower():
        gl_var_desc_new = copy.deepcopy(gl_var_desc)
        gl_var_desc_new.directive = "&НаКлиенте"
        gl_form_props['Основная']['struct'].global_vars.append(gl_var_desc_new)

main_form_text = strct1c.get_text(gl_form_props['Основная']['struct'])

##############################################################################################
# Перенос во вспомогательную основную форму.
# При переносе функций во вспомогательную форму необходимо удалить признак экспортной функции.
# gl_all_proc_funcs_to_move_secondary
# gl_replace_calls_to_main_module

# Во вспомогательных управляемых формах
# а) добавить переменную модуля формы ОсновнаяФорма
# б) в обработчик ПриОткрытии (должен быть добавлен во все формы) добавить вызов ОсновнаяФорма = ПолучитьОсновнуюФорму() (вместо ПолучитьОсновногоВладельцаФормы)
# в) во обращениях к основной форме вместо ПолучитьОсновногоВладельцаФормы() использовать ОсновнаяФорма

pass
