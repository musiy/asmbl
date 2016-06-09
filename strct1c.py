# -*- coding: utf-8 -*-

_gl_indend = None

def set_indent(indent):
    global _gl_indend
    _gl_indend = indent

def get_indent_spaces():
    global _gl_indend
    return _gl_indend*" "

def incrase_indent():
    global _gl_indend
    _gl_indend += 4

def decrase_indent():
    global _gl_indend
    _gl_indend -= 4

def get_op_list_text(op_list, add_semicolon = True):
    global _gl_indend
    text = ""
    for op in op_list:
        text += _gl_indend*" " + op.get_text()
        if add_semicolon and not isinstance(op, PreprocIfElseStatement):
            text += ";"
        text += "\n"
    return text

def get_text(module):
    set_indent(0)
    return module.get_text()

def get_func_list(struct_list):
    func_list = []
    for x in struct_list:
        func_list += x.get_func_list()
    return func_list

class Module:
    global_vars = None
    proc_func_list = None
    statements_list = None
    def __init__(self, statements_list, proc_func_list = None, global_vars = None):
        self.statements_list = statements_list
        self.proc_func_list = proc_func_list
        self.global_vars = global_vars
    def get_text(self):
        text = get_op_list_text(self.global_vars) + "\n"
        text += get_op_list_text(self.proc_func_list, False) + "\n"
        text += get_op_list_text(self.statements_list) + "\n"
        return text

class VariablesDeclaration:
    directive = None
    vars_list = None
    def __init__(self, vars_list, directive = None):
        self.vars_list = vars_list
        self.directive = directive
    def get_text(self):
        text = ""
        if self.directive:
            text += self.directive + "\n" + get_indent_spaces()
        text += "Перем "
        not_first = False
        for var_desc in self.vars_list:
            if not_first:
                text += ", "
            text += var_desc.get_text()
            not_first = True
        return text

class VarDesc:
    name = None
    export = None
    def __init__(self, name, export = False):
        self.name = name
        self.export = export
    def get_text(self):
        text = self.name
        if self.export:
            text += " Экспорт"
        return text

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
    def get_text(self):
        text = self.directive + "\n"
        text += ("Функция" if self.is_function else "Процедура") + " "
        text += self.name + "("
        not_first = False
        for var_init_decl in self.vars_list:
            if not_first:
                text += ", "
            text += var_init_decl.get_text()
            not_first = True
        text += ")" + (" Экспорт" if self.is_export else "") + "\n"

        incrase_indent()
        text += self.body.get_text()
        decrase_indent()

        text += "КонецФункции" if self.is_function else "КонецПроцедуры"
        return text

class FuncVarInitDecl:
    is_val = None
    var_name = None
    init_value = None
    def __init__(self, is_val, var_name, init_value = None):
        self.is_val = is_val
        self.var_name = var_name
        self.init_value = init_value
    def get_text(self):
        text = self.var_name
        if self.is_val:
            text = "знач " + text
        if self.init_value:
            text += " = " + self.init_value.get_text()
        return text

class FuncBody:
    vars_decls_list = None
    statements = None
    def __init__(self, vars_decls_list = None, statements = None):
        self.vars_decls_list = vars_decls_list
        self.statements = statements
    def get_func_list(self):
        return get_func_list(self.statements)
    def get_text(self):
        text = get_op_list_text(self.vars_decls_list)
        if self.vars_decls_list:
            text += "\n"
        text += get_op_list_text(self.statements)
        return text

class Statement:
    def __init__(self): pass

class StatementAssignment(Statement):
    # for expression like 'a = 1 + 2' and 'f()'
    property = None
    expr = None
    def __init__(self, property, expr = None):
        self.property = property
        self.expr = expr
    def get_func_list(self):
        return self.expr.get_func_list()
    def get_text(self):
        return self.property.get_text() + " = " + self.expr.get_text()


class StatementFuncCall(Statement):
    func_call_path = None
    def __init__(self, func_call_path):
        self.func_call_path = func_call_path
    def get_func_list(self):
        return self.func_call_path.get_func_list()
    def get_text(self):
        return self.func_call_path.get_text()

