
import os

def log_novo():
    from datetime import datetime
    date = "01/01/2050 00:00"
    date = datetime.strptime(date, '%d/%m/%Y  %H:%M').date()
    data_hoje = date.today()
    hoje = datetime.now()
    arquivo = str(data_hoje.year)+str(data_hoje.month).zfill(2)+str(data_hoje.day).zfill(2)
    dir_log = os.path.abspath(os.getcwd())+"\\log\\"
    path_log = dir_log+arquivo+".txt"
    #Cria diretório se não houver
    if not os.path.isdir(dir_log):
        os.mkdir(dir_log)
    #Cria arquivo de log diário, caso não exista ainda
    if not os.path.isfile(path_log):
        arquivo = open(path_log, 'w', encoding='utf-8')
        arquivo.close()
    else:
        with open(path_log,'a', encoding='utf-8') as arquivo:
            arquivo.writelines("\n=================================================================\
                                \n"+str(hoje.day).zfill(2)+"/"+str(hoje.month).zfill(2)+"/"+str(hoje.year)+" - "+str(hoje.hour).zfill(2)+":"+str(hoje.minute).zfill(2)+":"+str(hoje.second).zfill(2)+"\n")
        arquivo.close()

def log_grava(**kwargs):
    from datetime import datetime
    import traceback
    try:
        err = kwargs.get("err",None)
        if err:
            msg_err =  "".join(traceback.format_exception(type(err), err, err.__traceback__))
        else:
            msg_err = ""
        # msg = kwargs.get("msg","".join(traceback.format_exception(type(err), err, err.__traceback__)))
        
        msg = kwargs.get("msg","")
        
        date = "01/01/2050"
        date = datetime.strptime(date, '%d/%m/%Y').date()
        data_hoje = date.today()
        arquivo = str(data_hoje.year)+str(data_hoje.month).zfill(2)+str(data_hoje.day).zfill(2)
        dir_log = os.path.abspath(os.getcwd())+"\\log\\"
        path_log = dir_log+arquivo+".txt"
        log_text=msg+msg_err+"\n"
        date_hora = "01/01/2050 00:00"
        hora = datetime.strptime(date_hora, '%d/%m/%Y  %H:%M').date()
        hora = datetime.now()
        hora = str(hora.hour).zfill(2)+":"+str(hora.minute).zfill(2)+":"+str(hora.second).zfill(2)
        with open(path_log,'a', encoding='utf-8') as arquivo:
            arquivo.writelines("["+hora+"]"+log_text)
        arquivo.close()
    except Exception as err:
        msg_err =  "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg_err)