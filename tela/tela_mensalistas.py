from function_format import formatar_tela_mensalistas
from function_tela_alunos import fcn_lista_alunos_mensalistas
from function_window import fcn_w_preenche_tela_mensalistas
from inicializacao import tela_mensalistas_render
from system.pastas import verifica_pastas
from thread.thread_mensalistas import thread_mensalistas_proc

try:
    import traceback

    from PyQt6.QtGui import *
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import pyqtSignal

    from function_bd import clear_bd, leitura_de_contas, save_json
    from function_btn import btn_sair, btn_voltar
    from function_cb import cb_chrome, cb_novos_cadastros
    from function_format import formatar_tela_cadastro
    from system.logger import log_grava
    from function_tela_alunos import (
        fcn_lista_alunos_cadastrados,
        fcn_lista_cursos_cadastrados,
    )
    from function_window import fcn_w_preenche_tela_cadastro
    from inicializacao import (
        salva_config_user,
        tela_cadastro_render,
        tela_config_iniciais,
    )
    from window.window_mensalistas import Ui_MensalistasAlunos

except (ImportError,ModuleNotFoundError) as err:
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print("[INICIALIZANDO - TELA CADASTRO]:\n"+str(msg))
    log_grava(msg="[INICIALIZANDO - TELA CADASTRO] ERRO:\n"+str(msg))

except Exception as err:
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print("[INICIALIZANDO]:\n"+str(msg))
    log_grava(msg="[INICIALIZANDO - TELA CADASTRO] ERRO:\n"+str(msg))


class Window_MensalistasAlunos(QMainWindow):

    progresso_signal = pyqtSignal(int, str)

    def __init__(self):
        super(Window_MensalistasAlunos, self).__init__()

        self.ui = Ui_MensalistasAlunos()
        self.ui.setupUi(self)

        # Formatar dados iniciais
        self.config_iniciais()
        print("Configurações iniciais:", self.config)
        
        # Conexões
        self.ui.tableWidget.itemClicked.connect(self.select_row)
        self.ui.botao_atualiza_cadastro.clicked.connect(self.atualiza_atividades)
        self.ui.btn_arquivo.clicked.connect(self.seleciona_arquivo)
        self.ui.btn_limpar.clicked.connect(self.limpar_tabela)
        
        self.ui.botao_voltar.clicked.connect(self.voltar)
        self.ui.cb_chrome.clicked.connect(self.chrome)
        self.ui.cb_novos.clicked.connect(self.atualizar_novos_cadastros)

        # Conecte o sinal a uma função de atualização da GUI de maneira segura
        self.progresso_signal.connect(self.atualizar_barra_progresso)

        formatar_tela_mensalistas(self)
        tela_mensalistas_render(self)
        self.lista_alunos_mensalistas()
        log_grava(msg="[CADASTRO]: Módulo iniciado corretamente")
    
    def config_iniciais(self):
        tela_config_iniciais(self)
    
    def lista_alunos_mensalistas(self):
        fcn_lista_alunos_mensalistas(self)
        fcn_lista_cursos_cadastrados(self)
        fcn_w_preenche_tela_mensalistas(self)

    def atualiza_atividades(self):
        from thread.thread_mensalistas import thread_mensalistas
        try:
            self.progresso = 0
            thread_mensalistas(self)
            # thread_mensalistas_proc(self)
        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print("[INICIALIZANDO]:\n"+str(msg))

  
    def seleciona_arquivo(self):
        import os
        import shutil

        from tela.tela_arquivo import File_Dialog

        # Diretório base de visualização
        dir_files = os.path.join(os.path.expanduser("~"), "Desktop\\Papiron\\files")

        # Verifica se a pasta existe, e cria se não existir
        verifica_pastas(dir_pasta=dir_files)
        
        # Cria a instância de Tela de Dialogo
        tela_dialogo = File_Dialog()

        # Verifica se há pasta preferencial
        dir_login = self.config.get('path_dir_login', dir_files )

        # Chama a tela de diálogo
        self.arquivo_tela = tela_dialogo.pathFile(dir_login)

        # Se um arquivo foi selecionado
        if self.arquivo_tela:

            # Realiza o envio dos dados para um arquivo json
            try:
                path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\contas_mensalista.json"
                dicts_logins = leitura_de_contas(self.arquivo_tela) 
                n=len(dicts_logins)
                save_json(dicts_logins,path_file)       
                self.ui.l_info_progresso.setText(f"Arquivo atualizado com sucesso! →  Adicionados {n} Logins")

            except IndexError:
                self.ui.l_info_progresso.setText("[ATENÇÃO]: Arquivo de logins com problemas!! <<<")
        
            # Salva nas configurações onde localizaou o arquivo
            salva_config_user(path_file_login = os.path.dirname(self.arquivo_tela))
            self.config['path_dir_login'] = os.path.dirname(self.arquivo_tela)

    def clear_errados(self):
        clear_bd()
        self.lista_alunos_cadastrados()

    def select_row(self, item):
        self.ui.tableWidget.selectRow(item.row())

    def chrome(self):
        cb_chrome(self)

    def atualizar_novos_cadastros(self):
        cb_novos_cadastros(self)

    def prog(self,value, total, text_nome, info):
        # print(f"   Atualizando tela: {value} - {total} - {self.progresso}")
        self.progresso = self.progresso + value
        self.progresso = value
        valor = int(self.progresso/total*100)

        self.progresso_signal.emit(valor, text_nome)  # Emitindo o sinal
        
        print(f"   Tela atualizada: {valor} - {self.progresso}")
    
    def atualizar_barra_progresso(self, valor, texto):
        # Atualiza a GUI de forma segura
        self.ui.barra_progresso.setValue(valor)
        self.lista_alunos_mensalistas()
        self.text = texto
    
    def limpar_tabela(self):
        import ctypes
        import os

        ctypes.windll.user32.MessageBoxW(0, "A limpeza sairá desta tela, retorne para a tela de Mensalista em seguida!","Limpeza de Banco de Dados",0)
        file_mensalistas = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_mensalista.json"
        os.remove(file_mensalistas)
        btn_voltar(self)

    def voltar(self):
        btn_voltar(self)

    def sair(self):
        btn_sair(self)
      