from PyQt6.QtCore import QThread
import traceback

def thread_postar_atividades_40(self):
    from class_papiron.class_postar import Rotinas_PostarAtividades

    # Limpa a tabela de registros e o tempo da barra de progresso

    try:

        # Nunca sobrescreva dicionários diretamente:
        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        for i, curso in enumerate(self.cursos):

            # print("Inicio do Thread Rastreamento", curso)
            
            self.config['THREAD'] = i
            self.config['MÓDULO SITUAÇAO'] = self.modulo_situacao
            self.config['LISTA CURSOS']= curso
            self.config['MODULO'] = self.modulo
            self.config['MODULOS_ABERTOS'] =self.modulos_abertos
            t = str(i)

            # Atribui o Thread
            self.threads[t+'thread'+str(i)] = QThread()

            # Atribui o Worker
            print(f"THREAD_{i}  {curso}")
            self.workers[t+'[worker'+str(i)] = Rotinas_PostarAtividades(self.ui,self.config,curso,i)
            # Move o worker para dentro do Thread
            self.workers[t+'[worker'+str(i)].moveToThread(self.threads[t+'thread'+str(i)] )

            # Conecta o Thread com método
            self.threads[t+'thread'+str(i)] .started.connect(self.workers[t+'[worker'+str(i)].run_postar_atividades)

            # Conecta o sinal
            self.workers[t+'[worker'+str(i)].updateProgress_postar.connect(self.obter_progresso)
            
            # Quando o sinal finished do worker é emitido, o slot quit do thread é chamado,
            # o que faz com que o loop de eventos do thread pare e a execução da thread termine.
            self.workers[t+'[worker'+str(i)].finished.connect(self.threads[t+'thread'+str(i)].quit)
            # self.workers[t+'[worker'+str(i)].finished.connect(self.threads[t+'thread'+str(i)].wait)

            #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
            #  eles serão excluídos adequadamente da memória.            
            self.workers[t+'[worker'+str(i)].finished.connect(self.workers[t+'[worker'+str(i)].deleteLater)
            self.threads[t+'thread'+str(i)].finished.connect(self.threads[t+'thread'+str(i)].deleteLater)
            # self.threads[t+'thread'+str(i)].finished.connect(self.threads[t+'thread'+str(i)].quit)
            # self.threads[t+'thread'+str(i)].finished.connect(self.threads[t+'thread'+str(i)].wait)

            # Inicia o método do Worker no Thread
            self.threads[t+'thread'+str(i)].start()
            
            
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
        
    except AttributeError as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        return



def thread_postar_atividades(self):
    from class_papiron.class_postar import Rotinas_PostarAtividades

    # Limpa a tabela de registros e o tempo da barra de progresso

    try:

        # Nunca sobrescreva dicionários diretamente:
        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        for i, curso in enumerate(self.cursos):

            # print("Inicio do Thread Rastreamento", curso)
            
            self.config['THREAD'] = i
            self.config['MÓDULO SITUAÇAO'] = self.modulo_situacao
            self.config['LISTA CURSOS']= curso
            self.config['MODULO'] = self.modulo
            self.config['MODULOS_ABERTOS'] =self.modulo_abertos
            t = str(i)

            thread_key = f"thread_{i}"
            worker_key = f"worker_{i}"

            # Atribui o Thread
            self.threads[thread_key] = QThread(self)

            # Atribui o Worker
            print(f"THREAD_{i}  {curso}")
            self.workers[worker_key] = Rotinas_PostarAtividades(self.ui,self.config,curso,i)
            # Move o worker para dentro do Thread
            self.workers[worker_key].moveToThread(self.threads[thread_key] )

            # Conecta o Thread com método
            self.threads[thread_key] .started.connect(self.workers[worker_key].run_postar_atividades)

            # Conecta o sinal
            self.workers[worker_key].updateProgress_postar.connect(self.obter_progresso)
            
            # Quando o sinal finished do worker é emitido, o slot quit do thread é chamado,
            # o que faz com que o loop de eventos do thread pare e a execução da thread termine.
            self.workers[worker_key].finished.connect(self.threads[thread_key].quit)
            # self.workers[worker_key].finished.connect(self.threads[thread_key].wait)

            #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
            #  eles serão excluídos adequadamente da memória.            
            self.workers[worker_key].finished.connect(self.workers[worker_key].deleteLater)
            self.threads[thread_key].finished.connect(self.threads[thread_key].deleteLater)
            # self.threads[thread_key].finished.connect(self.threads[thread_key].quit)
            # self.threads[thread_key].finished.connect(self.threads[thread_key].wait)

            # Inicia o método do Worker no Thread
            self.threads[thread_key].start()
            
            
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
        
    except AttributeError as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        return
