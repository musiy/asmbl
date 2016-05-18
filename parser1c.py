import ply.yacc as yacc
from lexer1c import tokens

precedence = (
               ('left', 'EQ', 'NOT_EQ', 'LT', 'LE', 'GT', 'GE'),
               ('left', 'OR', 'AND'),
               ('left', 'PLUS', 'MINUS'),
               ('left', 'TIMES', 'DIVIDE', 'MOD'),
               ('right', 'UNOT'),
               ('right', 'UMINUS', 'UPLUS')
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
    '''declarator_list : empty'''
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
    '''func_body : vars_decls_list semi statements'''
    pass

def p_func_body_2(p):
    '''func_body : vars_decls_list
                 | statements'''
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

## statements

def p_statements_1(p):
    '''statements : statements_list semi'''
    pass

def p_statements_2(p):
    '''statements : statements_list'''
    pass

def p_statements_3(p):
    '''statements : empty'''
    pass

def p_statements_list_1(p):
    '''statements_list : statements_list semi statement'''
    pass

def p_statements_list_2(p):
    '''statements_list : statement'''
    pass

## -- end function & procedure body --

def p_statement_1(p):
    '''statement : prop_complex EQ expr'''
    pass

def p_statement_2(p):
    '''statement : func_call'''
    pass

def p_statement_3(p):
    '''statement : CONTINUE
                 | BREAK'''
    pass

def p_statement_4(p):
    '''statement : GOTO LABEL'''
    pass

def p_semi_1(p):
    '''semi : semi SEMI'''
    pass

def p_semi_2(p):
    '''semi : SEMI'''
    pass

## -- BEGIN statement  --

def p_prop_complex_1(p):
    '''prop_complex : prop_complex DOT property'''
    pass

def p_prop_complex_2(p):
    '''prop_complex : func_call DOT property'''
    pass

def p_prop_complex_3(p):
    '''prop_complex : property'''
    pass

def p_property_1(p):
    '''property : property LSB expr RSB'''
    pass

def p_property_2(p):
    '''property : func_call LSB expr RSB'''
    pass

def p_property_3(p):
    '''property : ID'''
    pass

def p_expr_simple(p):
    '''expr : prop_complex
            | func_call
            | bool
            | NUMBER
            | DATE
            | STRING
            | UNDEFINED'''
    pass

def p_expr_binary(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr MOD expr
            | expr OR expr
            | expr AND expr
            | expr NOT_EQ expr
            | expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr
            | expr EQ expr
            '''
    # | expr EQ expr
    pass

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    pass

def p_expr_not(p):
    'expr : NOT expr %prec UNOT'
    pass

def p_expr_uminus(p):
    'expr : MINUS expr %prec UMINUS'
    pass

def p_expr_uplus(p):
    'expr : PLUS expr %prec UPLUS'
    pass

def p_func_call(p):
    '''func_call : ID LPAREN params_list RPAREN'''
    pass

def p_params_list_1(p):
    '''params_list : empty'''
    pass

def p_params_list_2(p):
    '''params_list : expr'''
    pass

def p_params_list_3(p):
    '''params_list : params_list COMMA expr'''
    pass

## -- END statement --

## -- BEGIN complex statement --

def p_statement_complex_1(p):
    '''statement : for_each_block
                 | for_block
                 | while_block
                 | if_else_block
                 | try_block
                 | preproc_if_else_block'''
    pass

def p_for_each(p):
    '''for_each_block : FOR_EACH ID FROM expr DO statements END_DO'''
    pass

def p_for_block(p):
    '''for_block : FOR ID EQ expr TO expr DO statements END_DO'''
    pass

def p_while_block(p):
    '''while_block : WHILE expr DO statements END_DO'''
    pass

def p_try_block(p):
    '''try_block : TRY statements EXCEPTION statements END_TRY'''
    pass

## -- BEGIN if-elseif-else-endif block --

def p_if_else_block(p):
    '''if_else_block : IF expr THEN statements else_block END_IF'''
    pass

def p_else_block_empty(p):
    '''else_block : empty'''
    pass

def p_else_block_1(p):
    '''else_block : else_if_collection ELSE statements'''
    pass

def p_else_block_2(p):
    '''else_block : else_if_collection'''
    pass

def p_else_block_3(p):
    '''else_block : ELSE statements'''
    pass

def p_else_if_collection_1(p):
    '''else_if_collection : else_if_collection else_if'''
    pass

def p_else_if_collection_2(p):
    '''else_if_collection : else_if'''
    pass

def p_else_if_block(p):
    '''else_if : ELSE_IF expr THEN statements'''
    pass

## -- END if-elseif-else-endif block --

def p_preproc_if_else_block_1(p):
    '''preproc_if_else_block : DEF_IF preproc_expr THEN statements DEF_END_IF'''
    pass

def p_preproc_if_else_block_2(p):
    '''preproc_if_else_block : DEF_IF preproc_expr THEN statements preproc_else_block DEF_END_IF'''
    pass

def p_preproc_else_block_1(p):
    '''preproc_else_block : preproc_else_if_collection DEF_ELSE statements'''
    pass

def p_preproc_else_block_2(p):
    '''preproc_else_block : preproc_else_if_collection'''
    pass

def p_preproc_else_block_3(p):
    '''preproc_else_block : DEF_ELSE statements'''
    pass

def p_preproc_else_if_collection_1(p):
    '''preproc_else_if_collection : preproc_else_if_collection preproc_else_if'''
    pass

def p_preproc_else_if_collection_2(p):
    '''preproc_else_if_collection : preproc_else_if'''
    pass

def p_preproc_else_if_block(p):
    '''preproc_else_if : DEF_ELSE_IF preproc_expr THEN statements'''
    pass

def p_preproc_expr_1(p):
    '''preproc_expr : ID'''
    pass

def p_preproc_expr_2(p):
    '''preproc_expr : preproc_expr AND preproc_expr
                    | preproc_expr OR preproc_expr'''
    pass

def p_preproc_expr_3(p):
    '''preproc_expr : LPAREN preproc_expr RPAREN'''
    pass

## -- END complex statement --

def p_empty(p):
    '''empty : '''
    pass

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc()

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    result = parser.parse(data)
    print(result)
