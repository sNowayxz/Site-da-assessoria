import json
import os


def verifica_json(path_file:str) -> dict:
    """
    Verifica se o arquivo JSON existe, caso não existir cria no path indicado.

    Return -> dict
    """
    if not os.path.isfile(path_file):
        data = {}
        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(data, f ,ensure_ascii=False)
    
    else:
        with open(path_file, encoding='utf-8') as json_file:
            data = json.load(json_file)
           
    return data

def open_file(path_file):
    if not os.path.isfile(path_file):
        file = open(path_file, 'w', encoding='utf-8')
        return file
    else:
        file = open(path_file, 'a', encoding='utf-8')
        return file
