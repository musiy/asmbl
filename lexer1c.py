# -*- coding: utf-8 -*-

# ------------------------------------------------------------
# lexer1c.py
#
# tokenizer for a 1C:Enterprise embedded language "1C"
# ------------------------------------------------------------
import ply.lex as lex
import re
import sys

# Areas in 1C code to delete while lexing
areas_to_delete = set()
areas_to_delete.add('удалитьэтуобласть')
areas_deletion_in_process = False

states = (
   ('compstring','exclusive'),
)

# reserved words
reserved = {
    '#если'             : 'DEF_IF',
    '#иначеесли'        : 'DEF_ELSE_IF',
    '#иначе'            : 'DEF_ELSE',
    '#конецесли'        : 'DEF_END_IF',
    '#область'          : 'AREA_BEGIN',
    '#конецобласти'     : 'AREA_END',
    'если'              : 'IF',
    'тогда'             : 'THEN',
    'иначеесли'         : 'ELSE_IF',
    'иначе'             : 'ELSE',
    'конецесли'         : 'END_IF',
    'для'               : 'FOR',
    'по'                : 'TO',
    'из'                : 'FROM',
    'пока'              : 'WHILE',
    'цикл'              : 'DO',
    'конеццикла'        : 'END_DO',
    'продолжить'        : 'CONTINUE',
    'прервать'          : 'BREAK',
    'функция'           : 'FUNCTION',
    'конецфункции'      : 'END_FUNCTION',
    'процедура'         : 'PROCEDURE',
    'конецпроцедуры'    : 'END_PROCEDURE',
    'перейти'           : 'GOTO',
    'неопределено'      : 'UNDEFINED',
    'знач'              : 'VAL',
    'перем'             : 'VAR',
    'экспорт'           : 'EXPORT',
    'истина'            : 'TRUE',
    'ложь'              : 'FALSE',
    'не'                : 'NOT',
    'и'                 : 'AND',
    'или'               : 'OR',
    'новый'             : 'NEW',
    'попытка'           : 'TRY',
    'исключение'        : 'EXCEPTION',
    'конецпопытки'      : 'END_TRY',
    'вызватьисключение' : 'RAISE',
    'возврат'           : 'RETURN'
}

# List of token names. This is always required.
tokens = [
   'STRING',
   'NUMBER',
   'DATE',

   'LSB',       # [
   'RSB',       # ]
   'QSTN',      # ?
   'EQ',        # =
   'NOT_EQ',    # <>
   'LT',        # <
   'LE',        # <=
   'GT',        # >
   'GE',        # >=
   'PLUS',      # +
   'MINUS',     # -
   'TIMES',     # *
   'DIVIDE',    # /
   'MOD',       # %
   'COMMA',     # ,
   'SEMI',      # ;
   'DOT',       # .
   'COLON',     # :
   'LPAREN',    # (
   'RPAREN',    # )

   'ID', 
   'FOR_EACH',
   'DIRECTIVE',
   'LABEL'] + list(reserved.values())

# Regular expression rules for simple tokens
t_STRING    = r'"(?:[^"]|"")*"'
t_DATE      = r'\'(\d|-)+\''
t_DIRECTIVE = r'&[a-zA-Zа-яА-Я]*'
t_LABEL     = r'~[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
t_LSB       = r'\['
t_RSB       = r'\]'
t_QSTN      = r'\?'
t_EQ        = r'='
t_NOT_EQ    = r'\<\>'
t_LT        = r'\<'
t_LE        = r'\<='
t_GT        = r'\>'
t_GE        = r'\>='
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_MOD       = r'%'
t_COMMA     = r','
t_SEMI      = r';'
t_DOT       = r'\.'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_COLON     = r':'


def t_areas(t):
    r'\#(область|конецобласти)'
    global areas_deletion_in_process
    if areas_deletion_in_process:
        if t.value.lower() == '#область':
            t.type = 'AREA_BEGIN'
        else:
            t.type = 'AREA_END'
        return t
    if t.value.lower() == '#область':
        token = t.lexer.token()
        if token.value.lower() in areas_to_delete:
            areas_deletion_in_process = True
            area_level = 1
            while token.type != 'AREA_END' or area_level > 0:
                token = t.lexer.token()
                if token.type == 'AREA_BEGIN':
                    area_level +=1
                elif token.type == 'AREA_END' and area_level > 0:
                    area_level -= 1
            areas_deletion_in_process = False
    pass


def t_preprocessor(t):
    r'\#[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
    t.type = reserved.get(t.value.lower(), 'invalid preprocessor instruction: ' + t.value)
    return t

# double identificator
def t_FOR_EACH(t):
    r'для[\s]*каждого'
    t.type  = 'FOR_EACH'
    t.value = 'Для Каждого'
    return t

# identificator
def t_ID(t):
    r'[a-zA-Zа-яА-Я_][a-zA-Zа-яЁёА-Я_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')
    return t

# A regular expression rule with some action code
def t_NUMBER(t):
    r'\d+\.\d+|\d+'
    t.value = t.value
    return t

# comment
def t_comment(t):
    r'\/\/.*'
    pass

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\ufeff'

# Error handling rule
def t_error(t):
    print("== Illegal character: %s" % str(t))
    t.lexer.skip(1)

## string state processing

def t_compstring(t):
    '\"'
    t.lexer.begin('compstring')
    t.value = ""
    while lexer.lexstate == 'compstring':
        curr = t.lexer.next()
        t.value += curr.value
    t.type = 'STRING'
    return t

def t_compstring_next_block_type(t):
    r'[^"\n]{1,}'
    t.type = 'STRING'
    while (t.lexer.lexdata[t.lexer.lexpos] == '"'):
        if (t.lexer.lexdata[t.lexer.lexpos+1] == '"'):
            t.lexer.lexpos += 2
            t.value += '"'
        else:
            t.lexer.lexpos += 1
            t.lexer.begin('INITIAL')
            break
    return t

def t_compstring_quotes(t):
    r'\"'
    t.type = 'STRING'
    if t.lexer.lexpos == t.lexer.lexlen or t.lexer.lexdata[t.lexer.lexpos] != '"':
        t.lexer.begin('INITIAL')
        t.value = ""
    else:
        t.lexer.lexpos += 1
        t.value = '"'
    return t

def t_compstring_newline(t):
    r'\n\s*\|'
    for ch in t.value:
        if ch == "\n":
            t.lexer.lineno += 1
    t.value = "\n"
    t.type = "STRING"
    return t

def t_compstring_newline_withcomment(t):
    r'\n\s*\/\/.*'
    for ch in t.value:
        if ch == "\n":
            t.lexer.lineno += 1
    pass

t_compstring_ignore  = ''

def t_compstring_error(t):
    print("== string state processing error: %s" % str(t))
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex(reflags=re.I)

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    lexer.input(data)
    for lextoken in lexer:
        print(lextoken, lexer.lexstate)
