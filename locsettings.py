# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET

def get_localization_settings(loc):
    tree = ET.parse( r'Localization_3_5_RU.xml' );
    root = tree.getroot()
    result = dict()
    for term_element in root:
        for tr_element in term_element:
            if tr_element.attrib['build'] != loc:
                continue
            tr_name = term_element.attrib['name']
            if tr_element.attrib['loc']:
                tr_name += "_" + tr_element.attrib['loc']
            result[tr_name] = tr_element.text
    return result

if __name__ == '__main__':
    loc = get_localization_settings('ru')
    pass