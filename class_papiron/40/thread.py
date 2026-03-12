# class FrontEnd(QWidget):
#     def __init__(self):
#         super().__init__()

#         ... # code as in your original

#         stop_flag = Event()    
#         self.timer_thread = TimerThread(stop_flag)
#         self.timer_thread.update.connect(self.update_ui)
#         self.timer_thread.start()


import threading
import time

def worker():
    """Função que será executada em uma thread."""
    print("Iniciando thread")
    # Simula um trabalho que demora alguns segundos
    for i in range(1,20):
        print(f"Trabalhando... ({i}/5)")
        time.sleep(1)
    print("Thread finalizada com sucesso!")

# Cria a thread
t = threading.Thread(target=worker)
# Inicia a thread
t.start()
# Espera a thread terminar para continuar a execução do programa principal
t.join()