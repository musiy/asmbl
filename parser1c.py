import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from lexer1c import tokens


## function & procedure declaration

def p_func_declaration_1(p):
    '''function_decl : function_head func_body END_FUNCTION
                     | function_head END_FUNCTION'''
    pass


def p_func_head_1(p):
    '''function_head : DIRECTIVE FUNCTION ID params_decl
                     | DIRECTIVE FUNCTION ID params_decl EXPORT
                     | FUNCTION ID params_decl
                     | FUNCTION ID params_decl EXPORT'''
    pass


def p_func_params_1(p):
    '''params_decl : LPAREN RPAREN'''
    pass


def p_params_decl(p):
    '''params_decl : LPAREN declarator_list RPAREN'''
    pass


def p_init_declarator_list_1(t):
    '''declarator_list : init_declarator'''
    pass


def p_init_declarator_list_2(t):
    '''declarator_list : declarator_list COMMA init_declarator'''
    pass


def p_init_declarator_1(t):
    '''init_declarator : declarator'''
    pass


def p_init_declarator_2(t):
    '''init_declarator : declarator EQ initializer'''
    pass


def p_declarator_1(t):
    '''declarator : VAL param_name'''
    pass


def p_declarator_2(t):
    '''declarator : param_name'''
    pass


def p_initializer(t):
    '''initializer : STRING
                   | NUMBER
                   | UNDEFINED
    '''
    pass


def p_param_name(p):
    '''param_name : ID'''
    pass


def p_func_body_1(p):
    '''func_body : perem_decl_list statements_list'''
    pass


def p_func_body_2(p):
    '''func_body : perem_decl_list
                 | statements_list'''
    pass


def p_perem_decl_list_1(p):
    '''perem_decl_list : perem_decl_list perem_decl'''
    pass


def p_perem_decl_list_2(p):
    '''perem_decl_list : perem_decl'''
    pass


def p_perem_decl(p):
    '''perem_decl : VAR ID SEMI'''
    pass


def p_statements_list_1(p):
    '''statements_list : statements_list SEMI'''
    pass


def p_statements_list_2(p):
    '''statements_list : SEMI'''
    pass

## -- BEGIN EXPRESSION --

# def p_expression_plus(p):
#     'expression : expression PLUS term'
#     pass
#
#
# def p_expression_minus(p):
#     'expression : expression MINUS term'
#     pass
#
#
# def p_term_times(p):
#     'term : term TIMES factor'
#     pass
#
#
# def p_term_div(p):
#     'term : term DIVIDE factor'
#     pass
#
#
# def p_factor_num(p):
#     '''operand : NUMBER'''
#     pass
#
#
# def p_factor_expr(p):
#     'factor : LPAREN expression RPAREN'
#     pass


## -- END EXPRESSION --


# def p_statement_1(p):
#     '''statement : preproc_block
#                  | area_block
#                  | for_each_block
#                  | for_block
#                  | while_block
#                  | if_block
#                  | SEMI
#                  '''
#     pass
#
# def p_statement_2(p):
#     '''statement : lvalue = rvalue SEMI'''
#     pass
#
# def p_statement_3(p):
#     '''statement : rvalue SEMI'''
#     pass
#
# def p_lvalue(p):
#     ''''''
#     pass


# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc()

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    result = parser.parse(data)
    print(result)
