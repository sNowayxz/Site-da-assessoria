try:
    import traceback

    from PyQt6.QtGui import *
    from PyQt6.QtWidgets import *

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
    from window.window_cadastro_alunos import Ui_CadastroAlunos

except (ImportError,ModuleNotFoundError) as err:
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print("[INICIALIZANDO - TELA CADASTRO]:\n"+str(msg))
    log_grava(msg="[INICIALIZANDO - TELA CADASTRO] ERRO:\n"+str(msg))

except Exception as err:
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print("[INICIALIZANDO]:\n"+str(msg))
    log_grava(msg="[INICIALIZANDO - TELA CADASTRO] ERRO:\n"+str(msg))


class Window_CadastroAlunos(QMainWindow):
    def __init__(self):
        super(Window_CadastroAlunos, self).__init__()

        self.ui = Ui_CadastroAlunos()
        self.ui.setupUi(self)

        # Formatar dados iniciais
        self.config_iniciais()
        print("Configurações iniciais:", self.config)
        
        # Conexões
        self.ui.tableWidget.itemClicked.connect(self.select_row)
        self.ui.botao_atualiza_cadastro.clicked.connect(self.atualiza_alunos_cadastrados)
        self.ui.btn_arquivo.clicked.connect(self.seleciona_arquivo)
        self.ui.btn_del_errados.clicked.connect(self.clear_errados)

        self.ui.botao_voltar.clicked.connect(self.voltar)
        self.ui.cb_chrome.clicked.connect(self.chrome)
        self.ui.cb_novos.clicked.connect(self.atualizar_novos_cadastros)

        formatar_tela_cadastro(self)
        tela_cadastro_render(self)
        self.lista_alunos_cadastrados()
        log_grava(msg="[CADASTRO]: Módulo iniciado corretamente")
    
    def config_iniciais(self):
        tela_config_iniciais(self)
    
    def lista_alunos_cadastrados(self):
        fcn_lista_alunos_cadastrados(self)
        fcn_lista_cursos_cadastrados(self)
        fcn_w_preenche_tela_cadastro(self)

    def atualiza_alunos_cadastrados(self):
        from thread.thread_cadastro_alunos import thread_atualizar_dados_alunos
        try:
            log_grava(msg="[CADASTRO]: Inicia modo ATUALIZAR DADOS")
            self.progresso = 0
            
            # num_processos = int(self.ui.menu_processos.currentText())
            # self.progresso = 0
            # self.ui.tabela_registro.clear()
            # alunos, self.progresso_total = separa_contas_alunos(divisao = num_processos)
            # self.modulo_situacao = self.ui.l_situacao_modulo.text()
            thread_atualizar_dados_alunos(self)

        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print("[INICIALIZANDO]:\n"+str(msg))
            log_grava(msg="[CADASTRO] ERRO:\n"+str(msg))
  
    def seleciona_arquivo(self):
        import os
        import shutil

        from tela.tela_arquivo import File_Dialog

        # Diretório base de visualização
        dir_papiron = os.path.join(os.path.expanduser("~"), "Desktop\\Papiron")
        
        path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\contas.json"
        
        # Cria a instância de Tela de Dialogo
        tela_dialogo = File_Dialog()

        # Verifica se há pasta preferencial
        dir_dir_login = self.config.get('path_dir_login', dir_papiron )

        # Chama a tela de diálogo
        self.arquivo_tela = tela_dialogo.pathFile(dir_dir_login)

        # Se um arquivo foi selecionado
        if self.arquivo_tela:

            # Realiza o envio dos dados para um arquivo json
            try:
                dicts_logins = leitura_de_contas(self.arquivo_tela) 
                save_json(dicts_logins,path_file)       
                self.ui.l_info_progresso.setText("Arquivo de logins atualizado com sucesso!")

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
        self.progresso = self.progresso + value
        valor = int(self.progresso/total*100)
        self.ui.barra_progresso.setValue(valor)
        # self.ui.l_nome_aluno.setText(text_nome)
        # self.ui.l_nome_aluno.setStyleSheet("font-weight: bold;")
        # self.ui.l_info_progresso.setText(info)
    
    def voltar(self):
        btn_voltar(self)

    def sair(self):
        btn_sair(self)
      