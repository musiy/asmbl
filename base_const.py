# -*- coding: utf-8 -*-

import collections
import logging
from os import getlogin
from platform import node as comp_name

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

BuildParams = collections.namedtuple('ProcessingParams', ['object_name',
                                                          'main_managed_form',
                                                          'managed_forms',
                                                          'ordinary_forms'])

__ENV_DESC = {'user': getlogin(), 'comp': comp_name()}
__LOGGER = logging.getLogger('epfcomp')

def __init_logging():
    formatter = logging.Formatter('%(asctime)s %(comp)s(%(user)s)- %(levelname)s: %(message)s')
    # Вывод данных логирования в консоль
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    __LOGGER.addHandler(ch)
    __LOGGER.setLevel(logging.INFO)

def log(msg, *args):
    __LOGGER.info(msg, *args, extra=__ENV_DESC)

__init_logging()

if __name__ == '__main__':
    log('Пример сообщения логирования')