class TryStatement(Statement):
    try_statements = None
    except_statements = None
    def __init__(self, try_statements, except_statements):
        self.try_statements = try_statements
        self.except_statements = except_statements
    def get_func_list(self):
        return get_func_list(self.try_statements) + get_func_list(self.except_statements)
    def get_text(self):
        text = "Попытка" + "\n"
        incrase_indent()
        text += get_op_list_text(self.try_statements)
        decrase_indent()
        text += get_indent_spaces() + "Исключение" + "\n"
        incrase_indent()
        text += get_op_list_text(self.except_statements)
        decrase_indent()
        text += get_indent_spaces() + "КонецПопытки"
        return text


class LabeledStatement(Statement):
    label_name = None
    statement = None
    def __init__(self, label_name, statement):
        self.label_name = label_name
        self.statement = statement
    def get_func_list(self):
        return self.statement.get_func_list()
    def get_text(self):
        text = self.label_name + ":" + "\n"
        text += get_indent_spaces() + self.statement.get_text()
        return text


class IfElseStatement(Statement):
    if_expression = None
    if_statements = None
    else_collection = None
    def __init__(self, if_expression, if_statements, else_collection):
        self.if_expression = if_expression
        self.if_statements = if_statements
        self.else_collection = else_collection
    def get_func_list(self):
        return self.if_expression.get_func_list() \
               + get_func_list(self.if_statements) \
               + get_func_list(self.else_collection)
    def get_text(self):
        text = "Если " + self.if_expression.get_text() + " Тогда" + "\n"
        incrase_indent()
        text += get_op_list_text(self.if_statements)
        decrase_indent()

        for else_st in self.else_collection:
            if else_st.condition:
                text += get_indent_spaces() + "ИначеЕсли " + else_st.condition.get_text() + " Тогда"
            else:
                text += get_indent_spaces() + "Иначе"
            text += "\n"
            incrase_indent()
            text += get_op_list_text(else_st.statements)
            decrase_indent()

        text += get_indent_spaces() + "КонецЕсли"
        return text

class ElseStatement:
    condition = None
    statements = None
    def __init__(self, statements, condition = None):
        self.condition = condition
        self.statements = statements
    def get_func_list(self):
        result = []
        if (self.condition):
            result += self.condition.get_func_list()
        return result+get_func_list(self.statements)

class ForEachBlock(Statement):
    id_name = None
    expression = None
    statements = None
    def __init__(self, id_name, expression, statements):
        self.id_name = id_name
        self.expression = expression
        self.statements = statements
    def get_func_list(self):
        return self.expression.get_func_list() \
               + get_func_list(self.statements)
    def get_text(self):
        text = "Для Каждого " + self.id_name + " Из " + self.expression.get_text() + " Цикл" + "\n"
        incrase_indent()
        text += get_op_list_text(self.statements)
        decrase_indent()
        text += get_indent_spaces() + "КонецЦикла"
        return text


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
    def get_func_list(self):
        return self.expression_start.get_func_list() \
               + self.expression_end.get_func_list() \
               + get_func_list(self.statements)
    def get_text(self):
        text = "Для " + self.id_name + " = " + self.expression_start.get_text() \
                + " По " + self.expression_end.get_text() + " Цикл" + "\n"
        incrase_indent()
        text += get_op_list_text(self.statements)
        decrase_indent()
        text += get_indent_spaces() + "КонецЦикла"
        return text


class WhileBlock(Statement):
    expression = None
    statements = None
    def __init__(self, expression, statements):
        self.expression = expression
        self.statements = statements
    def get_func_list(self):
        return self.expression.get_func_list() \
               + get_func_list(self.statements)
    def get_text(self):
        text = "Пока " + self.expression.get_text() + " Цикл" + "\n"
        incrase_indent()
        text += get_op_list_text(self.statements)
        decrase_indent()
        text += get_indent_spaces() + "КонецЦикла"
        return text


