# ------------------------------------------------------------
# lexer1c.py
#
# tokenizer for a 1C:Enterprise embedded language "1C"
# ------------------------------------------------------------
import ply.lex as lex
import re
import imp
import sys
#imp.reload(sys)
#sys.setdefaultencoding('utf-8')

# reserved words
reserved = {
    '#если'             : 'DEF_IF',
    '#тогда'            : 'DEF_THEN',
    '#иначеесли'        : 'DEF_ELSE_IF',
    '#иначе'            : 'DEF_ELSE',
    '#конецесли'        : 'DEF_ENDIF',
    '#область'          : 'AREA',
    '#конецобласти'     : 'AREA_END',
    'если'              : 'IF',
    'тогда'             : 'THEN',
    'иначе'             : 'ELSE',
    'конецесли'         : 'ENDIF',
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
    'вызватьисключение' : 'RAISE'
}

# List of token names. This is always required.
tokens = [
   'STRING',
   'NUMBER',

   'LSB',       # [
   'RSB',       # ]
   'QSTN',      # ?
   'AMRSND',    # &
   'EQ',        # =
   'NOTEQ',     # <>
   'LESS',      # <
   'MORE',      # >
   'PLUS',      # +
   'MINUS',     # -
   'TIMES',     # *
   'DIVIDE',    # /
   'PERCENT',   # %
   'COMMA',     # ,
   'SEMI',      # ;
   'DOT',       # .
   'COLON',     # :
   'LPAREN',    # (
   'RPAREN',    # )

   'ID', 
   'FOR_EACH',
   'PREPROCID',
   'COMMENT',
   'DIRECTIVE',
   'LABEL'] + list(reserved.values())

# Regular expression rules for simple tokens
t_STRING    = r'"(?:[^"]|"")*"'
t_DIRECTIVE = r'&[a-zA-Zа-яА-Я]*'
t_LABEL     = r'~[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
t_LSB       = r'\['
t_RSB       = r'\]'
t_QSTN      = r'\?'
t_AMRSND    = r'\&'
t_EQ        = r'='
t_NOTEQ     = r'\<\>'
t_LESS      = r'\<'
t_MORE      = r'\>'
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_PERCENT   = r'%'
t_COMMA     = r','
t_SEMI      = r';'
t_DOT       = r'\.'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_COLON     = r':'

# comment
def t_COMMENT(t):
    r'\/\/.*\n'
    pass # just pass comment

# preprocessor instructions
def t_PREPROCID(t):
    r'\#[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
    t.type = reserved.get(t.value.lower(), 'unknown preprocessor instruction: ' + t.value)
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

# Build the lexer
lexer = lex.lex(reflags=re.I)

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    lexer.input(data)
    for lextoken in lexer:
        print(lextoken)
