import copy
import traceback

from PyQt6.QtCore import QThread

from function_bd import save_json
from system.logger import log_grava
from system.system import t

def thread_atualizar_tela_atividades(self):
    from class_papiron.class_cadastro import Rotinas_AtualizarTelaAtividades

    print("Iniciou TA1")
    cont = 5
    run = True
    while cont:
        try:
            if not hasattr(self, 'thread1') or not run:
                self.thread1 = QThread(self)
                self.worker1 =  Rotinas_AtualizarTelaAtividades(self.ui)
                
                self.worker1.moveToThread(self.thread1)
                self.thread1.started.connect(self.worker1.run_atualizar_tela_atividades)

                self.worker1.finished.connect(self.thread1.quit)
                self.worker1.finished.connect(self.worker1.deleteLater)
                self.thread1.finished.connect(self.thread1.deleteLater)

                self.thread1.start()
                break
            else:
                print("Existe TA1 ativo")
                cont-=1
                self.thread1 = QThread()
                print("TT1",self.thread1.isRunning())
                run = self.thread1.isRunning()
  

        except Exception as err:
            import traceback
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            # log_grava(msg="[INICIALIZANDO]:\n"+str(msg))
            print(msg)
            # ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>NosConformes>main>LOG'","Erro de Execução",0)
            return

def thread_atualizar_tela_atividades_2(self):

    from class_papiron.class_cadastro import Rotinas_AtualizarTelaAtividades

    # print("Iniciou TA2")
    
    cont = 3
    run = True
    while cont:
        try:
            if not hasattr(self, 'thread2') or not run:
                self.thread2 = QThread(self)
                self.worker2 =  Rotinas_AtualizarTelaAtividades(self.ui)
                
                self.worker2.moveToThread(self.thread2)
                # print("Ligou T")
                self.thread2.started.connect(self.worker2.run_lista_atividades)

                self.worker2.finished.connect(self.thread2.quit)
                self.worker2.finished.connect(self.worker2.deleteLater)
                self.thread2.finished.connect(self.thread2.deleteLater)

                # Conecta o sinal
                # self.worker1.updateProgress.connect(self.prog)

                self.thread2.start()
                # print("Saiu T")
                break
            else:
                try:
                    print("Existe TA2 ativo: ", self.thread2.isRunning())
                    cont-=1
                    if not self.thread2.isRunning(): 
                        self.thread2 = QThread()
                except RuntimeError:
                    print("Existe thread2:", hasattr(self, 'thread2'))
                    self.thread2 = QThread()
                print("Existe TA2 atual: ", self.thread2.isRunning())
                run = self.thread2.isRunning()
        

        except Exception as err:
            import traceback
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            # log_grava(msg="[INICIALIZANDO]:\n"+str(msg))
            print(msg)
            # ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>NosConformes>main>LOG'","Erro de Execução",0)
            return

def thread_rastrear_atividades_legado(self):
    from class_papiron.class_atividades import Rotinas_RastrearAtividades
    import random
    
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
            self.workers[worker_key] = Rotinas_RastrearAtividades(self.ui, self.config)
            
            # Move o worker para dentro do Thread
            self.workers[worker_key].moveToThread(self.threads[thread_key] )

            # Conecta o Thread com método
            self.threads[thread_key] .started.connect(self.workers[worker_key].run_rastrear_atividades)

            # Conecta o sinal
            self.workers[worker_key].updateProgress.connect(self.obter_progresso)
            
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
        # self.ui.btn_voltar.setEnabled(False)
        # self.ui.btn_rastrear_atividades.setEnabled(False)
        # self.ui.btn_postar_atividades.setEnabled(False)
        # self.ui.btn_gabaritos.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
       
        # Deixa os elementos clicáveis novamente

        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_voltar.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_rastrear_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_postar_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_gabaritos.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.tableWidget.setEnabled(True))
        

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg=msg)
        print(msg)
        return