class JumpStatemets(Statement):
    key_word = None
    second_param = None
    def __init__(self, key_word, second_param = None):
        self.key_word = key_word
        self.second_param = second_param
    def get_func_list(self):
        result = []
        if self.second_param:
            result += self.second_param.get_func_list()
        return result
    def get_text(self):
        text = self.key_word
        if self.second_param:
            text += " " + self.second_param.get_text()
        return text

class DottedExpression:
    properties_list = None
    def __init__(self, property):
        self.properties_list = [property]
    def append(self, property):
        self.properties_list += [property]
    def get_func_list(self):
        result = []
        # расчитываем на вызов <имя модуля>.<вызов функции>
        if len(self.properties_list) == 2:
            if isinstance(self.properties_list[0], Identifier) and isinstance(self.properties_list[1], FuncCall):
                # имя_модуля.имя_функции(<параметры>)
                result += [self.properties_list[0].id + "." + self.properties_list[1].name]
            elif isinstance(self.properties_list[0], Identifier) \
                    and isinstance(self.properties_list[1], PropertyIndexed) \
                    and isinstance(self.properties_list[1].operand, FuncCall):
                # имя_модуля.имя_функции(<параметры>)[expr][expr]
                result += [self.properties_list[0].id + "." + self.properties_list[1].operand.name]
        for prop_element in self.properties_list:
            if isinstance(prop_element, FuncCall):
                result += get_func_list(prop_element.param_list)
            elif isinstance(prop_element, PropertyIndexed):
                if isinstance(prop_element.operand, FuncCall):
                    result += get_func_list(prop_element.operand.param_list)
                    result += get_func_list(prop_element.index_expr_list)
        return result
    def get_text(self):
        text = ""
        for op in self.properties_list:
            if text:
                text += "."
            text += op.get_text()
        return text

class PropertyIndexed:
    operand = None
    index_expr_list = None
    def __init__(self, operand, index_expr = None):
        self.operand = operand
        self.index_expr_list = [index_expr]
    def apnd(self, index_expr):
        self.index_expr_list += [index_expr]
    def get_func_list(self):
        res = []
        for index_expr in self.index_expr_list:
            res += index_expr.get_func_list()
        res += self.operand.get_func_list()
        return res
    def get_text(self):
        text = self.operand.get_text()
        for expr in self.index_expr_list:
            text += "[" + expr.get_text() + "]"
        return text


class Identifier:
    id = None
    def __init__(self, id):
        self.id = id
    def get_func_list(self):
        return []
    def get_text(self):
        return self.id


class FuncCall:
    name = None
    param_list = None
    def __init__(self, name, param_list):
        self.name = name
        self.param_list = param_list
    def get_func_list(self):
        result = [self.name]
        result += get_func_list(self.param_list)
        return result
    def get_text(self):
        text = self.name + "("
        not_first = False
        for param in self.param_list:
            if not_first:
                text += ", "
            text += param.get_text()
            not_first = True
        text += ")"
        return text


class Expr:
    pass


class GroupedExpr(Expr):
    expr = None
    def __init__(self, expr):
        self.expr = expr
    def get_func_list(self):
        return self.expr.get_func_list()
    def get_text(self):
        return "(" + self.expr.get_text() + ")"


class BinaryExpr(Expr):
    expr1 = None
    expr2 = None
    oper  = None
    def __init__(self, expr1, expr2, oper):
        self.expr1 = expr1
        self.expr2 = expr2
        self.oper = oper
    def get_func_list(self):
        return self.expr1.get_func_list() + self.expr2.get_func_list()
    def get_text(self):
        return self.expr1.get_text() + " " + self.oper + " " + self.expr2.get_text()


class QuestionExpr(Expr):
    expr = None
    first = None
    second = None
    def __init__(self, expr, first, second):
        self.expr = expr
        self.first = first
        self.second = second
    def get_func_list(self):
        return self.expr.get_func_list()\
               + self.first.get_func_list()\
               + self.second.get_func_list()
    def get_text(self):
        return "? (" + self.expr.get_text() + ", " + self.first.get_text() + ", " + self.second.get_text() + ")"


