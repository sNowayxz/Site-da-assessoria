import json
import os
import traceback

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from function_bd import integridade_bd, save_json
from system.logger import log_grava

# Diretório Raiz de execução
path_dir = os.getcwd()


def fcn_curso_sigla_nome(self):
    """
    Atualiza o arquivo 'curso_sigla_nome.json' 
    Não é necessário nenhum parâmetro
    """
    path_file = os.getcwd()+'\\BD\\cursos\\curso_sigla_nome.json'
    if os.path.isfile(path_file):
        with open(path_file, encoding='utf-8') as json_file:
            self.sigla_nome = json.load(json_file)
    else:
        self.sigla_nome = {}

def fnc_modulo_novo(self):
    """
    Salva um novo módulo
    """
    
    path_file = path_dir+'\\BD\\atividades\\modulo.json'

    with open(path_file, encoding='utf-8') as json_file:
        data_modulo = json.load(json_file)

    novo_modulo = (self.ui.input_modulo_novo.text())

    if not novo_modulo in data_modulo: 
        data_modulo[novo_modulo] = {} 
        data_modulo[novo_modulo]['SITUAÇÃO'] = 'FECHADO'
    
    # Ordena o dicionário pelas chaves em ordem alfabética
    dados_ordenados = {chave: data_modulo[chave] for chave in sorted(data_modulo)}
    save_json(dados_ordenados,path_file)



def fcn_modulo_fechar(self):
    """
    Fecha o módulo selecionado na tela de atividades
    """
    path_file = path_dir+'\\BD\\atividades\\modulo.json'
    self.modulo = self.ui.menu_modulos.currentText()

    with open(path_file, encoding='utf-8') as json_file:
        data_modulo = json.load(json_file)
    
    data_modulo[self.modulo]['SITUAÇÃO'] = 'FECHADO'

    save_json(data_modulo,path_file)

def fcn_modulo_abrir(self):
    """
    Fecha o módulo selecionado na tela de atividades
    """
    from function import verifica_pastas
    
    path_file = path_dir+'\\BD\\atividades\\modulo.json'
    path_atividades = path_dir+'\\BD\\atividades'
    path_papiron = os.path.join(os.path.expanduser("~"), "Desktop\\Papiron")
    self.modulo = self.ui.menu_modulos.currentText()

    with open(path_file, encoding='utf-8') as json_file:
        data_modulo = json.load(json_file)
    
    data_modulo[self.modulo]['SITUAÇÃO'] = 'ABERTO'

    path_modulo_bd = path_atividades+'\\'+self.modulo.replace('/','')
    path_modulo_desktop = path_atividades+'\\'+self.modulo.replace('/','')
    verifica_pastas(path=path_modulo_bd)
    verifica_pastas(path=path_modulo_desktop)
    # if not os.path.isdir(path_modulo):
    #     os.mkdir(path_modulo)
    
    save_json(data_modulo,path_file)

def fcn_modulo_excluir(self):
    """
    Exclui o módulo selecionado na tela de atividades
    """
    path_file = path_dir+'\\BD\\atividades\\modulo.json'
    path_atividades = path_dir+'\\BD\\atividades'
    self.modulo = self.ui.menu_modulos.currentText()

    with open(path_file, encoding='utf-8') as json_file:
        data_modulo = json.load(json_file)
    try:
        del(data_modulo[self.modulo])
    except KeyError:
        for mod in data_modulo:
            if data_modulo[mod]['SITUAÇÃO'] == 'ABERTO':
                self.ui.menu_modulos.setCurrentText(mod)
                break
    save_json(data_modulo,path_file)

def fcn_modulos(self):
    """
    Verifica os módulos cadastrados
    """

    path_file = path_dir+'\\BD\\atividades\\modulo.json'

    with open(path_file, encoding='utf-8') as json_file:
        data_modulo = json.load(json_file)

    for modulo in data_modulo:
        modulo_atual = modulo
        self.modulo = modulo
        self.modulo_situacao = data_modulo[modulo]['SITUAÇÃO']
        # Se encontrar um Aberto este será o atual, senão será o último mesmo que esteja fechado
        if self.modulo_situacao == 'ABERTO':

            break
    
    # print(13 , self.modulo)
    self.lista_modulos = []
    for modulo in data_modulo:
        self.lista_modulos.append(modulo)

    # Altera na Tela de Atividades itens
    # print("preparar!")
    # self.ui.menu_modulos.clear()
    # print(15 , l_modulos)
    # self.ui.menu_modulos.addItems(l_modulos)
    # print(16)
    # self.ui.menu_modulos.setCurrentText(modulo_atual)
    # print(17)
    return None

def fnc_modulo_atual(self):
    import time
    self.modulo = self.ui.menu_modulos.currentText()
    return None

