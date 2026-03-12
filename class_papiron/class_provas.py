import json
import os
import time
import traceback
from tkinter import E

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from selenium.common.exceptions import (
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
)

from class_papiron.class_error import AlunoNotScrappedError, ModuloError, StatusScrappedError
from dict_lista_curso import dict_curso_sigla_nome
from function import painel_avaliacao_digital, verifica_aviso
from function_bd import abre_json, save_json
from system.chrome import chrome_encerra, iniciar_sesssao_chrome, login, login_papiron
from functions.curso import dict_curso
from class_papiron.class_dados_aluno import Aluno
from system.system import t

path_dir = os.getcwd()

keys_atividade =  ["STATUS_ATIVIDADE","ID_URL","LISTA_ID_URL","DT_INICIO", "DT_FIM"]
keys_questao   =  ["STATUS_ATIVIDADE","ID_URL","LISTA_ID_URL","DT_INICIO", "DT_FIM"] 

class Rotinas_RastrearProvas(QObject):
    finished = pyqtSignal()
    updateProgress_rastrear = pyqtSignal(int, str)
    updateBarra = pyqtSignal(int,int,str,str)

    def __init__(self, ui , cursos, modulo, config,  i) :

        super().__init__()
        self.ui = ui
        self.config = config
        self.cursos = cursos
        self.modulo = modulo
        self.i = config['THREAD']
        self.modulo = config['MODULO']
        self.modulo_situacao = config['MÓDULO SITUAÇAO']
        self.lista_curso = config['LISTA CURSOS'] 
    
    def run_rastrear_provas(self):
        import os

        from system.pastas import apagar_arquivos_pasta, diretorio_raiz

        # Informa o Thread
        self.config['THREAD'] = str(self.i)
        # self.config['MODULO'] = str(self.i)

        try:
            print(f"Início Run {self.i}")
            self.updateProgress_rastrear.emit( 0,  "Iniciou o Thread "+str(self.i))

            # Inicializando a instância Driver para Chrome
            driver = None

            # Apagar pastas temporárias anteriores
            dir_papiron = diretorio_raiz()
            dir_provas = dir_papiron+"\\Provas"

            # Dados dos alunos
            path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
            alunos = abre_json(path_file=path_file)
            n_contas = len(alunos)

            # Dados dos cursos curso -> sigla
            # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla.json"
            # cursos = abre_json(path_file=path_file_curso)
            cursos = dict_curso(opcao=6)

            for i, ra in enumerate(alunos):

                try:
                    usuario = alunos[ra]['RA']
                    senha = alunos[ra]['SENHA']
                    aluno_nome = alunos[ra]['NOME']
                    aluno_curso =alunos[ra]['CURSO']
                    verifica_senha = alunos[ra]['SENHA_OK']
                    
                    # verifica se está matriculado alguma disciplina
                    matriculado = True if 'MATRICULADA' in alunos[ra]['DISCIPLINAS'] else False

                    try:
                        situacao = alunos[ra]['SITUAÇÃO']
                        cursos_nome = alunos[ra]['CURSO']
                        curso = cursos[cursos_nome]

                        ###  BLOCO PARA VERIFICAR AS DISCIPLINAS DISPONÍVEIS ###
                    
                    except KeyError as err:
                        """
                        Se durante o rastreamento não foi possível identificar dados do Aluno,
                        Então passe para o seguinte
                        """
                        print(f"[{self.i}] Passou para o aluno seguinte por falta de dados.\n")
                        self.updateProgress_rastrear.emit(0 ,  "Não foi possível coletar dados do aluno: "+alunos[ra]['RA'])
                        continue
                    
                    # print(verifica_senha, "OK", verifica_senha == "OK" , situacao , "CURSANDO" , situacao == "CURSANDO" , curso in self.lista_curso , matriculado)
                    if verifica_senha == "OK"       and\
                        situacao == "CURSANDO"      and\
                        curso in self.lista_curso   and\
                        matriculado:

                        print(f"\n\n\n[{self.i}] Iniciando o scrapped nº {i}:\n  ALUNO: {aluno_nome}\n       Curso: {curso}\n       Situação: {alunos[ra]['SITUAÇÃO']}\n       Login: {alunos[ra]['RA']}\n       Senha: {alunos[ra]['SENHA']}\n       Sistema: {alunos[ra]['SENHA_OK']}   ")
                        self.updateProgress_rastrear.emit( 1, "Iniciando o scrapped nº "+str(i)+":  ALUNO: "+aluno_nome+" = "+curso)

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
                            username=usuario,
                            password=senha
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
                        print("   - Preparando para rastrear dados de: ", aluno.nome)

                        # Scrapped dos dados do curso e disciplinas
                        print(f"   >> Aluno: {aluno_nome} - {aluno_ra} - {aluno_curso}")

                        painel_avaliacao_digital(driver=driver, aluno=aluno, modulo=self.modulo)


                    elif not curso in self.lista_curso:
                        # Curso não pertence ao Thread passa para o seguinte
                        # self.updateProgress_rastrear.emit(0,"")
                        continue    
                    
                    else:
                        print(f"   >>> [{self.i}] ALUNO: {aluno_nome} - {curso}\n      SITUAÇÃO: {situacao}")
                        continue
                    
                except (StatusScrappedError, AlunoNotScrappedError) as err:
                    print(f"     [{self.i}] As atividades do aluno já foram rastreadas: {aluno_nome}")
                    # print("ERRO:  ", err)
                    # self.updateProgress_rastrear.emit(0 , "As atividades do aluno já foram rastreadas: "+aluno_nome)
                    continue
            # self.updateProgress_rastrear.emit( 0 , "")
            # self.updateProgress_rastrear.emit( 0 , "") 
            self.updateProgress_rastrear.emit( 0 , "Finalizou o Thread "+str(self.i))
            # self.updateProgress_rastrear.emit( 0 , "")
            # self.updateProgress_rastrear.emit( 0 , "")
            print(f"CURSOS {self.i}", self.lista_curso)
            print(f"Finalizou Thread >> {self.i}")
            t(60)
            # self.sinal_postar.emit(self.lista_curso, self.config['THREAD'])
            msg = ""
            
        
        except ModuloError as err:
            msg = err
            self.updateProgress_rastrear.emit( 100 , "Finalizou o Thread "+str(self.i)+"com erro: MÓDULO FECHADO" )
            print(f"MÓDULO FECHADO")

        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            self.updateProgress_rastrear.emit( 100, "Finalizou o Thread "+str(self.i)+"com erro: "+msg )
            print(f"Finalizou Thread {self.i} com erro\n\n {msg}")
        
        t(1.5)
        self.finished.emit()
        print(msg)
   