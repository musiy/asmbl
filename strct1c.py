# -*- coding: utf-8 -*-

import re

# Localization
__gl_str_loc = None
def set_str_locale(loc):
    global __gl_str_loc
    __gl_str_loc = loc
def get_str_locale():
    return __gl_str_loc

def localize(loc):
    to_delete = set()
    for child, parent in __gl_owners.items():
        if not isinstance(child, Strings):
            continue
        if isinstance(parent, FuncCall) and parent.name.lower() == 'нстр':
            nstr_owner = get_owner(parent)
            nstr_owner.replace_obj(parent, child)
            to_delete.add(parent)
            child.value[0] = trunc_loc(child.value[0], loc)
    for subject in to_delete:
        del_owner_link(subject)
    pass

def trunc_loc(text, loc):
    template = r"\s*{loc}\s*=\s*'[^']*'".replace('{loc}', loc)
    regex = re.compile(template)
    match = regex.search(text, 0)
    if match:
        text = text[match.start():match.end()]
        text = text[text.find("'")+1:-1]
        return text
    return text

# Getting text
__gl_indend = 0

def set_indent(indent):
    global __gl_indend
    __gl_indend = indent

def get_indent_spaces():
    return __gl_indend * ' '

def incrase_indent():
    global __gl_indend
    __gl_indend += 4

def decrase_indent():
    global __gl_indend
    __gl_indend -= 4

def get_op_list_text(op_list, add_semicolon = True):
    global __gl_indend
    text = ""
    for op in op_list:
        text += get_indent_spaces() + op.get_text()
        if add_semicolon and not isinstance(op, PreprocIfElseStatement):
            text += ";"
        text += "\n"
    return text

def get_text(module):
    set_indent(0)
    return module.get_text()

def get_tokens_list(struct_list, obj_type, filter):
    func_list = []
    for x in struct_list:
        func_list += x.get_tokens_list(obj_type, filter)
    return func_list

# Глобальная переменная, содержащая соответствия объекта его владельцу
__gl_owners = dict()

def get_owner(subject):
    return __gl_owners.get(subject, None)

def del_owner_link(subject):
    global __gl_owners
    del __gl_owners[subject]

def set_owner(subject, owner, recursive = False):
    if not subject or isinstance(subject, str) or isinstance(subject, int):
        return
    if isinstance(subject, list):
        for x in subject:
            __gl_owners[x] = owner
            if recursive:
                x.set_owner(recursive)
    else:
        __gl_owners[subject] = owner
        if recursive:
            subject.set_owner(recursive)


def replace_object(subject_list, obj_from, obj_to):
    for i in range(len(subject_list)):
        if subject_list[i] == obj_from:
            subject_list[i] = obj_to

class Module:
    global_vars_list = None
    proc_funcs_list = None
    statements_list = None
    def __init__(self, statements_list, proc_funcs_list = None, global_vars_list = None):
        self.statements_list = statements_list
        self.proc_funcs_list = proc_funcs_list
        self.global_vars_list = global_vars_list
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.statements_list, self, recursive)
        set_owner(self.proc_funcs_list, self, recursive)
        set_owner(self.global_vars_list, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.statements_list, obj_from, obj_to)
        replace_object(self.proc_funcs_list, obj_from, obj_to)
        replace_object(self.global_vars_list, obj_from, obj_to)
    def get_text(self):
        text = get_op_list_text(self.global_vars_list) + '\n'
        text += get_op_list_text(self.proc_funcs_list, False) + '\n'
        text += get_op_list_text(self.statements_list) + '\n'
        return text

