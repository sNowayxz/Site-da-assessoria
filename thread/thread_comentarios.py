import traceback

from PyQt6.QtCore import QThread

from system.logger import log_grava


def thread_enviar_comentarios(self):
    from class_papiron.class_comentario import RotinasComentario
    
    print("Inicio do Thread Comentarios")

    try:
        self.threads = {}
        self.workers = {}

        for i, curso in enumerate(self.cursos):
            print(f"Início Thread: thread_{i}: {curso}\n\n")
            self.config['THREAD'] = i
            self.config['MODULOS_ABERTOS'] =self.modulos_abertos

            # Atribui o Thread
            self.threads['thread'+str(i)] = QThread(self) 

            # Atribui o Worker 
            self.workers['worker'+str(i)] = RotinasComentario(self.ui,self.config,curso,i)
            
            # Move o worker para dentro do Thread
            self.workers['worker'+str(i)].moveToThread(self.threads['thread'+str(i)] )

            # Conecta o Thread com método
            self.threads['thread'+str(i)] .started.connect(self.workers['worker'+str(i)].run_enviar_comentarios)

            # Conecta o sinal
            self.workers['worker'+str(i)].updateProgress.connect(self.obter_progresso)
            
            # Quando o sinal finished do worker é emitido, o slot quit do thread é chamado,
            # o que faz com que o loop de eventos do thread pare e a execução da thread termine.
            self.workers['worker'+str(i)].finished.connect(self.threads['thread'+str(i)].quit)
            self.workers['worker'+str(i)].finished.connect(self.threads['thread'+str(i)].wait)

            #  Precisa garantir que, após a conclusão do trabalho realizado pela thread e pelo worker,
            #  eles serão excluídos adequadamente da memória.            
            self.workers['worker'+str(i)].finished.connect(self.workers['worker'+str(i)].deleteLater)
            self.threads['thread'+str(i)].finished.connect(self.threads['thread'+str(i)].deleteLater)

            # Inicia o método do Worker no Thread
            self.threads['thread'+str(i)].start()
    

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg=msg)
        print(msg)
        return
