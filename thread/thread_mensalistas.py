import ctypes
import traceback

from PyQt6.QtCore import QThread

from function import log_grava


def update_progress(self, value):
    self.progresso = self.progresso + value

def thread_mensalistas(self):

    from class_papiron.class_mensalistas import Rotinas_AtualizaMensalistas
    
    try:
        self.thread = QThread(self)
        self.worker = Rotinas_AtualizaMensalistas(self.ui,self.config)
        
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_atualizar_dados_alunos)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.updateTela.connect(self.worker.lista_alunos_mensalistas)
        self.worker.updateBarra.connect(self.prog)

        # Quando o sinal finished do worker é emitido, o slot quit do thread é chamado,
        # o que faz com que o loop de eventos do thread pare e a execução da thread termine.    
        self.worker.finished.connect(self.thread.quit)
        # self.worker.finished.connect(self.thread.wait)

        #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
        #  eles serão excluídos adequadamente da memória. 
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        # Desliga os elementos
        self.ui.botao_voltar.setEnabled(False)
        # self.ui.botao_atualiza_cadastro.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
        # self.ui.tableWidget_dados.setEnabled(False)
        
        # Deixa os elementos clicáveis novamente
        # self.thread.finished.connect(
            # lambda: self.ui.botao_atualiza_cadastro.setEnabled(True))

        self.thread.finished.connect(
            lambda: self.ui.botao_voltar.setEnabled(True))
        
        self.thread.finished.connect(
            lambda: self.ui.tableWidget.setEnabled(True))
        
        # self.thread.finished.connect(
        #     lambda: self.ui.tableWidget_dados.setEnabled(True))

    except Exception as err:
        import traceback
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>PAPIRON>PAPIRON>LOG'","Erro de Execução",0)
        return


def thread_mensalistas_proc(self):

    from class_papiron.class_mensalistas import Rotinas_AtualizaMensalistas
              
    print("Inicio do Thread Rastreamento", self.cursos)

    try:
        # Nunca sobrescreva dicionários diretamente:
        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        for i, curso in enumerate(self.cursos):
            print(f"Início Thread: thread_0"+str(i))
            self.config['THREAD'] = i
            self.config['MÓDULO SITUAÇAO'] = self.modulo_situacao
            self.config['LISTA CURSOS']= curso
            self.config['MODULO'] = self.modulo
            self.config['MODULOS_ABERTOS'] =self.modulos_abertos
           
            thread_key = f"thread_{i}"
            worker_key = f"worker_{i}"

            # Atribui o Thread
            self.threads[thread_key] = QThread(self) 

            # Atribui o Worker
            self.workers[worker_key] = Rotinas_AtualizaMensalistas(self.ui,self.config)
            
            # Move o worker para dentro do Thread
            self.workers[worker_key].moveToThread(self.threads[thread_key] )

            # Conecta o Thread com método
            self.threads[thread_key].started.connect(self.workers[worker_key].run_atualizar_dados_alunos)

            # Conecta o sinal
            self.workers[worker_key].updateProgress_thread.connect(self.obter_progresso)
            
            # Quando o sinal finished do worker é emitido, o slot quit do thread é chamado,
            # o que faz com que o loop de eventos do thread pare e a execução da thread termine.
            self.workers[worker_key].finished.connect(self.threads[thread_key].quit)
            self.workers[worker_key].finished.connect(self.threads[thread_key].wait)

            #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
            #  eles serão excluídos adequadamente da memória.            
            self.workers[worker_key].finished.connect(self.workers[worker_key].deleteLater)
            self.threads[thread_key].finished.connect(self.threads[thread_key].deleteLater)

            # Inicia o método do Worker no Thread
            self.threads[thread_key].start()

        # Desliga os elementos
        self.ui.botao_voltar.setEnabled(False)
        # self.ui.botao_atualiza_cadastro.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
        # self.ui.tableWidget_dados.setEnabled(False)
        
        # Deixa os elementos clicáveis novamente
        # self.thread.finished.connect(
            # lambda: self.ui.botao_atualiza_cadastro.setEnabled(True))

        self.thread.finished.connect(
            lambda: self.ui.botao_voltar.setEnabled(True))
        
        self.thread.finished.connect(
            lambda: self.ui.tableWidget.setEnabled(True))
        
        # self.thread.finished.connect(
        #     lambda: self.ui.tableWidget_dados.setEnabled(True))

    except Exception as err:
        import traceback
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>PAPIRON>PAPIRON>LOG'","Erro de Execução",0)
        return

