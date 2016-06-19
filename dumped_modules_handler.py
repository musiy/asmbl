import os.path
import os

def get_forms_properties(path, extproc_name):
    form_props = dict()
    dump_files_list = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for file_name in dump_files_list:
        if file_name.lower().startswith(('Обработка.'+extproc_name+'.Форма').lower()):
            form_name = file_name.split('.')[3]
            is_managed = not form_name.endswith("Обычная")
            form_text = open('dump/' + file_name, encoding='utf-8').read()
            form_props[form_name] = {'text_origin': form_text,
                                     'is_managed': is_managed,
                                     'file_name': file_name}
    return form_props

def get_modules_properties(path, extproc_name):
    common_modules_props = dict()
    dump_files_list = [f for f in os.listdir('dump') if os.path.isfile(os.path.join('dump', f))]
    for full_file_name in dump_files_list:
        if full_file_name.startswith('ОбщийМодуль'):
            module_name = full_file_name.split('.')[1]
            #if module_name.lower().find(extproc_name.lower()) == -1:
                # общие модули должны содержать в названии имя обработки
                #continue
            is_client = False
            is_server = False
            is_client_server = False
            
            if module_name.lower().find("клиентсервер") >= 0:
                is_client_server = True
            elif module_name.lower().find("клиент") >= 0:
                is_client = True
            else:
                is_server = True

            text_origin = open('dump/'+full_file_name, encoding='utf-8').read()
            common_modules_props[module_name] = {'text_origin': text_origin,
                                                 'is_client': is_client,
                                                 'is_server': is_server,
                                                 'is_client_server': is_client_server,
                                                 'file_name': full_file_name}
    return common_modules_props
