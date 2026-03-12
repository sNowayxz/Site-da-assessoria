import traceback

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal

from function import separa_contas, separa_cursos
from function_bd import abre_json, lista_sigla_cursos, save_json
from function_btn import btn_sair, btn_voltar
from function_cb import (
    cb_chrome,
    cb_corrige_gabarito,
    cb_discursivas,
    cb_geral_atualizar,
    cb_scg_atualizar,
    cb_verificar_idurl_site,
)

from functions.curso import dict_curso
from system.crypto import salva_dados
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
from inicializacao import tela_config_iniciais, tela_envio_render

from system.system import t
from thread.thread_atividades import thread_atualizar_tela_atividades, thread_atualizar_tela_atividades_2
from thread.thread_comentarios import thread_enviar_comentarios
from thread.thread_gabaritos import thread_postar_gabaritos

from thread.thread_postar_site import thread_postar_atividades
from window.window_envio import Ui_Atividades
import os
import json

class Window_Atividades(QMainWindow):
    
    progresso_signal = pyqtSignal(int, str)

    def __init__(self):
        super(Window_Atividades, self).__init__()

        # Inicialização antes da abertura da GUI
        fcn_modulos(self)
        
        # Formatar dados iniciais
        self.config_iniciais()
        # print("Configurações iniciais:", self.config)
        
        self.ui = Ui_Atividades()
        self.ui.setupUi(self)

        # Quando incluir um novo elemento, não esqueça de inclui-lo aqui
        tela_envio_render(self)
        # Conexões
        
        # Widgets
        self.ui.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection) #permite deixar várias células selecionadas
        self.ui.tableWidget.itemClicked.connect(self.select_row)

        # BTN
        self.ui.btn_postar_atividades.clicked.connect(self.postar_atividades)
        self.ui.btn_gabaritos.clicked.connect(self.postar_gabaritos)
        self.ui.btn_voltar.clicked.connect(self.voltar)
        self.ui.btn_modulo_abrir.clicked.connect(self.modulo_abrir)
        self.ui.btn_modulo_fechar.clicked.connect(self.modulo_fechar)
        self.ui.btn_modulo_novo.clicked.connect(self.modulo_novo)
        self.ui.btn_modulo_excluir.clicked.connect(self.modulo_excluir)
        # self.ui.btn_andamento.clicked.connect(self.verificar_andamento)
        self.ui.btn_comentar_questionarios.clicked.connect(self.comentar_questionarios)

        # QCOMBOBOX - Lista Suspensa - MÓDULOS
        self.ui.menu_modulos.addItems(self.lista_modulos)
        self.ui.menu_modulos.currentIndexChanged.connect(self.verifica_modulo_selecionado)
        self.ui.menu_modulos.setCurrentText(self.modulo)
        self.ui.l_situacao_modulo.setText(self.modulo_situacao)
        self.ui.input_modulo_novo.returnPressed.connect(self.modulo_novo)
        self.ui.menu_processos.currentIndexChanged.connect(self.verifica_numero_processos)
        
        # CheckBox
        self.ui.cb_salvar.clicked.connect(self.salvar_dados)
        self.ui.cb_scg.clicked.connect(self.scg)
        self.ui.cb_geral.clicked.connect(self.geral)
        self.ui.cb_verificar_idurl_site.clicked.connect(self.verificar_idurl_site)
        self.ui.cb_discursivas.clicked.connect(self.discursivas)
        self.ui.cb_corrige_gabarito.clicked.connect(self.corrige_gabarito)

        # Conecte o sinal a uma função de atualização da GUI de maneira segura
        self.progresso_signal.connect(self.atualizar_barra_progresso)
        
        ## Formatar dados iniciais
        formatar_tela_atividades(self)
        
        # Formatar Atividade e os módulos disponíveis
        lista_atividades(self)

        # Instancia os Threads
        self.threads = {}
        self.workers = {}
        
    def config_iniciais(self):
        tela_config_iniciais(self)

    def salvar_dados(self):
        salva_dados(self)

    def definir_inicio_script(self):
        
        # Quantidade de processos simultâneos
        num_processos = int(self.ui.menu_processos.currentText())

        # Verifica se é para restringir o processo em curso e/ou disciplina
        self.config['postar_cursos'] = self.ui.input_lista_cursos.text()
        self.config['disciplina_unica'] = self.ui.input_disciplina.text()

        # Leitura de usuário e senha do Papiron/Modelitos
        self.config['username'] = self.ui.input_login.text()
        self.config['password'] = self.ui.input_senha.text()

        # Iniciar o módulos     
        self.verificar_modulos_abertos()

        #        
        self.cursos = separa_cursos(lista_sigla_cursos(), num_processos)
        
        # Obter tamanho do progresso
        self.progresso = 0
        self.obter_tamanho_progresso(self.cursos)

    def postar_atividades(self):
        self.definir_inicio_script()
        thread_postar_atividades(self)


    def postar_gabaritos(self):
        self.definir_inicio_script()
        thread_postar_gabaritos(self)

        # lista_atividades(self)

    def comentar_questionarios(self):
        self.definir_inicio_script()
        thread_enviar_comentarios(self)
    
    def verificar_modulos_abertos(self):
        # Iniciar o módulos     
        path_file = os.getcwd()+'\\BD\\atividades\\modulo.json'

        with open(path_file, encoding='utf-8') as json_file:
            modulo_info = json.load(json_file)

        self.modulo_abertos = []
        for modulo in modulo_info:
            if modulo_info[modulo]['SITUAÇÃO']=="ABERTO":
                self.modulo_abertos.append(modulo)

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
 
    def select_row(self, item):
        self.ui.tableWidget.selectRow(item.row())
    
    def chrome(self):
        cb_chrome(self)
    
    def scg(self):
        cb_scg_atualizar(self)
    
    def geral(self):
        cb_geral_atualizar(self)

    def verificar_idurl_site(self):
        cb_verificar_idurl_site(self)

    def discursivas(self):
        cb_discursivas(self)

    def corrige_gabarito(self):
        cb_corrige_gabarito(self)

    def voltar(self):
        btn_voltar(self)

    def sair(self):
        btn_sair(self)

    def obter_tamanho_progresso(self, cursos):
        import re

        # # Obtém tamanho da operação
        # if self.config['postar_cursos']:
        #     # Retorna a quantidade de cursos específicos
        #     self.progresso_total=len(re.split(r'[;,\s]',self.config['postar_cursos'].strip())) * len(self.modulo_abertos)
        #     print(1, self.progresso_total)
        # else:
        # Retorna a quantidade total de cursos cadastrados
        self.progresso_total=len(self.modulo_abertos)*len(dict_curso(opcao=5))
        print(2, self.progresso_total)
        # Soma o total de elementos de cada sublista que há em cursos
        self.progresso_total = sum(len(curso) for curso in cursos)*len(self.modulo_abertos)
        print(3, self.progresso_total)
    

    def obter_progresso(self, valor, texto):
        
        try:
            self.progresso+=valor
            print(f"incremento: {valor} - {self.progresso} - {self.progresso_total}")
            andamento = int(self.progresso/self.progresso_total*100)
            self.text = texto
            self.progresso_signal.emit(andamento, texto)

        except Exception as err:
            log_grava(err=err)


    def atualizar_barra_progresso(self, valor, texto):
        # Atualiza a GUI de forma segura
        self.ui.barra_progresso_postar.setValue(valor)
        self.text = texto