def thread_rastrear_atividades_r(self):
    from class_papiron.class_atividades import Rotinas_RastrearAtividades
        
    print("Inicio do Thread Rastreamento", len(self.lista_curso_disciplinas))

    try:
        # Nunca sobrescreva dicionários diretamente:
        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        for i, dict_do_processo in enumerate(self.lista_dicts_disciplinas,start=1):
        # i = 0
            print(f"Início Thread: thread_0"+str(i))
            
            config_thread = copy.deepcopy(self.config)  # <<< CÓPIA PROFUNDA

            config_thread['THREAD'] = i
            config_thread['MODULOS_ABERTOS'] = self.modulos_abertos
            config_thread['CURSOS_DISCIPLINAS'] = copy.deepcopy(dict_do_processo)
            config_thread['disciplina_unica'] = self.disciplina_unica
            
            thread_key = f"thread_{i}"
            worker_key = f"worker_{i}"

            # Atribui o Thread
            self.threads[thread_key] = QThread(self) 

            # Atribui o Worker
            self.workers[worker_key] = Rotinas_RastrearAtividades(self.ui, config_thread)
            
            # Move o worker para dentro do Thread
            self.workers[worker_key].moveToThread(self.threads[thread_key] )

            # Conecta o Thread com método
            self.threads[thread_key] .started.connect(self.workers[worker_key].run_rastrear_atividades_req)

            # Conecta o sinal
            self.workers[worker_key].updateProgress.connect(self.obter_progresso)
            
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
        # self.ui.btn_voltar.setEnabled(False)
        # self.ui.btn_rastrear_atividades.setEnabled(False)
        # self.ui.btn_postar_atividades.setEnabled(False)
        # self.ui.btn_gabaritos.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
       
        # Deixa os elementos clicáveis novamente

        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_voltar.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_rastrear_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_postar_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_gabaritos.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.tableWidget.setEnabled(True))
        

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg=msg)
        print(msg)
        return


def thread_rastrear_atividades_r_scg(self):
    from class_papiron.class_atividades import Rotinas_RastrearAtividades
    import random
    
    print("Inicio do Thread Rastreamento", len(self.ras))

    try:
        # Nunca sobrescreva dicionários diretamente:
        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        # for i, curso in enumerate(self.cursos):
        i = 0
        print(f"Início Thread: thread_0"+str(i))
        config_thr = copy.deepcopy(self.config)
        config_thr['THREAD'] = i
        config_thr['ALUNOS_RA'] = copy.deepcopy(self.ras)
        
        thread_key = f"thread_{i}"
        worker_key = f"worker_{i}"

        # Atribui o Thread
        self.threads[thread_key] = QThread(self) 

        # Atribui o Worker
        self.workers[worker_key] = Rotinas_RastrearAtividades(self.ui, config_thr)
        
        # Move o worker para dentro do Thread
        self.workers[worker_key].moveToThread(self.threads[thread_key] )

        # Conecta o Thread com método
        self.threads[thread_key] .started.connect(self.workers[worker_key].run_rastrear_atividades_scg)

        # Conecta o sinal
        self.workers[worker_key].updateProgress.connect(self.obter_progresso)
        
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
        # self.ui.btn_voltar.setEnabled(False)
        # self.ui.btn_rastrear_atividades.setEnabled(False)
        # self.ui.btn_postar_atividades.setEnabled(False)
        # self.ui.btn_gabaritos.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
       
        # Deixa os elementos clicáveis novamente

        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_voltar.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_rastrear_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_postar_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_gabaritos.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.tableWidget.setEnabled(True))
        

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg=msg)
        print(msg)
        return


def thread_rastrear_atividades_r_ect(self):
    from class_papiron.class_atividades import Rotinas_RastrearAtividades
    import copy
    
    print("Inicio do Thread Rastreamento ECT", len(self.ras))

    try:
        # Nunca sobrescreva dicionários diretamente:
        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        # for i, curso in enumerate(self.cursos):
        i = 0
        print(f"Início Thread: thread_0"+str(i))
        config_thread = copy.deepcopy(self.config)  # Cópia para o worker/thread
        config_thread['THREAD'] = i
        config_thread['ALUNOS_RA'] = copy.deepcopy(self.ras)
        thread_key = f"thread_{i}"
        worker_key = f"worker_{i}"

        # Atribui o Thread
        self.threads[thread_key] = QThread(self) 

        # Atribui o Worker
        self.workers[worker_key] = Rotinas_RastrearAtividades(self.ui, config_thread)
        
        # Move o worker para dentro do Thread
        self.workers[worker_key].moveToThread(self.threads[thread_key] )

        # Conecta o Thread com método
        self.threads[thread_key] .started.connect(self.workers[worker_key].run_rastrear_atividades_ect)

        # Conecta o sinal
        self.workers[worker_key].updateProgress.connect(self.obter_progresso)
        
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
        # self.ui.btn_voltar.setEnabled(False)
        # self.ui.btn_rastrear_atividades.setEnabled(False)
        # self.ui.btn_postar_atividades.setEnabled(False)
        # self.ui.btn_gabaritos.setEnabled(False)
        # self.ui.tableWidget.setEnabled(False)
       
        # Deixa os elementos clicáveis novamente

        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_voltar.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_rastrear_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_postar_atividades.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.btn_gabaritos.setEnabled(True))
        
        # self.threads[thread_key].finished.connect(
        #     lambda: self.ui.tableWidget.setEnabled(True))
        

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg=msg)
        print(msg)
        return

