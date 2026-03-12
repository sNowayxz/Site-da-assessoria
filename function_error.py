import traceback


def imprimir_erro(err,**kwargs):
    """
    Imprime na tela o erro e seu rastreio    
    """
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print(msg)
