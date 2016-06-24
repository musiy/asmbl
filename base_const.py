import collections

APP_TYPE_MANAGED = 'managed'
APP_TYPE_ORDINARY = 'ordinary'
FORM_MANAGED = 'FormManaged'
FORM_ORDINARY = 'FormOrdinary'
COMMON_MODULE = 'CommonModule'

MoveConfiguration = collections.namedtuple('MoveConfiguration', ['primary_form_config', 'secondary_forms_config'])
PrimaryFormConf = collections.namedtuple('PrimaryFormConf', ['functions_to_move', 'export_functions'])
SecondaryFuncs = collections.namedtuple('SecondaryFuncs', ['functions_to_move_dict', 'replace_calls_to_primary_module',
                                        'wrapper_calls','export_functions'])
