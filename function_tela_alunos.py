import json
import os
import time


def fcn_lista_alunos_cadastrados(self):
    from json.decoder import JSONDecodeError
    path_file = os.getcwd()+'\\BD\\alunos\\dados_aluno_ra.json'
    cont = 4
    while cont:
        try:
            if os.path.isfile(path_file):
                with open(path_file, encoding='utf-8') as json_file:
                    self.dados_alunos = json.load(json_file)
            else:
                self.dados_alunos = {}
            break
        except JSONDecodeError:
            cont -=1
            time.sleep(3)
            if not cont:
                raise JSONDecodeError

def fcn_lista_alunos_mensalistas(self):
    from json.decoder import JSONDecodeError
    path_file = os.getcwd()+'\\BD\\alunos\\dados_aluno_mensalista.json'
    cont = 4
    while cont:
        try:
            if os.path.isfile(path_file):
                with open(path_file, encoding='utf-8') as json_file:
                    self.dados_alunos = json.load(json_file)
            else:
                self.dados_alunos = {}
            break
        except JSONDecodeError:
            cont -=1
            time.sleep(3)
            if not cont:
                raise JSONDecodeError

    # print("dados alunos:", self.dados_alunos)

def fcn_lista_cursos_cadastrados(self):
    path_file = os.getcwd()+'\\BD\\cursos\\curso_nome.json'
    try:
        with open(path_file, encoding='utf-8') as json_file:
            self.curso_nome = json.load(json_file)
    except:
        self.curso_nome = {}
    