class VariablesDeclaration:
    directive = None
    vars_list = None
    def __init__(self, vars_list, directive = None):
        self.vars_list = vars_list
        self.directive = directive
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.vars_list, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.vars_list, obj_from, obj_to)
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
    def set_owner(self, recursive = False):
        pass
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.vars_list, self, recursive)
        set_owner(self.body, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.vars_list, obj_from, obj_to)
        if self.body == obj_from:
            self.body = obj_to
    def get_text(self):
        text = ''
        if self.directive:
            text += self.directive + "\n"
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
    def set_owner(self, recursive = False):
        pass
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.vars_decls_list, self, recursive)
        set_owner(self.statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.vars_decls_list, obj_from, obj_to)
        replace_object(self.statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return get_tokens_list(self.statements, obj_type, filter)
    def get_text(self):
        text = get_op_list_text(self.vars_decls_list)
        if self.vars_decls_list:
            text += "\n"
        text += get_op_list_text(self.statements)
        return text

class Statement:
    def __init__(self): pass

class StatementAssignment(Statement):
    # expression like 'a = 1 + 2'
    property = None
    expr = None
    def __init__(self, property, expr = None):
        self.property = property
        self.expr = expr
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.property, self, recursive)
        set_owner(self.expr, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.property == obj_from:
            self.property = obj_to
        if self.expr == obj_from:
            self.expr = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.property.get_tokens_list(obj_type, filter) + self.expr.get_tokens_list(obj_type, filter)
    def get_text(self):
        return self.property.get_text() + " = " + self.expr.get_text()


class StatementFuncCall(Statement):
    statement = None
    def __init__(self, statement):
        self.statement = statement
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.statement, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.statement == obj_from:
            self.statement = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.statement.get_tokens_list(obj_type, filter)
    def get_text(self):
        return self.statement.get_text()

class TryStatement(Statement):
    try_statements = None
    except_statements = None
    def __init__(self, try_statements, except_statements):
        self.try_statements = try_statements
        self.except_statements = except_statements
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.try_statements, self, recursive)
        set_owner(self.except_statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.try_statements, obj_from, obj_to)
        replace_object(self.except_statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return get_tokens_list(self.try_statements, obj_type, filter) \
               + get_tokens_list(self.except_statements, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.statement, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.statement == obj_from:
            self.statement = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.statement.get_tokens_list(obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.if_expression, self, recursive)
        set_owner(self.if_statements, self, recursive)
        set_owner(self.else_collection, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.if_expression == obj_from:
            self.if_expression = obj_to
        replace_object(self.if_statements, obj_from, obj_to)
        replace_object(self.else_collection, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return self.if_expression.get_tokens_list(obj_type, filter) \
               + get_tokens_list(self.if_statements, obj_type, filter) \
               + get_tokens_list(self.else_collection, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.condition, self, recursive)
        set_owner(self.statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.condition == obj_from:
            self.condition = obj_to
        replace_object(self.statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        result = []
        if (self.condition):
            result += self.condition.get_tokens_list(obj_type, filter)
        return result + get_tokens_list(self.statements, obj_type, filter)

class ForEachBlock(Statement):
    id_name = None
    expression = None
    statements = None
    def __init__(self, id_name, expression, statements):
        self.id_name = id_name
        self.expression = expression
        self.statements = statements
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expression, self, recursive)
        set_owner(self.statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expression == obj_from:
            self.expression = obj_to
        replace_object(self.statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expression.get_tokens_list(obj_type, filter) \
               + get_tokens_list(self.statements, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expression_start, self, recursive)
        set_owner(self.expression_end, self, recursive)
        set_owner(self.statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expression_start == obj_from:
            self.expression_start = obj_to
        if self.expression_end == obj_from:
            self.expression_end = obj_to
        replace_object(self.statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expression_start.get_tokens_list(obj_type, filter) \
               + self.expression_end.get_tokens_list(obj_type, filter) \
               + get_tokens_list(self.statements, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expression, self, recursive)
        set_owner(self.statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expression == obj_from:
            self.expression = obj_to
        replace_object(self.statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expression.get_tokens_list(obj_type, filter) \
               + get_tokens_list(self.statements, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.second_param, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.second_param == obj_from:
            self.second_param = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        result = []
        if self.second_param:
            result += self.second_param.get_tokens_list(obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.properties_list, self, recursive)
    def append(self, property):
        self.properties_list += [property]
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.properties_list, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        result = []
        # расчитываем на вызов <имя модуля>.<вызов функции>
        if obj_type == "function" and len(self.properties_list) > 1:
            # вызов вида:
            #   ИмяОбщегоМодуля.ПолучитьРеквизитОбъекта().ИмяСвойство
            if isinstance(self.properties_list[0], Identifier) and self.properties_list[1].is_function():
                # имя_модуля.имя_функции(<параметры>)
                result += [(self, self.properties_list[0].id + "." + self.properties_list[1].get_name())]
            else:
                for prop_element in self.properties_list:
                    if prop_element.is_function():
                        result += [(self, prop_element.get_name())]

        elif obj_type == "id" and filter:
            # для идентификаторов обязательно должен быть установлен фильтр
            id_was_found = False
            # полный путь обращения к идентификатору
            id_text = ""
            for prop_element in self.properties_list:
                if isinstance(prop_element, Identifier) and prop_element.id.lower() in filter:
                    id_was_found = True
                if id_text:
                    id_text += "."
                id_text += prop_element.get_name()
            if id_was_found:
                result += [(self, id_text)]

        for prop_element in self.properties_list:
            # получаем обращения к функциям из параметров функций и индексов
            if isinstance(prop_element, FuncCall):
                result += get_tokens_list(prop_element.param_list, obj_type, filter)
            elif isinstance(prop_element, PropertyIndexed):
                if isinstance(prop_element.operand, FuncCall):
                    result += get_tokens_list(prop_element.operand.param_list, obj_type, filter)
                result += get_tokens_list(prop_element.index_expr_list, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.operand, self, recursive)
        set_owner(self.index_expr_list, self, recursive)
    def apnd(self, index_expr):
        self.index_expr_list += [index_expr]
    def replace_obj(self, obj_from, obj_to):
        if self.operand == obj_from:
            self.operand = obj_to
        replace_object(self.index_expr_list, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        result = []
        for index_expr in self.index_expr_list:
            result += index_expr.get_tokens_list(obj_type, filter)
        result += self.operand.get_tokens_list(obj_type, filter)
        return result
    def get_text(self):
        text = self.operand.get_text()
        for expr in self.index_expr_list:
            text += "[" + expr.get_text() + "]"
        return text
    def get_name(self):
        return self.operand.get_name()
    def set_name(self, name):
        self.operand.set_name(name)
    def is_function(self):
        return self.operand.is_function()


class FuncCall:
    name = None
    param_list = None
    def __init__(self, name, param_list):
        self.name = name
        self.param_list = param_list
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.param_list, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.param_list, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        result = []
        if obj_type == "function":
            result = [(self, self.name)]
        result += get_tokens_list(self.param_list, obj_type, filter)
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
    def get_name(self):
        return self.name
    def set_name(self, name):
        self.name = name
    def is_function(self):
        return True


class Identifier:
    id = None
    def __init__(self, id):
        self.id = id
    def set_owner(self, recursive = False):
        pass
    def get_tokens_list(self, obj_type, filter = set()):
        result = []
        if obj_type == "id" and filter and self.id.lower() in filter:
            result = [(self, self.id)]
        return result
    def get_text(self):
        return self.id
    def get_name(self):
        return self.id
    def set_name(self, name):
        self.id = name
    def is_function(self):
        return False


class Expr:
    pass


class GroupedExpr(Expr):
    expr = None
    def __init__(self, expr):
        self.expr = expr
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr == obj_from:
            self.expr = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expr.get_tokens_list(obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr1, self, recursive)
        set_owner(self.expr2, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr1 == obj_from:
            self.expr1 = obj_to
        if self.expr2 == obj_from:
            self.expr2 = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expr1.get_tokens_list(obj_type, filter) + self.expr2.get_tokens_list(obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr, self, recursive)
        set_owner(self.first, self, recursive)
        set_owner(self.second, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr == obj_from:
            self.expr = obj_to
        if self.first == obj_from:
            self.first = obj_to
        if self.second == obj_from:
            self.second = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expr.get_tokens_list(obj_type, filter)\
               + self.first.get_tokens_list(obj_type, filter)\
               + self.second.get_tokens_list(obj_type, filter)
    def get_text(self):
        return "? (" + self.expr.get_text() + ", " + self.first.get_text() + ", " + self.second.get_text() + ")"


class NewExpr(Expr):
    id = None
    param_list = None
    def __init__(self, id = None, param_list = None):
        self.id = id
        self.param_list = param_list
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.param_list, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        replace_object(self.param_list, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        res = []
        if self.param_list:
            res += get_tokens_list(self.param_list, obj_type, filter)
        return res
    def get_text(self):
        text = "Новый"
        if self.id:
            text += " " + self.id ;
        if self.param_list:
            text += " ("
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr == obj_from:
            self.expr = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expr.get_tokens_list(obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.if_expression, self, recursive)
        set_owner(self.if_statements, self, recursive)
        set_owner(self.else_collection, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.if_expression == obj_from:
            self.if_expression = obj_to
        replace_object(self.if_statements, obj_from, obj_to)
        replace_object(self.else_collection, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return get_tokens_list(self.if_statements, obj_type, filter) \
               + get_tokens_list(self.else_collection, obj_type, filter)
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.condition, self, recursive)
        set_owner(self.statements, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.condition == obj_from:
            self.condition = obj_to
        replace_object(self.statements, obj_from, obj_to)
    def get_tokens_list(self, obj_type, filter = set()):
        return get_tokens_list(self.statements, obj_type, filter)

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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr == obj_from:
            self.expr = obj_to
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
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr_left, self, recursive)
        set_owner(self.expr_right, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr_left == obj_from:
            self.expr_left = obj_to
        if self.expr_right == obj_from:
            self.expr_right = obj_to
    def get_text(self):
        text = get_preproc_expr_text (self.expr_left)
        text += " " + self.oper + " "
        text += get_preproc_expr_text (self.expr_right)
        return text


class PreprocExprNot:
    expr = None
    def __init__(self, expr):
        self.expr = expr
        self.set_owner()
    def set_owner(self, recursive = False):
        set_owner(self.expr, self, recursive)
    def replace_obj(self, obj_from, obj_to):
        if self.expr == obj_from:
            self.expr = obj_to
    def get_tokens_list(self, obj_type, filter = set()):
        return self.expr.get_tokens_list(obj_type, filter)
    def get_text(self):
        return "Не " + get_preproc_expr_text(self.expr)


## SIMPLE TYPES

class SimpleType:
    value = None
    def get_tokens_list(self, obj_type, filter = set()):
        return []
    def set_owner(self, recursive = False):
        pass
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
        return self.format_1c_str(self.value[0])
    def format_1c_str(self, origin_text):
        text = '"'
        for ch in origin_text:
            if ch == '"':
                text += '""'
            elif ch == '\n':
                text += ch + get_indent_spaces() + "|"
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
