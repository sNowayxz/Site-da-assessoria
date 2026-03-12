from datetime import datetime
import traceback

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal

import pdfkit

from function_bd import abre_json, lista_sigla_cursos, save_json
from function_btn import btn_sair, btn_voltar
from function_cb import (
    cb_chrome,
    cb_download_livros,
    cb_ect_atualizar,
    cb_geral_atualizar,
    cb_material_atualizar,
    cb_scg_atualizar,
)
from functions.atividade import dividir_json_em_n_arquivos, dividir_processos, lista_alunos_ra_ect, lista_alunos_ra_scg, listar_disciplinas
from system.chrome import terminate_chrome_processes
from system.crypto import recodification, salva_dados
from function_format import formatar_tela_atividades
from system.logger import log_grava
from function_tela_atividades import (
    fcn_modulo_abrir,
    fcn_modulo_excluir,
    fcn_modulo_fechar,
    fcn_modulos,
    fnc_modulo_novo,
    lista_atividades,
    progresso_lista,
)
from inicializacao import tela_atividades_render, tela_config_iniciais
from system.system import t
from thread.thread_atividades import (
    thread_atualizar_tela_atividades,
    thread_atualizar_tela_atividades_2,
    thread_rastrear_atividades_legado,
    thread_rastrear_atividades_r,
    thread_rastrear_atividades_r_ect,
    thread_rastrear_atividades_r_scg,
)
from window.window_atividades import Ui_Atividades
import os
import json

