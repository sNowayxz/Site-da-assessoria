import json
import os
import time
import traceback

from PyQt6 import QtCore
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from selenium.common.exceptions import (
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
)

from class_papiron.class_error import (
    AlunoNotScrappedError,
    CPFError,
    FileLoginError,
    SenhaError,
    StatusScrappedError,
)

from function import (
    situacao_aluno_mensalista,
    verifica_aviso,    
    iniciar_sesssao_chrome,
    login,
)

from function_bd import integridade_bd
from system.chrome import chrome_encerra
from system.logger import log_grava
from function_system import verifica_json
from function_tela_alunos import (
    fcn_lista_alunos_mensalistas,
    fcn_lista_cursos_cadastrados,
)
from function_tela_atividades import fcn_curso_sigla_nome
from function_window import fcn_w_preenche_tela_mensalistas
from class_papiron.class_dados_aluno import Aluno, Mensalista

path_dir = os.getcwd()

class Rotinas_AtualizaMensalistas(QObject):
    finished = pyqtSignal()
    updateProgress = pyqtSignal(int,str)
    updateTela = pyqtSignal()
    updateBarra = pyqtSignal(int,int,str,str)

    def __init__(self, ui, config) :

        super().__init__()

        self.ui = ui
        self.config = config

    def insere_label(self,text_nome, info):
        self.ui.l_nome_aluno.setText(text_nome)
        self.ui.l_nome_aluno.setStyleSheet("font-weight: bold;")
        self.ui.l_info_progresso.setText(info)
    
    def run_atualizar_dados_alunos(self):
        from urllib3.exceptions import MaxRetryError
       
        try:
            # Carrega o arquivo JSON de LOGINS/SENHAS
            path_file_logins = os.path.abspath(os.getcwd())+"\\BD\\alunos\\contas_mensalista.json"
            contas  = verifica_json(path_file_logins)
            n_contas = len(contas)
            print(f"    Total de contas: {n_contas}\n")

            # Carrega arquivo JSON de Alunos
            path_file_alunos = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_mensalista.json"
            alunos = verifica_json(path_file_alunos)

            # Carrega o arquivo JSON de Cursos
            # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_nome.json"
            # cursos = verifica_json(path_file_curso)
                      
            if not n_contas:
                raise FileLoginError

            # Inicializando
            driver = None
        
        except FileLoginError:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "[FALHA]: Arquivo de LOGINS está vazio.","Erro de Logins",0)
            self.finished.emit()
            return None

        cont = 0
        for i, usuario in enumerate(contas):

            try: 
                # self.updateTela.emit()
                print(">>>>>>>>>          <<<<<<<<<\n\n\n\nLogin Aluno:" + usuario, "Inicializando\n")
                # self.updateBarra.emit(1,n_contas,"RA Aluno: " + usuario,"Inicializando")
                # self.insere_label("RA Aluno: " + usuario, "Localizando informações")

                ra_login = usuario.replace("-","").replace(".","").replace("/","")
                tipo = True if len(ra_login) <= 9 else False

                # Verifica se o login é CPF ou RA
                # Se for CPF passa para o próximo
                if not tipo:
                    print("\n\nLogin pelo CPF passa para outro\n\n")
                    raise CPFError

                # Verifica se RA já consta no DICT que foi varrido
                if ra_login in alunos:
                    
                    # Verifica se atualiza todos os logins ou apenas novos
                    aluno_nome = alunos[ra_login]["NOME"]
                    if self.config['cb_atualizar_novos_cadastros']:
                        print(f"        Passa para o próximo aluno, pois {aluno_nome} já está no BD")
                        # Levanta erro, pois serão feitos scrappeds apenas em alunos novos
                        raise StatusScrappedError

                    # Caso ocorra algum erro em obter novamente estes dados
                    # logo a frente
                    aluno_ra = alunos[ra_login]["RA"]
                    aluno_curso = alunos[ra_login]["CURSO"]

                    print(f"    >>> Atualizar:  {aluno_ra} - {aluno_nome}")
                    # self.updateBarra.emit(0,n_contas,aluno_nome,"Atualizando login")

                else:
                    #Novo login
                    aluno_nome = ra_login
                    print(f"    >>> Novo Login:  {ra_login}")
                    # self.updateBarra.emit(0,n_contas,ra_login,"Novo Login")

                # Inicia a sessão somente se fechou a anterior, completou os dados do aluno
                # self.updateBarra.emit(0,n_contas,aluno_nome,"Instanciando Chromedriver")
                if driver:
                    driver=chrome_encerra(driver)
                driver = iniciar_sesssao_chrome()
                
                if not driver:
                    print("CHROME: Sessão não criada!!!")
                    raise SessionNotCreatedException
                    
                # Realiza o login no usuário do FOR
                driver = login(driver,contas[usuario]['RA'],contas[usuario]['password'])

                if not driver:
                    print("CHROME: Sessão não criada!!!")
                    raise SessionNotCreatedException
                
                # Verificações iniciais de login
                verifica_aviso(driver)

                # Cria instância do aluno
                aluno = Mensalista(driver)
                aluno_nome = aluno.nome
                aluno_ra = aluno.ra
                aluno_curso = aluno.curso
                aluno_atividades = aluno.atividades
                print("   - Obteve dados do aluno:", aluno.nome)


                # Scrapped dos dados do curso e disciplinas
                print(f"   >> Aluno: {aluno_nome} - {aluno_ra} - {aluno_curso}")
                # disciplinas  = lista_disciplinas(driver)
                # self.updateBarra.emit(0,n_contas,aluno_nome,"Gravando dados do Aluno")
                
                print("vai entrar")
                # if aluno_atividades:
                situacao_aluno_mensalista(
                        aluno_nome=aluno_nome,
                        ra=ra_login,
                        senha=contas[usuario],
                        curso=aluno_curso,
                        atividades = aluno_atividades                
                    )

                driver = chrome_encerra(driver)
                
            except (KeyError,TypeError,AttributeError, SessionNotCreatedException, MaxRetryError) as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("ERRO: passou para o seguinte - FALHA SESSÃO\n"+msg)
                situacao_aluno_mensalista(aluno_nome=contas[usuario]['nome'] ,ra=ra_login,senha=contas[usuario]['password'],senha_ok="FALHA DE SESSÃO")
                driver = chrome_encerra(driver)
                # continue

            except AlunoNotScrappedError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("ERRO: passou para o seguinte!\n"+msg)
                situacao_aluno_mensalista(ra=ra_login, senha=contas[usuario], senha_ok="SENHA FALHOU")
                driver = chrome_encerra(driver)
            
            except StatusScrappedError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("ERRO: Aluno já está na BD!\n"+msg)
                # Aluno já está no BD, pule para o seguinte
                # continue

            except SenhaError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f" {contas[usuario]['nome']} - Erro na senha, faça o seguinte\n"+msg)
                situacao_aluno_mensalista(
                    aluno_nome=contas[usuario]['nome'],
                    ra=ra_login, 
                    senha=contas[usuario]['password'],
                    erro="Erro de Senha"
                )
                
                # Salve o erro
                path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\logins_falhas.txt"
                with open(path_file, "r+") as file:
                    text = file.read()
                    if contas[usuario]['RA'] not in text:
                        file.writelines(contas[usuario]['RA']+"   "+contas[usuario]['password']+"   SENHA\n")

                driver = chrome_encerra(driver)
            
            except CPFError:
                print("Mude para RA URGENTE!")
                driver = chrome_encerra(driver)
                situacao_aluno_mensalista(
                        aluno_nome=aluno_nome,
                        ra=ra_login,
                        senha=contas[usuario]['password'],
                        erro = "Mude para RA URGENTE"               
                )


            except TimeoutException:
                print("Erro de TimeOut")
                driver = chrome_encerra(driver)
                situacao_aluno_mensalista(
                        aluno_nome=aluno_nome,
                        ra=ra_login,
                        senha=contas[usuario]['password'],
                        erro = "erro"               
                    )
                # continue

            except Exception as err:                
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f" ERRO DESCONHECIDO 1496:\n"+msg)

            try:
                
                import random
                n=random.randint(0,9)
                cont+=1
                if n==5:
                    print("\n\n               ATUALIZAÇÃO DA GUI")
                    self.updateBarra.emit(cont,n_contas,"RA Aluno: " + usuario,"Inicializando")
                    self.updateTela.emit()
                    print("\n\n               ATUALIZOU A GUI com sucesso")
                # t(0.64)

            except Exception as err:                
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f" ERRO DESCONHECIDO 9356:\n"+msg)


        # Encerra a execução do Thread
        self.updateBarra.emit(n_contas,n_contas,"","") #100%
        self.updateTela.emit()
        time.sleep(1.5)
        print(f"Finalizou Thread")
        self.finished.emit()
       
    def lista_alunos_mensalistas(self):
        print("Iniciou Tela MENSALISTA")
        fcn_lista_alunos_mensalistas(self)
        fcn_lista_cursos_cadastrados(self)
        fcn_w_preenche_tela_mensalistas(self)
        print("Fim Tela")
        # t(2.5)
                
