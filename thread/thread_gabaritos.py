from PyQt6.QtCore import QThread
import traceback

from system.logger import log_grava

def thread_postar_gabaritos(self):
    from class_papiron.class_gabarito import RotinasGabarito

    try:

        self.threads = getattr(self, 'threads', {})
        self.workers = getattr(self, 'workers', {})

        for i, curso in enumerate(self.cursos):
            print(f"Início Thread: g_{i}")
            self.config['THREAD'] = i
            self.config['MÓDULO SITUAÇAO'] = self.modulos_situacao
            self.config['LISTA CURSOS']=curso
            self.config['MODULO'] = self.modulo
            self.config['MODULOS_ABERTOS'] =self.modulo_abertos

            thread_key = f"thread_{i}"
            worker_key = f"worker_{i}"

            # Atribui o Thread
            self.threads[thread_key] = QThread(self)

            # Atribui o Worker
            self.workers[worker_key] = RotinasGabarito(self.ui,self.config,curso,i)
            
            # Move o worker para dentro do Thread
            self.workers[worker_key].moveToThread(self.threads[thread_key] )

            # Conecta o Thread com método
            self.threads[thread_key] .started.connect(self.workers[worker_key].run_enviar_gabaritos)

            # Conecta o sinal
            # self.workers[worker_key].updateProgress.connect(self.prog)
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

        
            print(f"Rodando thread {i}\n")

    except Exception as err:

        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        # log_grava(msg="[INICIALIZANDO]:\n"+str(msg))
        print(msg)
        return

def thread_postar_gabaritos_chatGPT(self, cursos, i):

    from class_papiron.class_gabarito import RotinasGabarito

    try:
        thread_id = f"g_{i}"
        worker_key = f"worker{thread_id}"
        thread_key = f"thread{thread_id}"

        print(f"Início Thread: {thread_id}")
        self.config.update({
            'THREAD': thread_id,
            'MÓDULO SITUAÇAO': self.modulo_situacao,
            'LISTA CURSOS': cursos,
            'MODULO': self.modulo,
            'MODULOS_ABERTOS': self.modulos_abertos
        })
        # Atribui o Thread
        thread = QThread()

        # Atribui o Worker
        worker = RotinasGabarito(self.ui, cursos, self.modulo, self.username, self.password, thread_id, self.config)
        
        # Move o worker para dentro do Thread
        worker.moveToThread(thread)

        # Conecta o Thread com método
        thread.started.connect(worker.run_enviar_gabaritos)

        # Conecta o sinal
        worker.updateProgress.connect(self.atualizar_barra_progresso)

        # Quando o sinal finished do worker é emitido, o slot quit do thread é chamado,
        # o que faz com que o loop de eventos do thread pare e a execução da thread termine.    
        worker.finished.connect(thread.quit)
        worker.finished.connect(thread.wait)

        #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
        #  eles serão excluídos adequadamente da memória. 
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self.threads[thread_key] = thread
        self.workers[worker_key] = worker

        thread.start()
        print(f"Rodando thread {thread_id}\\n")

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(err=msg)
        print(msg)
