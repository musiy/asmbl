# ------------------------------------------------------------
# lexer1c.py
#
# tokenizer for a 1C:Eterprise embedded language "1C"
# ------------------------------------------------------------
import ply.lex as lex

# reserved words

reserved = {
    '#если'         : 'DEF_IF',
    '#тогда'        : 'DEF_THEN',
    '#иначе'        : 'DEF_ELSE',
    '#конецесли'    : 'DEF_ENDIF',
    'если'          : 'IF',
    'тогда'         : 'THEN',
    'иначе'         : 'ELSE',
    'конецесли'     : 'ENDIF',
    'для'           : 'FOR',
    'по'            : 'TO',
    'пока'          : 'WHILE',
    'цикл'          : 'DO',
    'конеццикла'    : 'ENDDO',
    'функция'       : 'FUNCTION',
    'конецфункции'  : 'ENDFUNCTION',
    'процедура'     : 'PROCEDURE',
    'конецпроцедуры': 'ENDPROCEDURE',
    'неопределено'  : 'UNDEFINED',
    'перем'         : 'PEREM',
    'экспорт'       : 'EXPORT'
}

# List of token names. This is always required.
tokens = [
   'STRING',
   'NUMBER',

   'LSB',       # [
   'RSB',       # ]
   'AMRSND',    # &
   'EQ',        # =
   'PLUS',      # +
   'MINUS',     # -
   'TIMES',     # *
   'DIVIDE',    # /
   'COMMA',     # ,
   'SEMICOLON', # ;
   'DOT',       # .
   'LPAREN',    # (
   'RPAREN',    # )

   'ID', 
   'PREPROCID',
   'COMMENT',
   'DIRECTIVE'] + list(reserved.values())

# Regular expression rules for simple tokens
t_STRING    = r'"(?:[^"]|"")*"'
t_DIRECTIVE = r'&[a-zA-Zа-яА-Я]*'
t_LSB       = r'\['
t_RSB       = r'\]'
t_AMRSND    = r'\&'
t_EQ        = r'='
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_COMMA     = r','
t_SEMICOLON = r';'
t_DOT       = r'\.'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_COMMENT   = r'\/\/.*\n'

# preprocessor instructions
def t_PREPROCID(t):
    r'\#[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
    t.type = reserved.get(t.value.lower(), 'unknown preprocessor instruction: ' + t.value)
    return t

# identificator
def t_ID(t):
    r'[a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')
    return t

# A regular expression rule with some action code
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)    
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
lexer = lex.lex()

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    lexer.input(data)
    for lextoken in lexer:
        print(lextoken)
