try:
    # Inicia os módulos para registrar as ações iniciais
    import ctypes
    import sys
    import time
    import traceback

    from system.logger import log_novo
    log_novo()
    # Processo inicializados
    from PyQt6.QtGui import *
    from PyQt6.QtWidgets import QApplication, QMainWindow

    from dict_lista_curso import verifica_inicial_dicts
    from system.logger import log_grava
    from system.pastas import verifica_pastas
    from inicializacao import verifica_arq_config, verifica_arq_modulo, verifica_css
    from window.window_papiron import Ui_PapironLab

    # Crie uma Janela Principal para exibição dos elementos com
    # atríbutos da Classe da Janela que deseja exibir
    class Window(QMainWindow):

        def __init__(self):
            try:
                super(Window, self).__init__()
                self.ui = Ui_PapironLab()
                self.ui.setupUi(self)
                self.ui.botao_cadastro_aluno.clicked.connect(self.tela_cadastro_aluno_)
                self.ui.botao_extrai_atividades.clicked.connect(self.tela_atividades_)
                self.ui.botao_extrai_atividades_responsivo.clicked.connect(self.tela_envio_)
                self.ui.botao_mensalistas.clicked.connect(self.tela_mensalistas_)
                self.ui.label_atualizacao.hide()
                self.inicializacao()
            
            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("[INICIALIZANDO] ERRO:\n"+str(msg))
                msg="[INICIALIZANDO] ERRO:\n"+str(msg)
                log_grava(msg=msg)
                time.sleep(20)
        
        def inicializacao(self):

            try:
                log_grava(msg="[INICIALIZAÇÃO]: Realizando os preparativos para construir os dados do APP.")
                verifica_pastas()
                verifica_arq_config()
                verifica_arq_modulo()
                verifica_inicial_dicts()
                verifica_css()
                log_grava(msg="[INICIALIZAÇÃO]: Procedimentos realizados com sucesso")
                
            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("[INICIALIZANDO]:\n"+str(msg))
                log_grava(msg="[INICIALIZANDO] ERRO:\n"+str(msg))
                time.sleep(20)

        def tela_atividades_(self):
            
            try:
                from tela.tela_atividades import Window_Atividades
                self.tela_atividades= Window_Atividades()
                Window.hide(self)
                self.tela_atividades.show()

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("[INICIALIZANDO]:\n"+str(msg))
                log_grava(msg="[INICIALIZANDO - TELA ATIVIDADES] ERRO:\n"+str(msg))
               
        
        def tela_envio_(self):            
            try:
                from tela.tela_envio import Window_Atividades
                self.tela_envio= Window_Atividades()
                Window.hide(self)
                self.tela_envio.show()

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("[INICIALIZANDO]:\n"+str(msg))
                log_grava(msg="[INICIALIZANDO - TELA ENVIO] ERRO:\n"+str(msg))
               

        def tela_cadastro_aluno_(self):

            try:
                from tela.tela_cadastro_alunos import Window_CadastroAlunos
                self.tela_cadastro_alunos= Window_CadastroAlunos()
                Window.hide(self)
                self.tela_cadastro_alunos.show()

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("[INICIALIZANDO]:\n"+str(msg))
                log_grava(msg="[INICIALIZANDO - TELA CADASTRO] ERRO:\n"+str(msg))
                ctypes.windll.user32.MessageBoxW(0, r"Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>PapironLab\Papiron\Log\'","Erro de Execução",0)

        def tela_mensalistas_(self):

            try:
                from tela.tela_mensalistas import Window_MensalistasAlunos
                self.tela_mensalistas= Window_MensalistasAlunos()
                Window.hide(self)
                self.tela_mensalistas.show()

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("[INICIALIZANDO]:\n"+str(msg))
                log_grava(msg="[INICIALIZANDO - TELA MENSALISTAS] ERRO:\n"+str(msg))
                ctypes.windll.user32.MessageBoxW(0, r"Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>PapironLab\Papiron\Log\'","Erro de Execução",0)



    # Chame a Classe da janela e a exiba em forma de looping:
    if __name__ == "__main__":
        from gui.css import STYLE
        app = QApplication(sys.argv)
        app.setStyleSheet(STYLE)
        window = Window()
        window.show()
        sys.exit(app.exec())

except Exception as err:
    import time
    import traceback

    msg = "".join(traceback.format_exception(
        type(err), err, err.__traceback__))
    print("Erro:"+str(msg))
    msg="[INICIALIZAÇÃO]:\n"+str(msg)
    log_grava(msg=msg)
    time.sleep(8)

    r"""
    ########## DADOS PARA CRIAR E MANIPULAR INTERFACE GRÁFICA ####
    QT Designer.exe, consegue através do pyqt6-tools ou Pyside6 (obtive deste último)

    >> Instalar pyuic5-tools    
        Exemplo:
        
            Transformar o arquivo *.ui para arquivo python *.py
            
                pyuic6 -x window\window_papiron.ui -o window\window_papiron.py
                pyuic6 -x window\window_cadastro_alunos.ui -o window\window_cadastro_alunos.py
                pyuic6 -x window\window_atividades.ui -o window\window_atividades.py
                pyuic6 -x window\window_mensalistas.ui -o window\window_mensalistas.py

                pyuic6 -x window\window_envio.ui -o window\window_envio.py 

                pyinstaller --windowed --noconfirm --collect-all reportlab.graphics.barcode papiron.py
                pyinstaller --noconfirm --collect-all reportlab.graphics.barcode papiron.py

                    NOTA: Nunca deve ser alterado "diretamente" o arquivo window_main.PY, 
                        sempre realize alterações no arquivo .UI, e em seguida transforme
                        para .PY 



    Rastrear Erros:
    """

# except Exception as err:
#     import time
#     import traceback
#     msg = "".join(traceback.format_exception(
#         type(err), err, err.__traceback__))
#     print("erro"+str(msg))
#     time.sleep(15)

