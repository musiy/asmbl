import ply.yacc as yacc
from lexer1c import tokens
import strct1c

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
    p[0] = strct1c.Module(statements_list = p[4], proc_func_list = p[3], global_vars = p[1])

def p_module_2(p):
    '''module : global_vars SEMI statements'''
    p[0] = strct1c.Module(statements_list=p[3], global_vars=p[1])

def p_module_3(p):
    '''module : proc_func_list statements'''
    p[0] = strct1c.Module(statements_list=p[2], proc_func_list=p[1])

def p_module_4(p):
    '''module : statements'''
    p[0] = strct1c.Module(statements_list=p[1])

## global vars
def p_global_vars_1(p):
    '''global_vars : global_vars SEMI directive VAR global_var_decl_list'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.VariablesDeclaration(p[3], p[5]))

def p_global_vars_2(p):
    '''global_vars : directive VAR global_var_decl_list'''
    p[0] = [strct1c.VariablesDeclaration(p[1], p[3])]

def p_global_var_decl_list_1(p):
    '''global_var_decl_list : global_var_decl_list COMMA global_var_decl'''
    p[0] = [x for x in p[1]]
    p[0].append(p[3])
    pass

def p_global_var_decl_list_2(p):
    '''global_var_decl_list : global_var_decl'''
    p[0] = [p[1]]

def p_global_var_decl_1(p):
    '''global_var_decl : ID'''
    p[0] = strct1c.VarDesc(p[1])

def p_global_var_decl_2(p):
    '''global_var_decl : ID EXPORT'''
    p[0] = strct1c.VarDesc(p[1], True)

def p_directive(p):
    '''directive : DIRECTIVE'''
    p[0] = p[1]

def p_directive_empty(p):
    '''directive : empty'''
    p[0] = None

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
    '''func_begin : directive FUNCTION'''
    pass

def p_proc_begin(p):
    '''proc_begin : directive PROCEDURE'''
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

def p_statements_list(p):
    '''statements : statements SEMI statement'''
    p[0] = [x for x in p[1]]
    p[0].append(p[3])

def p_statements_simple(p):
    '''statements : statement'''
    p[0] = [p[1]]

def p_statements_error(p):
    '''statements : statements error SEMI statement'''
    print ("Incorect statement on line %d" % p.lexer.lineno)
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

def p_statement_eq(p):
    '''statement : property EQ expr'''
    p[0] = strct1c.StatementSimple(p[1], p[3])

def p_statement_func_call(p):
    '''statement : property'''
    # здесь вместо property должен быть сложный вызов func_call,
    # например для выражения a.a[1].f()
    p[0] = strct1c.StatementSimple(p[1])
    pass

def p_statement_empty(p):
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

def p_preproc_expr_not(p):
    '''preproc_expr : NOT preproc_expr %prec UNOT'''
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
    p[0] = strct1c.Property(p[1], p[3])

def p_property_2(p):
    '''property : prop_element'''
    p[0] = strct1c.Property(p[1])

def p_prop_element_1(p):
    '''prop_element : prop_element LSB expr RSB'''
    p[0] = strct1c.PropertyElement(p[1], p[3]);

def p_prop_element_2(p):
    '''prop_element : func_call'''
    p[0] = strct1c.PropertyElement(p[1]);

def p_prop_element_3(p):
    '''prop_element : ID'''
    p[0] = strct1c.PropertyElement(p[1]);

def p_func_call(p):
    '''func_call : ID LPAREN params_list RPAREN'''
    p[0] = strct1c.FuncCall(p[1], p[3])

## expression

def p_expr_simple(p):
    '''expr : property
            | bool
            | NUMBER
            | DATE
            | strings
            | UNDEFINED'''
    p[0] = strct1c.SimpleExpr(p[1])

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = strct1c.SimpleExpr(p[2], True)

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
    p[0] = strct1c.BinaryExpr(p[1], p[3], p[2])

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
    '''params_list : params_list COMMA expr'''
    p[0] = strct1c.ParamListComma(p[1], p[3])

def p_params_list_2(p):
    '''params_list : params_list COMMA empty'''
    p[0] = strct1c.ParamListComma(p[1])

def p_params_list_empty(p):
    '''params_list : empty'''
    p[0] = strct1c.Empty

def p_params_list_expr(p):
    '''params_list : expr'''
    p[0] = [p[1]]

## -- END statement --

def p_strings_1(p):
    '''strings : strings STRING'''
    p[0] = strct1c.StringsSeq(p[1], p[2])

def p_strings_2(p):
    '''strings : STRING'''
    p[0] = strct1c.StringsBase(p[1])

def p_empty(p):
    '''empty : '''
    p[0] = strct1c.Empty()

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input on %d"  % p.lexer.lineno)

# Build the parser
parser = yacc.yacc()

if __name__ == '__main__':
    data = open("samples/sample.1c", encoding='utf-8').read()
    result = parser.parse(data)
