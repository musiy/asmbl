import ply.yacc as yacc
from lexer1c import tokens

precedence = (
               ('left', 'PLUS','MINUS'),
               ('left', 'TIMES','DIVIDE'),
               ('left', 'MOD')
)

## -- begin function & procedure declaration --

def p_func_decl_1(p):
    '''func_decl : DIRECTIVE FUNCTION ID LPAREN declarator_list RPAREN func_body END_FUNCTION'''
    pass

def p_func_decl_2(p):
    '''func_decl : DIRECTIVE FUNCTION ID LPAREN declarator_list RPAREN EXPORT func_body END_FUNCTION'''
    pass

def p_func_decl_3(p):
    '''func_decl : FUNCTION ID LPAREN declarator_list RPAREN func_body END_FUNCTION'''
    pass

def p_func_decl_4(p):
    '''func_decl : FUNCTION ID LPAREN declarator_list RPAREN EXPORT func_body END_FUNCTION'''
    pass

def p_init_declarator_list_1(t):
    '''declarator_list : declarator_list COMMA init_declarator'''
    pass

def p_init_declarator_list_2(t):
    '''declarator_list : init_declarator'''
    pass

def p_init_declarator_list_3(t):
    '''declarator_list : '''
    pass

def p_init_declarator_1(t):
    '''init_declarator : ID'''
    pass

def p_init_declarator_2(t):
    '''init_declarator : VAL ID'''
    pass

def p_init_declarator_3(t):
    '''init_declarator : ID EQ func_param_initializer'''
    pass

def p_init_declarator_4(t):
    '''init_declarator : VAL ID EQ func_param_initializer'''
    pass

def p_initializer(t):
    '''func_param_initializer : bool
                              | STRING
                              | NUMBER
                              | DATE
                              | UNDEFINED'''
    pass

def p_bool(p):
    '''bool : TRUE
            | FALSE'''
    pass

## -- end function & procedure declaration --

## -- begin function & procedure body --

def p_func_body_1(p):
    '''func_body : vars_decls_list semi statements_list'''
    pass

def p_func_body_2(p):
    '''func_body : vars_decls_list semi statements_list semi'''
    pass
def p_func_body_3(p):
    '''func_body : vars_decls_list
                 | vars_decls_list semi
                 | statements_list'''
    pass

def p_perem_decl_list_1(p):
    '''vars_decls_list : vars_decls_list SEMI VAR vars_list'''
    pass

def p_perem_decl_list_2(p):
    '''vars_decls_list : VAR vars_list'''
    pass


def p_perems_list_1(p):
    '''vars_list : vars_list COMMA ID'''

def p_perems_list_2(p):
    '''vars_list : ID'''

## statements_list

def p_statements_list_1(p):
    '''statements_list : statements_list semi statement'''
    pass

def p_statements_list_2(p):
    '''statements_list : statement'''
    pass

## -- end function & procedure body --

def p_statement_2(p):
    '''statement : variable EQ NUMBER'''
    pass

def p_semi_1(p):
    '''semi : semi SEMI'''
    pass

def p_semi_2(p):
    '''semi : SEMI'''
    pass

## -- BEGIN VARIABLE --
## TODO

def p_var_1(p):
    '''variable : ID'''
    pass

def p_var_2(p):
    '''variable : ID square_brackets_list'''
    pass

def p_square_brackets_list_1(p):
   '''square_brackets_list : square_brackets_list LSB expr RSB'''
   pass

def p_square_brackets_list_2(p):
    '''square_brackets_list : LSB expr RSB'''
    pass

def p_expr_simple(p):
    '''expr : bool
            | NUMBER
            | STRING
            | UNDEFINED
            | ID'''
    pass

# def p_properties_list_1(p):
#    '''properties_list : properties_list DOT variable'''
#    pass
#
# def p_properties_list_2(p):
#    '''properties_list : DOT variable'''
#    pass

## -- END VARIABLE --

## -- BEGIN EXPRESSION --

# def p_expr_binary(p):
#     '''expr : expr PLUS expr
#             | expr MINUS expr
#             | expr TIMES expr
#             | expr DIVIDE expr
#             | expr MOD expr'''
#     pass

# def p_expr_simple(p):
#     '''expr : bool
#             | NUMBER
#             | STRING
#             | UNDEFINED
#             | ID'''
#             #| func_call'''
#     pass

# def p_expr_group(p):
#     '''expr : LPAREN expr RPAREN'''
#     pass
#
# ## -- END EXPRESSION --
#
# def p_func_call(p):
#     '''func_call : ID LPAREN params_list RPAREN'''
#     pass
#
# def p_params_list_1(p):
#     '''params_list : '''
#     pass
#
# def p_params_list_2(p):
#     '''params_list : expr'''
#     pass
#
# def p_params_list_3(p):
#     '''params_list : params_list COMMA expr'''
#     pass



#
# # def p_statement_1(p):
# #     '''statement : preproc_block
# #                  | area_block
# #                  | for_each_block
# #                  | for_block
# #                  | while_block
# #                  | if_block
# #                  | SEMI
# #                  '''
# #     pass
# #
# # def p_statement_2(p):
# #     '''statement : lvalue = rvalue SEMI'''
# #     pass
# #
# # def p_statement_3(p):
# #     '''statement : rvalue SEMI'''
# #     pass
# #
# # def p_lvalue(p):
# #     ''''''
# #     pass
#
#
# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc()

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    result = parser.parse(data)
    print(result)
