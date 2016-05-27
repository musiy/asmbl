
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
    def __init__(self, directive, vars_list):
        self.directive = directive
        self.vars_list = vars_list

class VarDesc:
    name = None
    export = None
    def __init__(self, name, export = False):
        self.name = name
        self.export = export

class Statement:
    pass

class StatementSimple(Statement):
    # for expression like 'a = 1 + 2' and 'f()'
    property = None
    expr = None
    def __init__(self, property, expr = None):
        self.property = property
        self.expr = expr

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

class Strings:
    pass

class StringsBase(Strings):
    value = None
    def __init__(self, value):
        self.value = value


class StringsSeq(Strings):
    strings_left  = None
    strings_right = None
    def __init__(self, strings_left, strings_right):
        self.strings_left = strings_left
        self.strings_right = strings_right

class Empty:
    pass
