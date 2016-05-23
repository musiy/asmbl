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

## content

def p_module_1(p):
    '''module : global_vars SEMI proc_func_list statements'''
    pass

def p_module_2(p):
    '''module : global_vars SEMI statements'''
    pass

def p_module_3(p):
    '''module : proc_func_list statements'''
    pass

def p_module_4(p):
    '''module : statements'''
    pass

## global vars
def p_global_vars_1(p):
    '''global_vars : global_vars SEMI VAR global_var_decl_list'''
    pass

def p_global_vars_2(p):
    '''global_vars : VAR global_var_decl_list'''
    pass

def p_global_vars_3(p):
    '''global_vars : DIRECTIVE VAR global_var_decl_list'''
    pass

def p_global_var_decl_list_1(p):
    '''global_var_decl_list : global_var_decl_list COMMA global_var_decl'''

def p_global_var_decl_list_2(p):
    '''global_var_decl_list : global_var_decl'''

def p_global_var_decl_1(p):
    '''global_var_decl : ID'''

def p_global_var_decl_2(p):
    '''global_var_decl : ID EXPORT'''

## funcs & procs

def p_func_decls_1(p):
    '''proc_func_list : proc_func_list func_decl'''
    pass

def p_func_decls_2(p):
    '''proc_func_list : proc_func_list proc_decl'''
    pass

def p_func_decls_3(p):
    '''proc_func_list : func_decl
                      | proc_decl'''
    pass

## -- begin function & procedure declaration --

def p_func_decl_1(p):
    '''func_decl : func_begin ID LPAREN declarator_list RPAREN func_body END_FUNCTION'''
    pass

def p_func_decl_2(p):
    '''func_decl : func_begin ID LPAREN declarator_list RPAREN EXPORT func_body END_FUNCTION'''
    pass

def p_proc_decl_1(p):
    '''proc_decl : proc_begin ID LPAREN declarator_list RPAREN func_body END_PROCEDURE'''
    pass

def p_proc_decl_2(p):
    '''proc_decl : proc_begin ID LPAREN declarator_list RPAREN EXPORT func_body END_PROCEDURE'''
    pass

def p_func_begin(p):
    '''func_begin : DIRECTIVE FUNCTION
                  | FUNCTION'''
    pass

def p_proc_begin(p):
    '''proc_begin : DIRECTIVE PROCEDURE
                  | PROCEDURE'''
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
                              | strings
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
    '''func_body : vars_decls_list SEMI statements'''
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
    '''statements : statements SEMI statement'''
    pass

def p_statements_error(p):
    '''statements : statements error SEMI statement'''
    print ("Incorect statement on line %d" % p.lexer.lineno)
    pass

def p_statements_2(p):
    '''statements : statement'''
    pass

## -- end function & procedure body --

def p_statement(p):
    '''statement : iteration_statement
                 | jump_statement
                 | if_else_statement
                 | try_statement
                 | labeled_statement
                 | preproc_statement'''
    pass

def p_statement_1(p):
    '''statement : property EQ expr'''
    pass

def p_statement_2(p):
    '''statement : property'''
    # здесь вместо property должен быть сложный вызов func_call,
    # например для выражения a.a[1].f()
    pass

def p_statement_3(p):
    '''statement : empty'''
    pass

def p_try_statement(p):
    '''try_statement : TRY statements EXCEPTION statements END_TRY'''
    pass

## labeled statement

def p_labeled_statement(p):
    '''labeled_statement : LABEL COLON statement'''
    pass

## if-else statement

def p_if_else_statement(p):
    '''if_else_statement : IF expr THEN statements else_block END_IF'''
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

## iteration statements

def p_iteration_statement(p):
    '''iteration_statement : for_each_block
                           | for_block
                           | while_block'''
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

## jump statements
def p_jump_statement(p):
    '''jump_statement : RETURN expr_opt
                      | RAISE expr_opt
                      | CONTINUE
                      | BREAK
                      | GOTO LABEL'''
    pass

def p_expr_opt_1(t):
    '''expr_opt : empty'''
    pass

def p_expr_opt_2(t):
    '''expr_opt : expr'''
    pass

## preproc statement

def p_preproc_if_else_block_1(p):
    '''preproc_statement : DEF_IF preproc_expr THEN statements DEF_END_IF'''
    pass

def p_preproc_if_else_block_2(p):
    '''preproc_statement : DEF_IF preproc_expr THEN statements preproc_else_block DEF_END_IF'''
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

## -- BEGIN statement  --

def p_property_1(p):
    '''property : property DOT prop_element'''
    pass

def p_property_2(p):
    '''property : prop_element'''
    pass

def p_prop_element_1(p):
    '''prop_element : prop_element LSB expr RSB'''
    pass

def p_prop_element_2(p):
    '''prop_element : func_call'''
    pass

def p_prop_element_3(p):
    '''prop_element : ID'''
    pass

def p_func_call(p):
    '''func_call : ID LPAREN params_list RPAREN'''
    pass

## expression

def p_expr_simple(p):
    '''expr : property
            | bool
            | NUMBER
            | DATE
            | strings
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
    pass

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    pass

def p_expr_qstn(p):
    '''expr : QSTN LPAREN expr COMMA expr COMMA expr RPAREN'''
    pass

def p_expr_new_1(p):
    '''expr : NEW ID'''
    pass

def p_expr_new_2(p):
    '''expr : NEW ID LPAREN params_list RPAREN'''
    pass

def p_expr_new_3(p):
    '''expr : NEW LPAREN new_params_list RPAREN'''
    pass

def p_new_params_list_1(p):
    '''new_params_list : new_params_list COMMA expr'''
    pass

def p_new_params_list_2(p):
    '''new_params_list : expr'''
    pass

def p_expr_not(p):
    '''expr : NOT expr %prec UNOT'''
    pass

def p_expr_uminus(p):
    '''expr : MINUS expr %prec UMINUS'''
    pass

def p_expr_uplus(p):
    '''expr : PLUS expr %prec UPLUS'''
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

def p_strings_1(p):
    '''strings : strings STRING'''
    pass

def p_strings_2(p):
    '''strings : STRING'''
    pass

def p_empty(p):
    '''empty : '''
    pass

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input on %d"  % p.lexer.lineno)

# Build the parser
parser = yacc.yacc()

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    result = parser.parse(data)
