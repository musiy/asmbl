UNPACK_DIR_PATH = r'E:\RomanMusiy\Assembly1C\out\unpack'
COMMON_MODULE_ID = "0fe48980-252d-11d6-a3c7-0050bae0a776"

def process1cTree(str, list, *, pos = 1):
    """Рекурсивно обходит описание данных в формате 1С и составляет список из них.
    Каждый блок данных обрамляется в фигурные скобки: {<данные>}
    Каждый блок данных состоит из произвольного числа элементов: строки, числа идентфикаторы, либо другие блоки
    @param str строка содержащая блок данных
    @param pos позиция в строке для продолжения разбора
    @param list список в который следует добавить элементы на текущем уровне разбора
    @return позиция закрывающейся скобки на текущем уровне разбора
    """
    token = ''
    while True:
        pos += 1
        if str[pos] == '{':
            subList=[]
            list.append(subList)
            pos = process1cTree(str, subList, pos = pos)
        elif str[pos] == '}':
            list.append(token.strip())
            return pos
        elif str[pos] == ',':
            if token:
                list.append(token.strip())
            token = ''
        else:
            token += str[pos]

def loadDataFile(fileName):
    return open(UNPACK_DIR_PATH + "\\" + fileName, encoding='utf-8').read().replace('\n', '')

# Файл root содержит идентификатор файла с описанием конфигурации
rootList = []
process1cTree(loadDataFile("root"), rootList)

# Считывание файла с конфигурацией
confData = loadDataFile(rootList[1])
pos = confData.find(COMMON_MODULE_ID)
if pos == -1:
    raise Exception("В файле описания структуры метаданных не найдены идентификатор блока общих модулей")
commonModulesList = []
process1cTree(confData, commonModulesList, pos = (pos - 1))

for moduleId in commonModulesList[2:]:
    print(moduleId)
