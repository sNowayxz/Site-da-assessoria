import json
import os
import time
import traceback

from function import (
    iniciar_sesssao_chrome,
    lista_disciplinas,
    login,
    situacao_aluno,
    registra_curso,
    verifica_aviso,
)

from functions.curso import dict_curso

from PyQt6 import QtCore
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from selenium.common.exceptions import (
    SessionNotCreatedException,
    TimeoutException,
)

from class_papiron.class_error import (
    AlunoNotScrappedError,
    CPFError,
    DisciplinaError,
    FileLoginError,
    SenhaError,
    StatusScrappedError,
)

from function_bd import abre_json, integridade_bd, save_json
from system.chrome import chrome_encerra
from system.logger import log_grava
from function_system import verifica_json
from function_tela_alunos import (
    fcn_lista_alunos_cadastrados,
    fcn_lista_cursos_cadastrados,
)
from function_tela_atividades import fcn_curso_sigla_nome
from function_window import fcn_w_preenche_tela_cadastro
from class_papiron.class_dados_aluno import Aluno
from system.system import t

path_dir = os.getcwd()

class Rotinas_AtualizaCadastro(QObject):
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
            path_file_logins = os.path.abspath(os.getcwd())+"\\BD\\alunos\\contas.json"
            contas  = verifica_json(path_file_logins)
            n_contas = len(contas)

            # Carrega arquivo JSON de Alunos
            path_file_alunos = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
            alunos = verifica_json(path_file_alunos)

            # Carrega o arquivo JSON de Cursos
            cursos = dict_curso(opcao=4)
            
            if not n_contas:
                raise FileLoginError

            # Inicializando
            driver = None
        
        except FileLoginError:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "[FALHA]: Arquivo de LOGINS está vazio.","Erro de Logins",0)
            self.finished.emit()
            return None

        for usuario in contas:

            self.updateTela.emit()
            print(">>>>>>>>>          <<<<<<<<<\n\nLogin Aluno:" + usuario, "Inicializando\n")
            self.updateBarra.emit(1,n_contas,"RA Aluno: " + usuario,"Inicializando")
            self.insere_label("RA Aluno: " + usuario, "Localizando informações")

            try: 
                
                ra_login = usuario.replace("-","").replace(".","").replace("/","")
                tipo = True if len(ra_login) <= 9 else False

                # Verifica se o login é CPF ou RA
                # Se for CPF passa para o próximo
                if not tipo:
                    print("\n\nLogin pelo CPF passa para outro\n\n")
                    raise CPFError

                if ra_login in alunos:
                    
                    # Verifica se atualiza todos os logins ou apenas novos
                    aluno_nome = alunos[ra_login]["NOME"]
                    if self.config['cb_atualizar_novos_cadastros']:
                        print(f"        Passa para o próximo aluno, pois {aluno_nome} já está no BD")
                        t(0.5)
                        # Levanta erro, pois serão feitos scrappeds apenas em alunos novos
                        raise StatusScrappedError

                    # Caso ocorra algum erro em obter novamente estes dados
                    # logo a frente
                    aluno_ra = alunos[ra_login]["RA"]
                    aluno_curso = alunos[ra_login]["CURSO"]

                    print(f"    >>> Atualizar:  {aluno_ra} - {aluno_nome}")
                    self.updateBarra.emit(0,n_contas,aluno_nome,"Atualizando login")

                else:
                    #Novo login
                    aluno_nome = ra_login
                    print(f"    >>> Novo Login:  {ra_login}")
                    self.updateBarra.emit(0,n_contas,ra_login,"Novo Login")

                # Inicia a sessão somente se fechou a anterior, completou os dados do aluno
                self.updateBarra.emit(0,n_contas,aluno_nome,"Instanciando Chromedriver")
                if driver:
                    driver=chrome_encerra(driver)
                driver = iniciar_sesssao_chrome()
                
                if not driver:
                    print("CHROME: Sessão não criada!!!")
                    raise SessionNotCreatedException
                    
                # Realiza o login no usuário do FOR
                self.updateBarra.emit(0,n_contas,aluno_nome,"Acessando Portal")
                driver = login(
                    driver=driver,
                    username=contas[usuario]['RA'],
                    password=contas[usuario]['password']
                )

                if not driver:
                    print("CHROME: Sessão não criada!!!")
                    raise SessionNotCreatedException
                
                # Verificações iniciais de login
                verifica_aviso(driver)
                self.updateBarra.emit(0,n_contas,aluno_nome,"Portal acessado")

                # Cria instância do aluno
                aluno = Aluno(driver)
                aluno_nome = aluno.nome
                aluno_ra = aluno.ra
                aluno_curso = aluno.curso
                print("   - Obteve dados do aluno:", aluno.nome)

                # Verifica se é um curso novo na lista
                if aluno.curso not in cursos:
                    cursos[aluno.curso] = "NOVO"
                    registra_curso(aluno.curso)

                # Scrapped dos dados do curso e disciplinas
                print(f"   >> Aluno: {aluno_nome} - {aluno_ra} - {aluno_curso}")

                # painel_avaliacao_digital(driver=driver, aluno=aluno)
                
                disciplinas  = lista_disciplinas(driver)
                self.updateBarra.emit(0,n_contas,aluno_nome,"Gravando dados do Aluno")
                situacao_aluno(
                    aluno_nome=aluno_nome,
                    ra=ra_login,
                    senha=contas[usuario]['password'],
                    curso=aluno_curso,
                    disciplinas=disciplinas
                )
                driver = chrome_encerra(driver)
                
            except (KeyError,TypeError,AttributeError, SessionNotCreatedException, MaxRetryError) as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("ERRO: passou para o seguinte!\n"+msg)
                situacao_aluno(
                    ra=ra_login,
                    senha=contas[usuario]['password'],
                    senha_ok="FALHA DE SESSÃO"
                )
                driver = chrome_encerra(driver)
                continue

            except AlunoNotScrappedError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("ERRO: passou para o seguinte!\n"+msg)
                situacao_aluno(
                    ra=ra_login, 
                    senha=contas[usuario]['password'], 
                    senha_ok="SENHA FALHOU"
                )
                driver = chrome_encerra(driver)
            
            except StatusScrappedError as err:
                # Aluno já está no BD, pule para o seguinte
                continue

            except DisciplinaError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("Erro em acessar as disciplinas Matriculadas:"+msg)
                situacao_aluno(
                    ra=ra_login,
                    senha=contas[usuario]['password']
                )
                driver = chrome_encerra(driver)
                continue

            except SenhaError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("Erro na senha, faça o seguinte\n"+msg)
                situacao_aluno(
                    ra=ra_login,
                    senha = contas[usuario]['password'],
                    senha_ok="SENHA FALHOU"
                )
                
                # Salve o erro
                path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\logins_falhas.txt"
                with open(path_file, "r+") as file:
                    text = file.read()
                    if usuario not in text:
                        file.writelines(usuario+"   "+contas[usuario]['password']+"   SENHA\n")

                driver = chrome_encerra(driver)
            
            except CPFError as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("Login em formato de CPF, faça o seguinte\n"+msg)
                situacao_aluno(
                    ra=ra_login,
                    senha=contas[usuario]['password'],
                    senha_ok = "INDEFINIDO"
                )
                # Salve o erro
                path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\logins_falhas.txt"
                with open(path_file, "r+") as file:
                    text = file.read()
                    if usuario not in text:
                        file.writelines(usuario+"   "+contas[usuario]['password']+"   CPF\n")
                continue

            except TimeoutException:
                print("Erro de TimeOut")
                driver = chrome_encerra(driver)
                continue
            
            except Exception as err:
                log_grava(err=err)

        # Encerra a execução do Thread
        self.updateBarra.emit(n_contas,n_contas,"","") #100%
        self.updateTela.emit()
        t(1.5)

        # Colocar por ordem de Curso e RA
        path_file_alunos = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
        atualiza_ordem = abre_json(path_file=path_file_alunos)
        sorted_data = dict(sorted(atualiza_ordem.items(), key=lambda item: (item[1]['CURSO'], item[1]['RA'])))
        save_json(data=sorted_data,path_file=path_file_alunos)
        print(f"Finalizou Thread")
        self.finished.emit()
       
    def lista_alunos_cadastrados(self):
        print("Iniciou Tela")
        fcn_lista_alunos_cadastrados(self)
        fcn_lista_cursos_cadastrados(self)
        fcn_w_preenche_tela_cadastro(self)
        print("Fim Tela")
                
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
        
        # self.ui.tableWidget.setRowCount(0)
        # Atualiza arquivo sigla_nome  
        fcn_curso_sigla_nome(self)

        keys_atividade =  ["STATUS_ATIVIDADE","ID_URL", "DT_INICIO", "DT_FIM","LISTA_ID_URL"]
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
            # print("Verifica BD", data)
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