class  Rotinas_AtualizarTelaAtividades(QObject):
    finished = pyqtSignal()
    
    def __init__(self, ui) :

        super().__init__()

        self.ui = ui
        self.modulo = self.ui.menu_modulos.currentText()
        
    def run_atualizar_tela_atividades(self):
        """
        Verifica os módulos cadastrados e atualiza na GUI
        """
        path_file = path_dir+'\\BD\\atividades\\modulo.json'

        with open(path_file, encoding='utf-8') as json_file:
            data_modulo = json.load(json_file)

        modulo_atual = self.ui.menu_modulos.currentText()
        lista_modulos = []
        for modulo in data_modulo:
            lista_modulos.append(modulo)

        self.ui.menu_modulos.clear()
        self.ui.menu_modulos.addItems(lista_modulos)

        if self.modulo in lista_modulos:
            if self.ui.input_modulo_novo.text() != '' and self.ui.input_modulo_novo.text() in lista_modulos:
                self.ui.menu_modulos.setCurrentText(self.ui.input_modulo_novo.text())
            else:
                self.ui.menu_modulos.setCurrentText(modulo_atual)
        else:
            self.modulo = lista_modulos[0]
            self.ui.menu_modulos.setCurrentText(lista_modulos[0])

        self.modulo_situacao = data_modulo[self.modulo]['SITUAÇÃO']
        self.ui.l_situacao_modulo.setText(self.modulo_situacao)
        self.run_lista_atividades()
        self.finished.emit()

    def run_lista_atividades(self):
        """
        Atualiza as atividades dos módulos na GUI
        """      
        path_file = path_dir+'\\BD\\atividades\\modulo.json'
        with open(path_file, encoding='utf-8') as json_file:
            data_modulo = json.load(json_file)
        
        self.ui.tableWidget.setRowCount(0)
        # Atualiza arquivo sigla_nome  
        fcn_curso_sigla_nome(self)

        keys_atividade =  ["STATUS_ATIVIDADE","ID_URL", "DT_INICIO", "DT_FIM"]
        self.modulos = []
        disciplinas = []
        modulo = self.ui.menu_modulos.currentText()
        self.modulo_situacao = data_modulo[modulo]['SITUAÇÃO']
        self.ui.l_situacao_modulo.setText(self.modulo_situacao)

        # print(self.sigla_nome)
        for sigla in self.sigla_nome :
            #Verifica a integridade do BD da curso (sigla)
            # print("Verifica BD")
            data , path_file = integridade_bd(sigla,modulo)
            if data:
                for curso in data:
                    # print(curso)
                    for disciplina in data[curso]:
                        for atividade in data[curso][disciplina][modulo]["ATIVIDADE"]:
                            if atividade not in keys_atividade:
                                for questao in data[curso][disciplina][modulo]["ATIVIDADE"][atividade]:

                                    if questao not in keys_atividade:
                                        # Verfica se a Atividade foi publicada
                                        if data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]['ID_URL']:
                                            situacao = "ok"
                                        else:
                                            situacao = "a Enviar"
                                        
                                        if data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]['ESTILO'] == "QUESTIONARIO":
                                            if 'GABARITO' in data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]:
                                                if 'GABARITO_OK' in data[curso][disciplina][modulo]["ATIVIDADE"][atividade][questao]:
                                                    gabarito = "ok"
                                                else:
                                                    gabarito = "rastreado"
                                            else:
                                                gabarito = "a rastrear"
                                        else:
                                            gabarito = "n/a"
                                        
                                        
                                        if disciplina not in disciplinas and gabarito != "n/a":
                                            disciplinas.append(disciplina)
                                                
                                            # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
                                            rowPosition = self.ui.tableWidget.rowCount()

                                            # Insere uma nova linha na tabela
                                            self.ui.tableWidget.insertRow(rowPosition)

                                            # Cria o QTableWidgetItem para ser inserido na Widgettable, não se insere o elemento cru, como uma "str"
                                            item_sigla = QTableWidgetItem(sigla)
                                            item_disciplina = QTableWidgetItem(disciplina)
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
        # print("Finaliza T2")
        self.finished.emit()