class NewExpr(Expr):
    id = None
    param_list = None
    def __init__(self, id = None, param_list = None):
        self.id = id
        self.param_list = param_list
    def get_func_list(self):
        res = []
        if self.param_list:
            res += get_func_list(self.param_list)
        return res
    def get_text(self):
        text = "Новый "
        if self.id:
            text += self.id + " ";
        text += "("
        if self.param_list:
            not_first = False
            for param in self.param_list:
                if not_first:
                    text += ", "
                text += param.get_text()
                not_first = True
        text += ")"
        return text


class UnaryExpr(Expr):
    op = None
    expr = None
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr
    def get_func_list(self):
        return self.expr.get_func_list()
    def get_text(self):
        return self.op + " " + self.expr.get_text()

## PREPROC

class PreprocIfElseStatement:
    if_expression = None
    if_statements = None
    else_collection = None
    def __init__(self, if_expression, if_statements, else_collection):
        self.if_expression = if_expression
        self.if_statements = if_statements
        self.else_collection = else_collection
    def get_func_list(self):
        return get_func_list(self.if_statements) + get_func_list(self.else_collection)
    def get_text(self):
        text = "#Если " + self.if_expression.get_text() + " Тогда" + "\n"
        incrase_indent()
        text += get_op_list_text(self.if_statements)
        decrase_indent()
        for else_st in self.else_collection:
            if else_st.condition:
                text += get_indent_spaces() + "#ИначеЕсли " + else_st.condition.get_text() + " Тогда"
            else:
                text += get_indent_spaces() + "#Иначе"
            text += "\n"
            incrase_indent()
            text += get_op_list_text(else_st.statements)
            decrase_indent()

        text += get_indent_spaces() + "#КонецЕсли"
        return text

class PreprocElse:
    condition = None
    statements = None
    def __init__(self, statements, condition = None):
        self.condition = condition
        self.statements = statements
    def get_func_list(self):
        return get_func_list(self.statements)

def get_preproc_expr_text(preproc_expr):
    if type(preproc_expr) == str:
        return preproc_expr
    else:
        return preproc_expr.get_text()


class PreprocExpr:
    expr = None
    brackets = None
    def __init__(self, expr, brackets):
        self.expr = expr
        self.brackets = brackets
    def get_text(self):
        text = ""
        if self.brackets:
            text += "("
        text += get_preproc_expr_text(self.expr)
        if self.brackets:
            text += ")"
        return text


class PreprocExprBinary:
    expr_left = None
    expr_right = None
    oper = None
    def __init__(self, expr_left, expr_right, oper):
        self.expr_left = expr_left
        self.expr_right = expr_right
        self.oper = oper
    def get_text(self):
        text = get_preproc_expr_text (self.expr_left)
        text += " " + self.oper + " "
        text += get_preproc_expr_text (self.expr_right)
        return text


class PreprocExprNot:
    expr = None
    def __init__(self, expr):
        self.expr = expr
    def get_func_list(self):
        return self.expr.get_func_list()
    def get_text(self):
        return "Не " + get_preproc_expr_text(self.expr)


## SIMPLE TYPES

class SimpleType:
    value = None
    def get_func_list(self):
        return []
    def get_text(self):
        return self.value

class Bool (SimpleType):
    def __init__(self, value):
        self.value = value

class Number (SimpleType):
    def __init__(self, value):
        self.value = value

class Date (SimpleType):
    def __init__(self, value):
        self.value = value

class Strings (SimpleType):
    def __init__(self, value):
        self.value = [value]
    def apnd(self, value):
        self.value += [value]
    def get_text(self):
        global _gl_indend
        text = '"'
        for ch in self.value[0]:
            if ch == '"':
                text += '""'
            elif ch == '\n':
                text += ch + (' '*_gl_indend) + "|"
            else:
                text += ch
        text += '"'
        return text

class Undefined (SimpleType):
    def __init__(self):
        pass
    def get_text(self):
        return "Неопределено"

class Empty (SimpleType):
    def __init__(self):
        pass
    def get_text(self):
        return ""
