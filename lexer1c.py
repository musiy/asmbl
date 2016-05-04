# ------------------------------------------------------------
# calclex.py
#
# tokenizer for a simple expression evaluator for
# numbers and +,-,*,/
# ------------------------------------------------------------
import ply.lex as lex

# reserved words

reserved = {
    '#если' :    'DEF_IF',
    '#тогда':    'DEF_THEN',
    '#иначе':    'DEF_ELSE',
    '#конецесли':'DEF_ENDIF',
    'если' :     'IF',
    'тогда':     'THEN',
    'иначе':     'ELSE',
    'конецесли': 'ENDIF',
    'для':       'FOR',
    'по':        'TO',
    'пока':      'WHILE',
    'цикл':      'DO',
    'конеццикла':'ENDDO'
}

# List of token names.   This is always required
tokens = [
   'STRING',
   'NUMBER',
   'LSB',
   'RSB',
   'AMRSND',
   'EQ',
   'PLUS',
   'MINUS',
   'TIMES',
   'DIVIDE',
   'COMA',
   'SEMICOLON',
   'DOT',
   'LPAREN',
   'RPAREN',
   'ID'] + list(reserved.values())

# Regular expression rules for simple tokens
t_STRING    = r'["].*["]'
t_LSB       = r'\['
t_RSB       = r'\]'
t_AMRSND    = r'\&'
t_EQ        = r'='
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_COMA      = r','
t_SEMICOLON = r';'
t_DOT       = r'\.'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'

# identificator
def t_ID(t):
    r'[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')
    return t

# A regular expression rule with some action code
def t_NUMBER(t):
    r'\d+' # function documentation string
    t.value = int(t.value)    
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

data = """
&НаКлиенте
Функция ПростоТак(Знач Перем1 = "", Перем2 = Неопределено)
    Если 1 = 1 Тогда
        перем_1 = (3 + 5) * 7 - 9;
        #Если ВебКлиент Тогда
            перем_3 = ОбщийМодуль.ФункцияДелающаяЧтоТо(1, 2, 3);
        #Иначе
            перем_3 = НСтр("ru = 'Добрый вечер!'; en = 'Good Evening!'"));
        #КонецЕсли
    КонецЕсли;
    Возврат перем_1;
КонецФункции

&НаСервере
Процедура СервернаяПроцедура(Количество)
    ЭтаФорма.Элементы["СтрокаПростая"] = "Виг вам";
КонецПроцедуры

"""
print (data)

lexer.input(data)

for lextoken in lexer:
    print(lextoken)