def fnc_verifica_modulo_selecionado(self):
    
    self.modulo = self.ui.menu_modulos.currentText()

    path_file = path_dir+'\\BD\\atividades\\modulo.json'
    with open(path_file, encoding='utf-8') as json_file:
        data_modulo = json.load(json_file)

    self.modulo_situacao = data_modulo[self.modulo]['SITUAÇÃO']
    self.ui.l_situacao_modulo.setText(self.modulo_situacao)
        
    return None

def lista_atividades(self):

    # Atualiza arquivo sigla_nome  
    fcn_curso_sigla_nome(self)

    keys_atividade =  ["STATUS_ATIVIDADE","ID_URL","DT_INICIO", "DT_FIM","LISTA_ID_URL"]
    self.modulos = []
    disciplinas = []
    lista_tela = []
    try:
        for sigla in self.sigla_nome :
            #Verifica a integridade do BD da curso (sigla)
            data , path_file = integridade_bd(sigla,self.modulo)
            if data:
                for curso in data:
                    # print(curso)
                    for disciplina in data[curso]:
                        # print("   "+disciplina)
                        for modulo in data[curso][disciplina]:
                            # print("   "+modulo+" "+self.modulo)
                            if not modulo in self.modulos:
                                self.modulos.append(modulo)
                            for atividade in data[curso][disciplina][modulo]["ATIVIDADE"]:
                                # print("       "+atividade)
                                if atividade not in keys_atividade:
                                    for questao in data[curso][disciplina][modulo]["ATIVIDADE"][atividade]:
                                        if questao not in keys_atividade:
                                            # Verfica se a Atividade foi publicada
                                            if data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]['ID_URL']:
                                                situacao = "ok"
                                            else:
                                                situacao = "a Enviar"
                                            
                                            gabarito = None
                                            
                                            if data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]['ESTILO'] == "QUESTIONARIO":
                                                if 'GABARITO_OK' in data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]:
                                                    # print("GAB:", data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]["GABARITO"])
                                                    # verifica se tem Gabarito
                                                    if data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]["GABARITO_OK"] == "OK":
                                                        gabarito = "ok"
                                                    else:
                                                        gabarito = "rastreado"
                                                else:
                                                    gabarito = "a rastrear"
                                            else:
                                                gabarito = "n/a"
                                            
                                            
                                            # if (disciplina not in disciplinas) and (data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]['ESTILO'] == "QUESTIONARIO"):
                                            disc_ativ = disciplina+" - "+atividade
                                            if disc_ativ not in lista_tela:
                                                lista_tela.append(disc_ativ)
                                                disciplinas.append(disciplina)
                                                    
                                                # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
                                                rowPosition = self.ui.tableWidget.rowCount()

                                                # Insere uma nova linha na tabela
                                                self.ui.tableWidget.insertRow(rowPosition)

                                                # Cria o QTableWidgetItem para ser inserido na Widgettable, não se insere o elemento cru, como uma "str"
                                                item_sigla = QTableWidgetItem(sigla)
                                                # # if (gabarito == "n/a"):
                                                # print(disciplina+" - "+atividade)
                                                item_disciplina = QTableWidgetItem(disc_ativ)
                                                item_situacao = QTableWidgetItem(situacao)
                                                item_gabarito = QTableWidgetItem(gabarito)
                    
                                                # centraliza H e V o widget no item, não entendi a segunda sequência
                                                item_sigla.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                                                item_disciplina.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                                                item_situacao.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                                item_gabarito.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                                                item_sigla.setFlags(item_sigla.flags() ^ Qt.ItemFlag.ItemIsSelectable)
                                                item_disciplina.setFlags(item_disciplina.flags() ^ Qt.ItemFlag.ItemIsSelectable)
                                                item_situacao.setFlags(item_situacao.flags() ^ Qt.ItemFlag.ItemIsSelectable)
                                                item_gabarito.setFlags(item_situacao.flags() ^ Qt.ItemFlag.ItemIsSelectable)

                                                # Insere dados na tabela
                                                self.ui.tableWidget.setItem(rowPosition,0, item_sigla)
                                                self.ui.tableWidget.setItem(rowPosition,1, item_disciplina)
                                                self.ui.tableWidget.setItem(rowPosition,2, item_situacao)
                                                self.ui.tableWidget.setItem(rowPosition,3, item_gabarito)
    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print("ALERTA:", msg)
        log_grava(msg="[TELA ATIVIDADES - INICIALIZAÇÃO]: "+str(msg))


def progresso_lista(self,texto:str):
    """
    Adicona o registro *texto* no histórico

    ### Args:

        - texto : str - define o que será inserido no ListWidget
    """
    item = QListWidgetItem(texto)
    self.ui.tabela_registro.addItem(item)
    self.ui.tabela_registro.scrollToBottom()
