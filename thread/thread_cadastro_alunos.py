import ctypes
import traceback

from PyQt6.QtCore import QThread

from function import log_grava


def update_progress(self, value):
    self.progresso = self.progresso + value

def thread_atualizar_dados_alunos(self):

    from class_papiron.class_cadastro import Rotinas_AtualizaCadastro
    
    try:
        self.thread = QThread(self)
        self.worker = Rotinas_AtualizaCadastro(self.ui,self.config)
        
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_atualizar_dados_alunos)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.updateTela.connect(self.lista_alunos_cadastrados)
        self.worker.updateBarra.connect(self.prog)
        self.thread.start()

        # Desliga os elementos
        self.ui.botao_voltar.setEnabled(False)
        self.ui.botao_atualiza_cadastro.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
        # self.ui.tableWidget_dados.setEnabled(False)
        
        # Deixa os elementos clicáveis novamente
        self.thread.finished.connect(
            lambda: self.ui.botao_atualiza_cadastro.setEnabled(True))

        self.thread.finished.connect(
            lambda: self.ui.botao_voltar.setEnabled(True))
        
        self.thread.finished.connect(
            lambda: self.ui.tableWidget.setEnabled(True))
        
        # self.thread.finished.connect(
        #     lambda: self.ui.tableWidget_dados.setEnabled(True))

    except Exception as err:
        import traceback
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg="[THREAD CADASTRO]:\n"+str(msg))
        print(msg)
        ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>PAPIRON>PAPIRON>LOG'","Erro de Execução",0)
        return

def thread_atualizar_dados_alunos_dev(self, cursos):
    from class_papiron.class_cadastro import Rotinas_AtualizaCadastro

    # Limpa a tabela de registros e o tempo da barra de progresso
    self.ui.barra_progresso.setValue(0)
    self.progresso = 0

    try:
        self.threads = {}
        self.workers = {}
      
        for i in range (len(cursos)):
            print(f"Início Thread: thread_0"+str(i))
            self.config['THREAD'] = i
            self.config['LISTA CURSOS']= cursos[i] 

            # Atribui o Thread
            self.threads['thread'+str(i)] = QThread()

            # Atribui o Worker
            self.worker = Rotinas_AtualizaCadastro(self.ui,self.config)
            
            # Move o worker para dentro do Thread
            self.workers['worker'+str(i)].moveToThread(self.threads['thread'+str(i)] )

            # Conecta o Thread com método
            self.threads['thread'+str(i)] .started.connect(self.workers['worker'+str(i)].run_atualizar_dados_alunos)

            # Conecta o sinal
            self.workers['worker'+str(i)].updateProgress.connect(self.prog)

            # Libera um processo para realizar a postagem
            self.workers['worker'+str(i)].finished.connect(self.libera_postar)
            
            # Quando o sinal finished do worker é emitido.
            # realiza a atualização da tela e da barra
            self.workers['worker'+str(i)].upateTela.connect(self.lista_alunos_cadastrados)
            self.workers['worker'+str(i)].updateBarra.connect(self.prog)

            #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
            #  eles serão excluídos adequadamente da memória.            
            self.workers['worker'+str(i)].finished.connect(self.workers['worker'+str(i)].deleteLater)
            self.threads['thread'+str(i)].finished.connect(self.threads['thread'+str(i)].deleteLater)

            # Inicia o método do Worker no Thread
            self.threads['thread'+str(i)].start()
        
        
        # Desliga os elementos

        # self.ui.btn_voltar.setEnabled(False)
        # self.ui.btn_rastrear_atividades.setEnabled(False)
        # self.ui.btn_postar_atividades.setEnabled(False)
        # self.ui.btn_gabaritos.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
       
        # Deixa os elementos clicáveis novamente

        # self.threads['thread'+str(i)].finished.connect(
        #     lambda: self.ui.btn_voltar.setEnabled(True))
        
        # self.threads['thread'+str(i)].finished.connect(
        #     lambda: self.ui.btn_rastrear_atividades.setEnabled(True))
        
        # self.threads['thread'+str(i)].finished.connect(
        #     lambda: self.ui.btn_postar_atividades.setEnabled(True))
        
        # self.threads['thread'+str(i)].finished.connect(
        #     lambda: self.ui.btn_gabaritos.setEnabled(True))
        
        # self.threads['thread'+str(i)].finished.connect(
        #     lambda: self.ui.tableWidget.setEnabled(True))
        

    except Exception as err:

        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        # log_grava(msg="[INICIALIZANDO]:\n"+str(msg))
        print(msg)
        ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa.",0)
        return