class Window_Atividades(QMainWindow):
    
    progresso_signal = pyqtSignal(int, str)

    def __init__(self):
        super(Window_Atividades, self).__init__()

        # Inicialização antes da abertura da GUI
        fcn_modulos(self)

        from PyQt6.QtCore import QDate        

        # Formatar dados iniciais
        self.config_iniciais()
        # print("Configurações iniciais:", self.config)
        
        self.ui = Ui_Atividades()
        self.ui.setupUi(self)

        # Supondo que o nome do widget seja self.ui.seuDateEdit
        hoje = QDate.currentDate()
        self.ui.data_inicio_rastreio.setDate(hoje)

        # Quando incluir um novo elemento, não esqueça de inclui-lo aqui
        tela_atividades_render(self)
        # Conexões
        
        # Widgets
        # self.ui.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection) #permite deixar várias células selecionadas
        # self.ui.tableWidget.itemClicked.connect(self.select_row)

        # BTN
        self.ui.btn_rastrear_atividades.clicked.connect(self.rastrear_atividades)
        self.ui.btn_rastrear_scg.clicked.connect(self.rastrear_atividades_scg)
        self.ui.btn_rastrear_ect.clicked.connect(self.rastrear_atividades_ect)
        self.ui.btn_voltar.clicked.connect(self.voltar)
        self.ui.btn_modulo_abrir.clicked.connect(self.modulo_abrir)
        self.ui.btn_modulo_fechar.clicked.connect(self.modulo_fechar)
        self.ui.btn_modulo_novo.clicked.connect(self.modulo_novo)
        self.ui.btn_modulo_excluir.clicked.connect(self.modulo_excluir)
        self.ui.btn_resetar_alunos.clicked.connect(self.resetar_alunos)
        self.ui.btn_resetar_atividades.clicked.connect(self.resetar_atividades)
        # self.ui.btn_andamento.clicked.connect(self.verificar_andamento)
        # self.ui.btn_comentar_questionarios.clicked.connect(self.comentar_questionarios)
        self.ui.btn_retomar_scrapped.clicked.connect(self.retomar_scrapped)

        # QCOMBOBOX - Lista Suspensa - MÓDULOS
        self.ui.menu_modulos.addItems(self.lista_modulos)
        self.ui.menu_modulos.currentIndexChanged.connect(self.verifica_modulo_selecionado)
        self.ui.menu_modulos.setCurrentText(self.modulo)
        self.ui.l_situacao_modulo.setText(self.modulo_situacao)
        self.ui.input_modulo_novo.returnPressed.connect(self.modulo_novo)
        self.ui.menu_processos.currentIndexChanged.connect(self.verifica_numero_processos)
        
        # CheckBox
        self.ui.cb_download_livros.clicked.connect(self.download_livros)
        # self.ui.cb_chrome.clicked.connect(self.chrome)
        self.ui.cb_material_atualizar.clicked.connect(self.material_atualizar)
        # self.ui.cb_scg.clicked.connect(self.scg)
        self.ui.cb_geral.clicked.connect(self.geral)
        # self.ui.cb_ect.clicked.connect(self.ect)

        # Conecte o sinal a uma função de atualização da GUI de maneira segura
        self.progresso_signal.connect(self.atualizar_barra_progresso)
        
        ## Formatar dados iniciais
        # formatar_tela_atividades(self)
        
        # Formatar Atividade e os módulos disponíveis
        # lista_atividades(self)

        # Instancia os Threads
        self.threads = {}
        self.workers = {}
        
    def config_iniciais(self):
        tela_config_iniciais(self)

    def salvar_dados(self):
        salva_dados(self)

    def rastrear_atividades(self):
            
            # a = 1200
            # print(f"Aguardando {a} segundos")
            # t(a)
            # t(1800)
            
            # Limpa a tabela de registros e o tempo da barra de progresso
            self.ui.barra_progresso_rastrear.setValue(0)
            self.progresso_rastrear = 0
            self.progresso_postar = 0

            # Leitura de usuário e senha do Papiron/Modelitos
            data = abre_json(r'BD/atividades/user_data.json')
            self.config['username'] = recodification(data['usuario'])
            self.config['password'] = recodification(data['password'])

            # Data de início de rastreio
            checked_date = self.ui.cb_data_inicio_rastreio.isChecked()
            if checked_date:
                self.config["data_base"] = self.ui.data_inicio_rastreio.date().toString("yyyy-MM-dd")
            else:
                self.config["data_base"] = "2010-01-01"

            # Número de processos que serão acionados durante o rastreamento e módulo atual
            self.num_processos = int(self.ui.menu_processos.currentText())

            # Iniciar o módulos     
            self.verificar_modulos_abertos()

            # Limpa tabela
            self.ui.tabela_registro.clear()

            # Verifica se é alguma disciplina única
            self.disciplina_unica = self.ui.disciplina.text().strip() if self.ui.disciplina.text().strip() else None
            if self.disciplina_unica:
                print(f" >>> Irá rastrear apenas {self.disciplina_unica}")             

            # Obter do site as disciplinas dos módulos desejados
            self.lista_curso_disciplinas = listar_disciplinas(self)

            # self.lista_dicts_disciplinas = dividir_processos(self.lista_curso_disciplinas,self.num_processos)
            self.lista_dicts_disciplinas = dividir_json_em_n_arquivos(self.lista_curso_disciplinas, '00/aaa_4433', self.num_processos)

            self.progresso_total_rastrear = self.contar_disciplinas()

            print(f" >> Foram localizadas {self.progresso_total_rastrear} disciplinas.  >> Processos {self.num_processos}")

            thread_rastrear_atividades_r(self)

    def rastrear_atividades_scg(self):
                        
            # Limpa a tabela de registros e o tempo da barra de progresso
            self.ui.barra_progresso_rastrear.setValue(0)
            self.progresso_rastrear = 0
            self.progresso_postar = 0

            # Leitura de usuário e senha do Papiron/Modelitos
            data = abre_json(r'BD/atividades/user_data.json')
            self.config['username'] = recodification(data['usuario'])
            self.config['password'] = recodification(data['password'])

            # Data de início de rastreio
            checked_date = self.ui.cb_data_inicio_rastreio.isChecked()
            if checked_date:
                self.config["data_base"] = self.ui.seuDateEdit.date().toString("yyyy-MM-dd")
            else:
                self.config["data_base"] = None

            # Número de processos que serão acionados durante o rastreamento e módulo atual
            self.num_processos = int(self.ui.menu_processos.currentText())

            # Limpa tabela
            self.ui.tabela_registro.clear()

            # Obter do site as disciplinas dos módulos desejados
            disc_especial = "scg"
            
            lista_alunos_ra_scg(self, disc_especial)

            self.config['rastrear_scg'] = True

            self.progresso_total_rastrear = len(self.ras)

            self.config['disciplina'] = "SEMANA DE CONHECIMENTOS GERAIS"

            print(f" >> Foram localizados {self.progresso_total_rastrear} portais para rastrear {self.config['disciplina']}")

            thread_rastrear_atividades_r_scg(self)
            
    def rastrear_atividades_ect(self,disc_especial):
                        
            # Limpa a tabela de registros e o tempo da barra de progresso
            self.ui.barra_progresso_rastrear.setValue(0)
            self.progresso_rastrear = 0
            self.progresso_postar = 0

            # Leitura de usuário e senha do Papiron/Modelitos
            data = abre_json(r'BD/atividades/user_data.json')
            self.config['username'] = recodification(data['usuario'])
            self.config['password'] = recodification(data['password'])

            # Iniciar o módulos     
            self.verificar_modulos_abertos()

            # Data de início de rastreio
            checked_date = self.ui.cb_data_inicio_rastreio.isChecked()
            if checked_date:
                self.config["data_base"] = self.ui.seuDateEdit.date().toString("yyyy-MM-dd")
            else:
                self.config["data_base"] = "2010-01-01"

            # Número de processos que serão acionados durante o rastreamento e módulo atual
            self.num_processos = int(self.ui.menu_processos.currentText())

            # Limpa tabela
            self.ui.tabela_registro.clear()

            self.config['rastrear_ect'] = True

            disc_especial = "ect"

            self.ras = lista_alunos_ra_ect(self, disc_especial)

            save_json(data=self.ras,path_file="00/alunos_ect.json")

            self.progresso_total_rastrear = self.contar_alunos_ect(self.ras)

            thread_rastrear_atividades_r_ect(self)

    def contar_cursos(self):

        return sum(
            len(modulo)
            for ano in self.lista_curso_disciplinas.values()
            for modulo in ano.values()
        )
    
    def contar_disciplinas(self):

        total_disciplinas = 0
        for ano in self.lista_curso_disciplinas.values():
            for modulo in ano.values():
                for curso in modulo.values():
                    total_disciplinas += len(curso)

        return total_disciplinas
    
     
    def contar_alunos_ect(self,ras):
        # Realiza a contagem total de alunos que fazem ECT
        total_alunos = 0
        for ano in ras.values():
            print(ano)
            for modulo in ano.values():
                total_alunos += len(modulo)

        total_alunos

        return total_alunos

    def retomar_scrapped(self):
        import os
        from datetime import datetime

        dt_hoje = datetime.now().__format__('%Y%m%d')
        path_file_atividades = os.getcwd()+'\\BD\\atividades\\dias_scrapped.json'
        if os.path.isfile(path=path_file_atividades):
            data_atividades = abre_json(path_file=path_file_atividades)
            for data in data_atividades:
               pass
            # Repete o último rastreio para a data atual
            if dt_hoje != data:
                data_atividades[dt_hoje] = data_atividades[data] 
                save_json(data=data_atividades,path_file=path_file_atividades)

        path_file_alunos = os.getcwd()+'\\BD\\alunos\\dias_scrapped.json'
        if os.path.isfile(path=path_file_alunos):
            data_alunos = abre_json(path_file=path_file_alunos)
            for data in data_alunos:
               pass
            
            # Repete o último rastreio para a data atual
            if dt_hoje != data:
                data_alunos[dt_hoje] = data_alunos[data] 
                save_json(data=data_alunos,path_file=path_file_alunos)
                progresso_lista(self,"Dados de rastreios duplicados com sucesso")
            else:
                progresso_lista(self,"Os dados não puderam duplicados pois o último dia foi hoje.")

    def verificar_modulos_abertos(self):
        # Iniciar o módulos     
        path_file = os.getcwd()+'\\BD\\atividades\\modulo.json'

        with open(path_file, encoding='utf-8') as json_file:
            modulo_info = json.load(json_file)

        self.modulos_abertos = []
        for modulo in modulo_info:
            if modulo_info[modulo]['SITUAÇÃO']=="ABERTO":
                self.modulos_abertos.append(modulo)
            
        if self.ui.cb_geral.isChecked():
            ano_atual = datetime.now().year
            self.modulos_abertos.append(f"{ano_atual}_9")

    def modulo_novo(self):

        # Leitura do módulo atual
        # self.modulo = #fnc_modulo_atual(self)
        
        # Leitura do input Novo Módulo
        self.modulo_novo = self.ui.input_modulo_novo.text()

        # Criação novo módulo
        fnc_modulo_novo(self)

        # Refazimento dos itens da lista Suspensa
        thread_atualizar_tela_atividades(self)

    def verifica_modulo_selecionado(self):
        # print("passou")
        thread_atualizar_tela_atividades_2(self)
        
    def verifica_numero_processos(self):
        import os
        path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
        data = abre_json(path_file=path_file)
        data['menu_processos'] = int(self.ui.menu_processos.currentText())
        save_json(data=data, path_file=path_file)
        
    def modulo_abrir(self):
        fcn_modulo_abrir(self)
        thread_atualizar_tela_atividades(self)

    def modulo_fechar(self):
        fcn_modulo_fechar(self)
        thread_atualizar_tela_atividades(self)
    
    def modulo_excluir(self):
        fcn_modulo_excluir(self)
        thread_atualizar_tela_atividades(self)
 
    # def select_row(self, item):
        # self.ui.tableWidget.selectRow(item.row())

    def download_livros(self):
        cb_download_livros(self)
    
    def chrome(self):
        cb_chrome(self)

    def material_atualizar(self):
        cb_material_atualizar(self)
    
    def scg(self):
        cb_scg_atualizar(self)
    
    def geral(self):
        cb_geral_atualizar(self)
        
    def ect(self):
        cb_ect_atualizar(self)

    def voltar(self):
        btn_voltar(self)

    def sair(self):
        btn_sair(self)

    def obter_progresso(self, value, texto):
        """
        Value é o valor já processado, enviado pela Thread.
        Texto é o valor a ser inserido na tabela de Andamento.
        """
        try:
            self.progresso_signal.emit(value, texto)
        except Exception as err:
            log_grava(err=err)
        
    def atualizar_barra_progresso(self, value, texto):

        # Calcula percentual
        valor_barra = value / self.progresso_total_rastrear * 100

        # Atualiza a barra de progresso
        self.ui.barra_progresso_rastrear.setValue(int(valor_barra))

        # Atualiza o QLabel ao lado da barra, mostrando centesimais e fração real
        texto_acompanhamento = "{:.2f}%  ({}/{})".format(valor_barra, int(value), self.progresso_total_rastrear)
        self.ui.label_progresso_valor.setText(texto_acompanhamento)

        # Atualiza log
        if texto:
            self.adicionar_log_tabela_registro(texto)

    def adicionar_log_tabela_registro(self, texto):

        # Adiciona nova linha na QListWidget (tabela_registro)
        self.ui.tabela_registro.addItem(texto)

        # Faz scroll automático para a última linha
        self.ui.tabela_registro.scrollToBottom()
  
    def resetar_alunos(self):
        import os
        path_file = os.getcwd()+'\\BD\\alunos\\dias_scrapped.json'
        if os.path.isfile(path=path_file):
            os.remove(path=path_file)
        
        path_file_temp = os.getcwd()+'\\BD\\alunos\\dias_scrapped.TEMP.json'
        if os.path.isfile(path=path_file_temp):
            os.remove(path=path_file_temp)

    def resetar_atividades(self):
        import os
        path_file = os.getcwd()+'\\BD\\atividades\\dias_scrapped.json'
        if os.path.isfile(path=path_file):
            os.remove(path=path_file)

        path_file_temp = os.getcwd()+'\\BD\\atividades\\dias_scrapped.TEMP.json'
        if os.path.isfile(path=path_file_temp):
            os.remove(path=path_file_temp)
