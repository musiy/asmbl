
class Module:
    proc_func_list = None
    statements_list = None
    def __init__(self, statements_list, proc_func_list = None, global_vars = None):
        self.statements_list = statements_list
        self.proc_func_list = proc_func_list
        self.global_vars = global_vars


class VariablesDeclaration:
    directive = None
    vars_list = None
    def __init__(self, vars_list, directive = None):
        self.vars_list = vars_list
        self.directive = directive

class VarDesc:
    name = None
    export = None
    def __init__(self, name, export = False):
        self.name = name
        self.export = export

class Function:
    is_function = None
    is_export = None
    directive = None
    name = None
    vars_list = None
    body = None
    def __init__(self, is_function, is_export, directive, name, vars_list, body):
        self.is_function = is_function
        self.is_export = is_export
        self.directive = directive
        self.name = name
        self.vars_list = vars_list
        self.body = body

class FuncBody:
    vars_decls_list = None
    statements = None
    def __init__(self, vars_decls_list = None, statements = None):
        self.vars_decls_list = vars_decls_list
        self.statements = statements

class FuncVarInitDecl:
    is_val = None
    var_name = None
    init_value = None
    def __init__(self, is_val, var_name, init_value = None):
        self.is_val = is_val
        self.var_name = var_name
        self.init_value = init_value

class Statement:
    pass

class StatementAssignment(Statement):
    # for expression like 'a = 1 + 2' and 'f()'
    property = None
    expr = None
    def __init__(self, property, expr = None):
        self.property = property
        self.expr = expr

class StatementFuncCall(Statement):
    func_call_path = None
    def __init__(self, func_call_path):
        self.func_call_path = func_call_path

class TryStatement(Statement):
    try_statements = None
    except_statements = None
    def __init__(self, try_statements, except_statements):
        self.try_statements = try_statements
        self.except_statements = except_statements

class LabeledStatement(Statement):
    label_name = None
    statement = None
    def __init__(self, label_name, statement):
        self.label_name = label_name
        self.statement = statement

class IfElseStatement(Statement):
    if_expression = None
    if_statements = None
    else_collection = None
    def __init__(self, if_expression, if_statements, else_collection):
        self.if_expression = if_expression
        self.if_statements = if_statements
        self.else_collection = else_collection

class ElseCollection:
    condition = None
    statements = None
    def __init__(self, statements, condition = None):
        self.condition = condition
        self.statements = statements

class ForEachBlock(Statement):
    id_name = None
    expression = None
    statements = None
    def __init__(self, id_name, expression, statements):
        self.id_name = id_name
        self.expression = expression
        self.statements = statements

class ForBlock(Statement):
    id_name = None
    expression_start = None
    expression_end = None
    statements = None
    def __init__(self, id_name, expression_start, expression_end, statements):
        self.id_name = id_name
        self.expression_start = expression_start
        self.expression_end = expression_end
        self.statements = statements

class WhileBlock(Statement):
    expression = None
    statements = None
    def __init__(self, expression, statements):
        self.expression = expression
        self.statements = statements

class JumpStatemets(Statement):
    key_word = None
    second_param = None
    def __init__(self, key_word, second_param = None):
        self.key_word = key_word
        self.second_param = second_param


class Property:
    property_left = None
    property_right = None
    def __init__(self, property_left, property_right = None):
        self.property_left = property_left
        self.property_right = property_right

class PropertyElement:
    prop_element = None
    expr = None
    def __init__(self, prop_element, expr = None):
        self.prop_element = prop_element
        self.expr = expr

class FuncCall:
    name = None
    param_list = None
    def __init__(self, name, param_list):
        self.name = name
        self.param_list = param_list


class ParamList:
    pass

class ParamListEmpty(ParamList):
    pass

class ParamListExpr(ParamList):
    expr = None
    def __init__(self, expr):
        self.expr = expr

class ParamListComma(ParamList):
    param_left = None
    param_right = None
    def __init__(self, param_left, param_right = None):
        self.param_left = param_left
        self.param_right = param_right

class Expr:
    pass

class SimpleExpr(Expr):
    expr = None
    is_group = None
    def __init__(self, expr, is_group=False):
        self.expr = expr
        self.is_group = is_group

class BinaryExpr(Expr):
    expr1 = None
    expr2 = None
    oper  = None
    def __init__(self, expr1, expr2, oper):
        self.expr1 = expr1
        self.expr2 = expr2
        self.oper = oper

class QuestionExpr(Expr):
    expr = None
    first = None
    second = None
    def __init__(self, expr, first, second):
        self.expr = expr
        self.first = first
        self.second = second

class NewExpr(Expr):
    id = None
    param_list = None
    def __init__(self, id = None, param_list = None):
        self.id = id
        self.param_list = param_list

class UnaryExpr(Expr):
    op = None
    expr = None
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

## PREPROC

class PreprocIfElseStatement:
    if_expression = None
    if_statements = None
    else_collection = None
    def __init__(self, if_expression, if_statements, else_collection):
        self.if_expression = if_expression
        self.if_statements = if_statements
        self.else_collection = else_collection


class PreprocElseCollection:
    condition = None
    statements = None
    def __init__(self, statements, condition = None):
        self.condition = condition
        self.statements = statements

class PreprocExpr:
    expr = None
    brackets = None
    def __init__(self, expr, brackets):
        self.expr = expr
        self.brackets = brackets

class PreprocExprBinary:
    expr_left = None
    expr_right = None
    oper = None
    def __init__(self, expr_left, expr_right, oper):
        self.expr_left = expr_left
        self.expr_right = expr_right
        self.oper = oper

class PreprocExprNot:
    expr = None
    def __init__(self, expr):
        self.expr = expr

## SIMPLE TYPES

class Bool:
    value = None
    def __init__(self, value):
        self.value = value

class Strings:
    value = None
    def __init__(self, value):
        self.value = value

class Number:
    value = None
    def __init__(self, value):
        self.value = value

class Date:
    value = None
    def __init__(self, value):
        self.value = value

class Undefined:
    pass

class Empty:
    pass
