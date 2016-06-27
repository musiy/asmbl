# -*- coding: utf-8 -*-

import collections

APP_TYPE_MANAGED = 'managed'
APP_TYPE_ORDINARY = 'ordinary'

FORM_MANAGED = 'FormManaged'
FORM_ORDINARY = 'FormOrdinary'
COMMON_MODULE = 'CommonModule'
DATA_PROCESSOR = 'DataProcessor'

MoveConfiguration = collections.namedtuple('MoveConfiguration', ['primary_form_config', 'secondary_forms_config'])

PrimaryModuleConfiguration = collections.namedtuple('PrimaryModuleConfiguration',
                                                    ['functions_to_move',
                                                     'export_functions',
                                                     'dp_module_chain'])

SecondaryFormsConfiguration = collections.namedtuple('SecondaryFormsConfiguration',
                                                     ['functions_to_move_dict',
                                                      'replace_calls_to_primary_module',
                                                      'wrapper_calls',
                                                      'export_functions'])
