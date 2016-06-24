# -*- coding: utf-8 -*-

class Preprocessor1C:
    '''
    Выполняет вычисление и удаление инструкций препроцессора, а так же областей в коде 1С.
    '''

    # Код модуля 1С для обработки
    text = ""

    def __init__(self, text):
        self.text = text
        pass

    def execute(self, mode, areas_to_delete = [], symbols_to_retain = []):
        '''
        Обработать модуль.

        @param areas_to_delete: см. подробности в remove_areas
        @param symbols_to_retain: см. подробности в remove_preproc
        @return (str): модуль без областей, обработанный препроцессором
        '''
        self.text = self.remove_areas(areas_to_delete)
        self.text = self.do_preproc(mode, symbols_to_retain)
        return self.text

    def remove_areas(self, areas_to_delete):
        '''
        Выполняет удаление инструкций с указанием областей.
        Так же удаляет содержимое областей, указанных в areas_to_delete.

        @param areas_to_delete (list): список из строк - названий областей, которые необходимо вырезать из кода 1С
        @return (str): модуль, из которого были извлечены инструкции с указанием областей
        '''

        AREA_BEGIN = "#область"
        AREA_END = "#конецобласти"

        def codeline_is_area_begin(line):
            return line.lstrip()[:len(AREA_BEGIN)].lower() == AREA_BEGIN or line.lstrip()[1:len(AREA_BEGIN)+1].lower() == AREA_BEGIN

        def codeline_is_area_end(line):
            return line.strip().lower() == AREA_END

        def codeline_area_name(line):
            return line.lstrip()[len(AREA_BEGIN):].strip().lower()

        # перевод в нижний регистр
        areas_to_delete = {x.lower() for x in areas_to_delete}

        text_lines = self.text.split('\n')
        index = 0
        new_text = ""

        while index < len(text_lines):
            line = text_lines[index]
            index += 1
            if codeline_is_area_begin(line): # если это начало области
                area_name = codeline_area_name(line)
                if area_name in areas_to_delete: # пропускаем весь контент внутри области
                    area_level = 1 # вошли область
                    while area_level > 0:
                        line = text_lines[index]
                        if codeline_is_area_begin(line):
                            area_level += 1
                        elif codeline_is_area_end(line):
                            area_level -= 1
                        index += 1
                continue
            elif codeline_is_area_end(line):
                continue
            new_text += line + '\n'

        return new_text

    def do_preproc(self, mode, symbols_to_retain):
        """
        Вызывается для выполнения препроцессинга над кодом
        @param mode: контекст исполнения кода 1С, возможные варианты:
                      - ТолстыйКлиентОбычноеПриложение
                      - ТонкийКлиент
                      ..

        @param excluded_symbols: символы препроцессора исключаемые из анализа.
                      Примечание: исключаются из анализа если в условии препроцессора
                                  использованы символы из списка, иначе препроцессор
                                  по прежнему выполняетя

        @return:
        """

        def is_client(symbol):
            """Клиент|Client"""
            return symbol.lower().find('клиент') != -1 or symbol.lower().find('client')

        def is_server(symbol):
            """Сервер|Server"""
            return symbol.lower().find('сервер') != -1 or symbol.lower().find('server')

        def is_external_connection(symbol):
            """ВнешнееСоединение|ExternalConnection"""
            raise Exception("Не поддерживается")

        def is_at_client(symbol):
            """НаКлиенте|AtClient"""
            return is_client(symbol)

        def is_at_server(symbol):
            """НаСервере|AtServer"""
            return is_server(symbol)

        def is_mobile_app_client(symbol):
            """МобильноеПриложениеКлиент|MobileAppClient"""
            return symbol.lower() == "мобильноеприложениеклиент" or symbol.lower() == "mobileappclient"

        def is_mobile_app_server(symbol):
            """МобильноеПриложениеСервер|MobileAppServer"""
            return symbol.lower() == "мобильноеприложениесервер" or symbol.lower() == "mobileappserver"

        def is_thick_client_ordinary_application(symbol):
            """ТолстыйКлиентОбычноеПриложение|ThickClientOrdinaryApplication"""
            return symbol.lower() == "толстыйклиентобычноеприложение" or symbol.lower() == "thickclientordinaryapplication"

        def is_thick_client_managed_application(symbol):
            """ТолстыйКлиентУправляемоеПриложение|ThickClientManagedApplication"""
            return symbol.lower() == "толстыйклиентуправляемоеприложение" or symbol.lower() == "thickclientmanagedapplication"

        def is_thin_client(symbol):
            """ТонкийКлиент|ThinClient"""
            return symbol.lower() == "тонкийклиент" or symbol.lower() == "thinclient"

        def is_web_client(symbol):
            """ВебКлиент|WebClient"""
            return symbol.lower() == "вебклиент" or symbol.lower() == "webclient"

        ## Этап №1. Формирование соотвествия имени символа препроцессора функции, которая
        ##           вычислит его значение для текущего режима.

        func_list = [func_name for func_name in dir() if func_name[:3]=="is_"]
        symcalc_ru = {}
        symcalc_en = {}

        for func_name in func_list:
            func_desc_list = eval(func_name + ".__doc__").split("|")
            symname_ru = func_desc_list[0]
            symname_en = func_desc_list[1]
            symcalc_ru[symname_ru.lower()] = eval(func_name)
            symcalc_en[symname_en.lower()] = eval(func_name)

        ## Этап №2. Проход по коду, вычисление препроцессора

        def check_begin_with(line, keyword):
            """
            Проверяет, что строка кода начинается с ключевого слова keyword.
            Пробельные символы в начале строки пропускаются.
            """
            return line.lstrip()[:len(keyword)].lower() == keyword.lower()

        def preproc_if(line):
            return check_begin_with(line, "#Если")

        def preproc_elseif(line):
            return check_begin_with(line, "#ИначеЕсли")

        def preproc_else(line):
            return check_begin_with(line, "#Иначе")

        def preproc_endif(line):
            return check_begin_with(line, "#КонецЕсли")

        def preproc_line(line):
            return preproc_if(line) or preproc_elseif(line) or preproc_else(line) or preproc_endif(line)

        def codeline_condition_text(line):
            """
            Выделяет текст условия препроцессора.
            @param line (str): текущая строка пропроцессора в коде модуля.
                               Пример:
                                    #Если НЕ ТонкийКлиент И НЕ ТолстыйКлиентОбычноеПриложение Тогда
            @return: выделенное условие, ответ для приведенного примера:
                                    НЕ ТонкийКлиент И НЕ ТолстыйКлиентОбычноеПриложение
            """
            line = line.lstrip().lower()
            pos_begin = line.find(" ") # первый пробельный символ идёт перед условием препроцессора
            pos_end = line.find("тогда")  # первый пробельный символ идёт перед условием препроцессора
            if pos_begin == -1 or pos_end == -1:
                raise Exception("Не верная инструкция препроцессора: " + line)
            return line[pos_begin:pos_end]

        def get_expr_tokens(condition):
            """
            Разбирает условие препроцессора на токены.
            @param condition: условие препроцессора для разбора на токены
            @return: список токенов
            """
            tokens = []
            curr_token = ""
            pos = 0
            while pos < len(condition):
                sym = condition[pos]
                if sym == ' ' or sym == '\t' or sym == '(' or sym == ')':
                    if curr_token:
                        tokens.append(curr_token)
                        curr_token = ""
                    if sym == '(' or sym == ')':
                        tokens.append(sym)
                elif sym.isalpha():
                    curr_token += sym
                pos += 1
            tokens = [x.lower() for x in tokens]
            return tokens

        def check_define_should_be_retained(tokens):
            """
            Проверяет, что все все перечисленные токены содержаться в symbols_to_retain.
            Если так, то необходимо оставить условие "как есть" и возвратить весь текст включая препроцессор.
            @param tokens (list): токены из условия препроцессора
            @return (bool): True - условие необходимо сохранить, Иначе False
            """
            nonlocal symbols_to_retain
            retain = True
            symbols_to_retain = {x.lower() for x in symbols_to_retain}

            for token in tokens:
                if token in {"не", "и", "или", "(", ")"}:
                    pass
                elif not token in symbols_to_retain:
                    retain = False
                    break
            return retain

        def eval_cond(tokens):
            """
            Пересобирает логическое выражение в терминах python и вычисляет его через eval.
            @param tokens:
            @return:
            """

            nonlocal symcalc_ru
            nonlocal symcalc_en

            expr = ""
            for token in tokens:
                if token == "не":
                    expr += "not"
                elif token == "и":
                    expr += "and"
                elif token == "или":
                    expr += "or"
                elif token in {"(", ")"}:
                    expr += token
                else:
                    result = symcalc_ru[token](mode)
                    expr += "True" if result else "False"
                expr += " "
            return eval(expr)


        def preproc_block():
            """
            Вычисляет блок препроцессора и возвращает участок кода.
                #Если <условие препроцессора> Тогда
                    ..
                #ИначеЕсли <условие препроцессора> Тогда
                    ..
                #Иначе
                    ..
                #КонецЕсли

            @param text_lines (list): строки кода
            @param index (int): текущий индекс
            @return (str): участок кода (строка)
            """

            nonlocal text_lines
            nonlocal index
            nonlocal mode
            nonlocal symbols_to_retain

            new_text = ""

            # Признак, что какой то из блоков инструкции препроцессора уже был выбран.
            # Используется для того что бы пропустить остальные блоки условий.
            # Если не выбрано ни одно условие, выбирается блок #Иначе (если присутствует).
            already_chosen = False

            # Признак того, что весь блок #Если .. #КонецЕсли нужно оставить "как есть"
            # Это может потребоваться для парсера 1С, который будет считатать инструкции
            # препроцессора "обычными" инструкциями.
            retain = False

            # Цикл по блокам препроцессора на одном уровне
            # Начало цикла это одна из возможных строк препроцессора:
            #   #Если .. Тогда
            #   #ИначеЕсли .. Тогда
            #   #Иначе ..
            #   КонецЕсли
            while not preproc_endif(text_lines[index]):

                if preproc_else(text_lines[index]):
                    # спец. блок, что бы не разбирать условие
                    if not already_chosen:
                        choose_block = True
                else:
                    # Получить условие препроцессора
                    cond = codeline_condition_text(text_lines[index])
                    # Разбить условие препроцессора на токены
                    tokens = get_expr_tokens(cond)
                    choose_block = eval_cond(tokens)

                    # Проверить, что условие необходимо оставить "как есть", без удаления
                    if preproc_if(text_lines[index]):
                        retain = check_define_should_be_retained(tokens)

                if retain:
                    new_text += text_lines[index] + '\n'

                if (not already_chosen and choose_block) or retain:
                    already_chosen = True
                    while True:
                        index += 1
                        line = text_lines[index]
                        if preproc_if(line):
                            # Начало нового условия препроцессора.
                            # Вызываем функцию рекурсивно для расчёта внутреннего блока.
                            new_text += preproc_block() + '\n'
                        elif preproc_line(line):
                            break
                        else:
                            new_text += line + '\n'
                else:
                    # Пропускаем простые строки внутренние блоки препроцессора до
                    # тех пор пока не встретится "#ИначеЕсли" или "#Иначе" или "#КонецЕсли"
                    # на текущем уровне препроцессора.
                    level = 1
                    while True:
                        index += 1
                        line = text_lines[index]
                        if preproc_if(line):
                            level += 1
                        if preproc_endif(line):
                            level -= 1
                        if level == 0 or (level == 1 and (preproc_elseif(line) or preproc_else(line))):
                            break

            if retain:
                new_text += text_lines[index] + '\n'

            index += 1
            return new_text

        text_lines = self.text.split('\n')
        index = 0
        new_text = ""

        while index < len(text_lines):
            line = text_lines[index]
            if preproc_if(line):
                new_text += preproc_block()
            else:
                new_text += line + '\n'
                index += 1
        return new_text

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    proc = Preprocessor1C(data)
    new_text = proc.execute("ТолстыйКлиентОбычноеПриложение", ["DEBUG"], ["НаКлиенте"])
    print(new_text)
    pass
