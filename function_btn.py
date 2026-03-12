import ctypes
import traceback

def btn_voltar(self):
    
    try:
        from papiron import Window
        try:
            self.driver.quit()
        except:
            pass
        Window.hide(self)
        self.window = Window()
        self.window.show()

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        # log_grava(msg="[INICIALIZANDO]:\n"+str(msg))
        ctypes.windll.user32.MessageBoxW(0, "Houve um erro na execução do programa. Envie o último arquivo de log na pasta 'C:>NosConformes>main>LOG'","Erro de Execução",0)
        return

def btn_sair(self):
    from papiron import Window
    import sys
    Window.close(self)
    try:
        self.driver.quit()
    except:
        pass
    try:
        self.driver2.quit()
    except:
        pass
    try:
        self.driver3.quit()
    except:
        pass
    sys.exit()
