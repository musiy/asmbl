# -*- coding: utf-8 -*-

import ply.yacc as yacc
from lexer1c import tokens
import strct1c

precedence = (
               ('left', 'OR', 'AND'),
               ('left', 'EQ', 'NOT_EQ', 'LT', 'LE', 'GT', 'GE'),
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
    p[0] = strct1c.Module(statements_list=p[3], proc_func_list = [], global_vars=p[1])

def p_module_3(p):
    '''module : proc_func_list statements'''
    p[0] = strct1c.Module(statements_list=p[2], proc_func_list=p[1], global_vars = [])

def p_module_4(p):
    '''module : statements'''
    p[0] = strct1c.Module(statements_list=p[1], proc_func_list = [], global_vars = [])

## global vars
def p_global_vars_1(p):
    '''global_vars : global_vars SEMI directive VAR global_var_decl_list'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.VariablesDeclaration(p[5], p[3]))

def p_global_vars_2(p):
    '''global_vars : directive VAR global_var_decl_list'''
    p[0] = [strct1c.VariablesDeclaration(p[3], p[1])]

def p_global_var_decl_list_1(p):
    '''global_var_decl_list : global_var_decl_list COMMA global_var_decl'''
    p[0] = [x for x in p[1]]
    p[0].append(p[3])

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
    p[0] = ""

## funcs & procs

def p_func_decls(p):
    '''proc_func_list : proc_func_list func_decl
                      | proc_func_list proc_decl'''
    p[0] = [x for x in p[1]]
    p[0].append(p[2])

def p_func_decls_one(p):
    '''proc_func_list : func_decl
                      | proc_decl'''
    p[0] = [p[1]]

## -- begin function & procedure declaration --

def p_func_decl(p):
    '''func_decl : directive FUNCTION ID LPAREN declarator_list RPAREN func_body END_FUNCTION'''
    p[0] = strct1c.Function(True, False, p[1], p[3], p[5], p[7])

def p_func_decl_export(p):
    '''func_decl : directive FUNCTION ID LPAREN declarator_list RPAREN EXPORT func_body END_FUNCTION'''
    p[0] = strct1c.Function(True, True, p[1], p[3], p[5], p[8])

def p_proc_decl(p):
    '''proc_decl : directive PROCEDURE ID LPAREN declarator_list RPAREN func_body END_PROCEDURE'''
    p[0] = strct1c.Function(False, False, p[1], p[3], p[5], p[7])

def p_proc_decl_export(p):
    '''proc_decl : directive PROCEDURE ID LPAREN declarator_list RPAREN EXPORT func_body END_PROCEDURE'''
    p[0] = strct1c.Function(False, True, p[1], p[3], p[5], p[8])

def p_init_declarator_list_1(p):
    '''declarator_list : declarator_list COMMA init_declarator'''
    p[0] = [x for x in p[1]]
    p[0].append(p[3])

def p_init_declarator_list_2(p):
    '''declarator_list : init_declarator'''
    p[0] = [p[1]]

def p_init_declarator_list_3(p):
    '''declarator_list : empty'''
    p[0] = []

def p_init_declarator_1(p):
    '''init_declarator : ID'''
    p[0] = strct1c.FuncVarInitDecl(False, p[1])

def p_init_declarator_2(p):
    '''init_declarator : VAL ID'''
    p[0] = strct1c.FuncVarInitDecl(True, p[2])

def p_init_declarator_3(p):
    '''init_declarator : ID EQ func_param_initializer'''
    p[0] = strct1c.FuncVarInitDecl(False, p[1], p[3])

def p_init_declarator_4(p):
    '''init_declarator : VAL ID EQ func_param_initializer'''
    p[0] = strct1c.FuncVarInitDecl(True, p[2], p[4])

def p_initializer(p):
    '''func_param_initializer : bool
                              | strings
                              | number
                              | date
                              | undefined'''
    p[0]=p[1]

## -- end function & procedure declaration --

## -- begin function & procedure body --

def p_func_body_1(p):
    '''func_body : vars_decls_list SEMI statements'''
    p[0] = strct1c.FuncBody(vars_decls_list=p[1], statements=p[3])

def p_func_body_vars_decls_list(p):
    '''func_body : vars_decls_list'''
    p[0] = strct1c.FuncBody(vars_decls_list=p[1], statements = [])

def p_func_body_statements(p):
    '''func_body : statements'''
    p[0] = strct1c.FuncBody(vars_decls_list=[], statements=p[1])

def p_perem_decl_list_1(p):
    '''vars_decls_list : vars_decls_list SEMI VAR vars_list'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.VariablesDeclaration(p[4]))

def p_perem_decl_list_2(p):
    '''vars_decls_list : VAR vars_list'''
    p[0] = [strct1c.VariablesDeclaration(p[2])]

def p_perems_list_1(p):
    '''vars_list : vars_list COMMA ID'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.VarDesc(p[3]))

def p_perems_list_2(p):
    '''vars_list : ID'''
    p[0] = [strct1c.VarDesc(p[1])]

## statements

def p_statements_list(p):
    '''statements : statements SEMI statement'''
    p[0] = [x for x in p[1]]
    if not isinstance(p[3], strct1c.Empty):
        # пропускаем завершающий пустой блок
        p[0].append(p[3])

def p_statements_simple(p):
    '''statements : statement'''
    p[0] = [] if isinstance(p[1], strct1c.Empty) else [p[1]]

def p_statements_error(p):
    '''statements : statements error SEMI statement'''
    print ("Incorect statement on line %d" % p.lexer.lineno)

## -- end function & procedure body --

def p_statement_block(p):
    '''statement : iteration_statement
                 | jump_statement
                 | if_else_statement
                 | try_statement
                 | labeled_statement
                 | preproc_statement'''
    p[0] = p[1]

def p_statement_eq(p):
    '''statement : property EQ expr'''
    p[0] = strct1c.StatementAssignment(p[1], p[3])

def p_statement_func_call(p):
    '''statement : property'''
    # todo добавить проверку, что оканчивается на вызов функции
    # todo например, p.p.p[1].f() - вырено, а p.p.p[1] - нет
    p[0] = strct1c.StatementFuncCall(p[1])

def p_statement_empty(p):
    '''statement : empty'''
    p[0] = p[1]

def p_try_statement(p):
    '''try_statement : TRY statements EXCEPTION statements END_TRY'''
    p[0] = strct1c.TryStatement(p[2], p[4])

## labeled statement

def p_labeled_statement(p):
    '''labeled_statement : LABEL COLON statement'''
    p[0] = strct1c.LabeledStatement(p[1], p[3])

## if-else statement

def p_if_else_statement(p):
    '''if_else_statement : IF expr THEN statements else_block END_IF'''
    p[0] = strct1c.IfElseStatement(p[2], p[4], p[5])

def p_else_block_empty(p):
    '''else_block : empty'''
    p[0] = []

def p_else_block_1(p):
    '''else_block : else_if_collection ELSE statements'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.ElseStatement(p[3]))

def p_else_block_2(p):
    '''else_block : else_if_collection'''
    p[0] = p[1]

def p_else_block_3(p):
    '''else_block : ELSE statements'''
    p[0] = [strct1c.ElseStatement(p[2])]

def p_else_if_collection_1(p):
    '''else_if_collection : else_if_collection ELSE_IF expr THEN statements'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.ElseStatement(p[5], p[3]))

def p_else_if_collection_2(p):
    '''else_if_collection : ELSE_IF expr THEN statements'''
    p[0] = [strct1c.ElseStatement(p[4], p[2])]

## iteration statements

def p_iteration_statement(p):
    '''iteration_statement : for_each_block
                           | for_block
                           | while_block'''
    p[0] = p[1]

def p_for_each(p):
    '''for_each_block : FOR_EACH ID FROM expr DO statements END_DO'''
    p[0] = strct1c.ForEachBlock(p[2], p[4], p[6])

def p_for_block(p):
    '''for_block : FOR ID EQ expr TO expr DO statements END_DO'''
    p[0] = strct1c.ForBlock(p[2], p[4], p[6], p[8])

def p_while_block(p):
    '''while_block : WHILE expr DO statements END_DO'''
    p[0] = strct1c.WhileBlock(p[2], p[4])

## jump statements
def p_jump_statement(p):
    '''jump_statement : CONTINUE
                      | BREAK'''
    p[0] = strct1c.JumpStatemets(p[1])

def p_jump_statement_two(p):
    '''jump_statement : RETURN expr_opt
                      | RAISE expr_opt
                      | GOTO LABEL'''
    p[0] = strct1c.JumpStatemets(p[1], p[2])

def p_expr_opt_1(p):
    '''expr_opt : empty'''
    p[0] = p[1]

def p_expr_opt_2(p):
    '''expr_opt : expr'''
    p[0] = p[1]

## preproc statement

def p_preproc_if_else_block(p):
    '''preproc_statement : DEF_IF preproc_expr THEN statements preproc_else_block DEF_END_IF'''
    p[0] = strct1c.PreprocIfElseStatement(p[2], p[4], p[5])

def p_preproc_else_block_empty(p):
    '''preproc_else_block : empty'''
    p[0] = []

def p_preproc_else_block_1(p):
    '''preproc_else_block : preproc_else_if_collection DEF_ELSE statements'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.PreprocElse(p[3]))

def p_preproc_else_block_2(p):
    '''preproc_else_block : preproc_else_if_collection'''
    p[0] = [x for x in p[1]]

def p_preproc_else_block_3(p):
    '''preproc_else_block : DEF_ELSE statements'''
    p[0] = [strct1c.PreprocElse(p[2])]

def p_preproc_else_if_collection_1(p):
    '''preproc_else_if_collection : preproc_else_if_collection DEF_ELSE_IF preproc_expr THEN statements'''
    p[0] = [x for x in p[1]]
    p[0].append(strct1c.PreprocElse(p[5], p[3]))

def p_preproc_else_if_collection_2(p):
    '''preproc_else_if_collection : DEF_ELSE_IF preproc_expr THEN statements'''
    p[0] = [strct1c.PreprocElse(p[4], p[2])]

def p_preproc_expr_binary(p):
    '''preproc_expr : preproc_expr AND preproc_expr
                    | preproc_expr OR preproc_expr'''
    p[0] = strct1c.PreprocExprBinary(p[1], p[3], p[2])

def p_preproc_expr_rb(p):
    '''preproc_expr : LPAREN preproc_expr RPAREN'''
    p[0] = strct1c.PreprocExpr(p[1], True)

def p_preproc_expr_simple(p):
    '''preproc_expr : ID'''
    p[0] = strct1c.PreprocExpr(p[1], False)

def p_preproc_expr_not(p):
    '''preproc_expr : NOT preproc_expr %prec UNOT'''
    p[0] = strct1c.PreprocExprNot(p[2])


## -- BEGIN statement  --

def p_property_1(p):
    '''property : property DOT prop_element'''
    if isinstance(p[1], strct1c.DottedExpression):
        property_dotted = p[1]
    else:
        property_dotted = strct1c.DottedExpression(p[1])
    property_dotted.append(p[3])
    p[0] = property_dotted

def p_property_2(p):
    '''property : prop_element'''
    p[0] = p[1]

def p_prop_element_1(p):
    '''prop_element : prop_element LSB expr RSB'''
    if isinstance(p[1], strct1c.PropertyIndexed):
        p[1].apnd(p[3])
        p[0] = p[1]
    else:
        p[0] = strct1c.PropertyIndexed(p[1], p[3])

def p_prop_element_2(p):
    '''prop_element : func_call'''
    p[0] = p[1]

def p_prop_element_3(p):
    '''prop_element : ID'''
    p[0] = strct1c.Identifier(p[1])

def p_func_call(p):
    '''func_call : ID LPAREN params_list RPAREN'''
    p[0] = strct1c.FuncCall(p[1], p[3])

## expression

def p_expr_simple(p):
    '''expr : property
            | bool
            | number
            | date
            | strings
            | undefined'''
    p[0] = p[1]

def p_expr_group(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = strct1c.GroupedExpr(p[2])

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
    p[0] = strct1c.QuestionExpr(p[3], p[5], p[7])

def p_expr_new_1(p):
    '''expr : NEW ID'''
    p[0] = strct1c.NewExpr(id=p[2])

def p_expr_new_2(p):
    '''expr : NEW ID LPAREN params_list RPAREN'''
    p[0] = strct1c.NewExpr(id=p[2], param_list=p[4])

def p_expr_new_3(p):
    '''expr : NEW LPAREN new_params_list RPAREN'''
    p[0] = strct1c.NewExpr(param_list=p[3])

def p_new_params_list_1(p):
    '''new_params_list : new_params_list COMMA expr'''
    p[0] = [x for x in p[1]]
    p[0].append(p[3])

def p_new_params_list_2(p):
    '''new_params_list : expr'''
    p[0] = [p[1]]

def p_expr_not(p):
    '''expr : NOT expr %prec UNOT'''
    p[0] = strct1c.UnaryExpr(p[1], p[2])

def p_expr_uminus(p):
    '''expr : MINUS expr %prec UMINUS'''
    p[0] = strct1c.UnaryExpr(p[1], p[2])

def p_expr_uplus(p):
    '''expr : PLUS expr %prec UPLUS'''
    p[0] = strct1c.UnaryExpr(p[1], p[2])

def p_params_list_1(p):
    '''params_list : params_list COMMA expr'''
    res = [x for x in p[1]]
    res += [p[3]]
    p[0] = res

def p_params_list_2(p):
    '''params_list : params_list COMMA empty'''
    res = [x for x in p[1]]
    res += [p[3]]
    p[0] = res

def p_params_list_empty(p):
    '''params_list : empty'''
    p[0] = [p[1]]

def p_params_list_expr(p):
    '''params_list : expr'''
    p[0] = [p[1]]

## -- END statement --

def p_bool(p):
    '''bool : TRUE
            | FALSE'''
    p[0] = strct1c.Bool(p[1])

def p_number(p):
    '''number : NUMBER'''
    p[0] = strct1c.Number(p[1])

def p_date(p):
    '''date : DATE'''
    p[0] = strct1c.Date(p[1])

def p_undefined(p):
    '''undefined : UNDEFINED'''
    p[0] = strct1c.Undefined()

def p_strings_list(p):
    '''strings : strings STRING'''
    p[1].apnd(p[2])
    p[0] = p[1]

def p_strings(p):
    '''strings : STRING'''
    p[0] = strct1c.Strings(p[1])

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
    strct1c.get_tokens_list(result.statements_list, obj_type="function", filter = set())
    print(strct1c.get_text(result))
    pass
