
import os
import traceback

from system.logger import log_grava


def localizar_desktop():
    import ctypes
    desktop_OS = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(0, 0x0000, 0, 0, desktop_OS)
    path_desktop = desktop_OS.value
    return path_desktop

def verifica_pastas(**kwargs):
    
    # Pasta Papiron na base na àrea de Trabalho
    path_desktop = localizar_desktop()
    path_papiron = path_desktop+'\\Papiron'
 
    # Desempacotando possíveis elementos
    curso = kwargs.get('curso', None)
    disciplina = kwargs.get('disciplina', None)
    modulo = kwargs.get('modulo', None)
    dir_pasta = kwargs.get('pasta', None) #insere outra pasta não específicada anteriormente
    drive = kwargs.get('drive', False)
    questionario = kwargs.get("questionario", False)

    # curso = curso.replace("EGRAD_","")

    # Verifica pasta
    if dir_pasta:
        try:
            if not os.path.isdir(dir_pasta):
                listas_pastas = dir_pasta.split("\\")
                pasta_parcial = ""
                for pasta in listas_pastas:
                    if pasta_parcial:
                        pasta_parcial = pasta_parcial + "\\" + pasta
                    else:
                        pasta_parcial = pasta

                    if not os.path.isdir(escapa_path(pasta_parcial)):
                        os.mkdir(escapa_path(pasta_parcial))

                return None
            else:
                # Pasta já existe
                pass
        except (PermissionError, OSError) as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg+"\n\n  Não foi possível criar a pasta no local indicado, verifique o caminho específicado")  

        return None
        

    if modulo:
        mod = modulo.replace("/","")
        if not os.path.isdir(escapa_path(path_papiron+'\\'+mod)):
            os.mkdir(escapa_path(path_papiron+'\\'+mod))
        
        # Verifica pasta de Atividades
        if not os.path.isdir(escapa_path(path_papiron+'\\'+mod+'\\Atividades')):
            os.mkdir(escapa_path(path_papiron+'\\'+mod+'\\Atividades'))

        # Verifica pasta do CURSO
        if not os.path.isdir(escapa_path(path_papiron+'\\'+mod+'\\'+curso)):
            os.mkdir(escapa_path(path_papiron+'\\'+mod+'\\'+curso))

        # Verifica pasta da DISCIPLINA
        if not os.path.isdir(escapa_path(path_papiron+'\\'+mod+'\\'+curso+'\\'+disciplina)):
            path = escapa_path(path_papiron+'\\'+mod+'\\'+curso+'\\'+disciplina)
            os.mkdir(path)
            os.mkdir(path+'\\Material')
        
        return None

    
    # Caso não seja passado nenhum parâmetro apenas verifica as pastas base do App
    # Verificando se as pastas do App estão Ok
    if not os.path.isdir(path_papiron):
        os.mkdir(path_papiron)

    if not os.path.isdir(path_papiron+'\\Downloads'):
        os.mkdir(path_papiron+'\\Downloads')
    
    # if not os.path.isdir(path_papiron+'\\Downloads\\Temp'):
        os.mkdir(path_papiron+'\\Downloads\\Temp')
    log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas Download e Temp criadas:\n   path: "+str(path_papiron+'\\Downloads'))
    
    # Verifica pasta de Livros Digitais    
    if not os.path.isdir(path_papiron+"\\Livros Digitais"):
        os.mkdir(path_papiron+"\\Livros Digitais")
        log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas Livros Digitais:\n   path: "+str(path_papiron+'\\Livros Digitais'))

    # Verifica pasta files    
    if not os.path.isdir(path_papiron+"\\files"):
        os.mkdir(path_papiron+"\\files")
        log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas suporte:\n   path: "+str(path_papiron+'\\files'))
    

    # Verifica as as pastas do BD
    dir_bd = os.path.abspath(os.getcwd())+"\\BD"
    dir_atividades = dir_bd+"\\atividades"
    dir_cursos = dir_bd+"\\cursos"
    dir_alunos = dir_bd+"\\alunos"
    
    if not os.path.isdir(dir_bd):
        os.mkdir(dir_bd)

    if not os.path.isdir(dir_atividades):
        os.mkdir(dir_atividades)
        log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas BD:\n   path: "+str(dir_atividades))

    if not os.path.isdir(dir_cursos):
        os.mkdir(dir_cursos)
        log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas BD:\n   path: "+str(dir_cursos))

    if not os.path.isdir(dir_alunos):
        os.mkdir(dir_alunos)
        log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas BD:\n   path: "+str(dir_alunos))



    log_grava(msg="[INICIALIZAÇÃO - PASTAS]: Pastas verificadas")

def escapa_path(path):
    import string

    # Evita que tire o ":" do "C:\"
    path = path[:5] + path[5:].replace(":", "-").replace("\n", "").replace("\t", "").replace("\b", "")
    
    # Cria lista de caracteres que devem ser removidos, exceto "-", ",", "_"
    escapas = string.punctuation.replace("\\", "").replace(".", "").replace("_", "")
    
    for escapa in escapas:
        if escapa != "-" and escapa != ",":
            path = path[:5] + path[5:].replace(escapa, "")
    
    return path

def escapa_palavras(palavra):
    import string

    # Evita que tire o":" do "C:\\""
    palavra = palavra.replace(":","-").replace("\n","").replace("\t","").replace("\b","")
    escapas = string.punctuation.replace("\\","").replace(".","")
    for escapa in escapas:
        if escapa != "-" and escapa != ",":
            palavra = palavra.replace(escapa,"")

    return palavra

def apagar_arquivos_pasta(path_dir):

    arquivos = os.listdir(path_dir)

    print(arquivos)
    
    # Iterar sobre os arquivos e apagar um por um
    for arquivo in arquivos:
        caminho_arquivo = os.path.join(path_dir, arquivo)
        print("CC: ", os.path.isdir(caminho_arquivo) ,caminho_arquivo)
        try:
            if os.path.isdir(caminho_arquivo):
                print("tentou")
                os.remove(caminho_arquivo)
                import time
                time.sleep(2)
                if os.path.isdir(caminho_arquivo):
                    print("não deu certo")
                else:
                    print("era para ter dado")

            else:
                print("tentou nãooooo")
        except Exception as err:
            import traceback
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg)
            pass

def verifica_OneDrive():  
    import os

    # Caminho para a pasta do Desktop do usuário
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

    # Caminho para a pasta do OneDrive do usuário
    onedrive_path = os.path.join(os.path.expanduser('~'), 'OneDrive')

    # Verifica se o caminho da pasta do Desktop está dentro do caminho da pasta do OneDrive
    if desktop_path.startswith(onedrive_path):
        return True
    else:
        return False

def diretorio_raiz():
    one_drive = verifica_OneDrive() 
    if not one_drive:
        dir_papiron = os.path.join(os.path.expanduser("~"), "Desktop\\Papiron")
    else:
        onedrive_folder = os.path.expanduser("~/OneDrive")  # substitua "~/OneDrive" pelo caminho da pasta do OneDrive, se for diferente
        desktop_folder = os.path.join(onedrive_folder, "Área de Trabalho")  # substitua "Área de Trabalho" pelo nome da pasta em português, se for diferente
        dir_papiron = desktop_folder+"\\Papiron"

    return dir_papiron

def pasta_mais_recente(path_dir):

    with os.scandir(path_dir) as entradas:
        pastas = [entrada.name for entrada in entradas if entrada.is_dir()]
        
    if not pastas:
        return None  # Retorna None se não há pastas
    
    # Encontrar a pasta mais recentemente modificada
    mais_recente = max(pastas, key=lambda pasta: os.path.getmtime(os.path.join(path_dir, pasta)))

    # print("mais recernt")
    
    return mais_recente+"\\"

def construir_path_chromedriver(n_thread):
    
    try:
        dir_chrome = os.path.join(os.path.expanduser("~"),"")+".wdm\\drivers\\chromedriver\\win64\\"
        dir_exe = dir_chrome+pasta_mais_recente(dir_chrome)+"chromedriver-win32\\"
        file_origin = dir_exe+"chromedriver.exe"
        file = dir_exe+"chromedriver"+n_thread+".exe"

        if not os.path.isfile(file_origin):
            # Caso tenha ocorrido erro e não tenha arquivo na pasta filha
            # tenta obter o arquivo na pasta pai
            dir_exe = dir_chrome+pasta_mais_recente(dir_chrome)+"\\"
            file_origin = dir_exe+"chromedriver.exe"
            file = dir_exe+"chromedriver"+n_thread+".exe"
    except TypeError:
        raise TypeError

    return file , file_origin


def definir_sufixo_legado(nome_curso,disciplina,questionario,**kwargs):

    lista_saude = [
        "BIOMEDICINA",
        "ENFERMAGEM",
        "NUTRIÇÃO",
        "FISIOTERAPIA",
        "FARMÁCIA", "FARMACIA",
        "ESTÉTICA", "ESTETICA",
        "TERAPIA OCUPACIONAL",
        "INTEGRATIVA",
        "PODOLOGIA",
        "RADIOLOGIA"
    ]

    lista_engenharia = [
        "ENGENHARIA",
        "INDUSTRIAL",
        "AGRONOMIA",
        "ARQUITETURA"
    ]

    if nome_curso == "GERAL" or ("ESTUDO CONTEMPORÂNEO E TRANSVERSAL" in disciplina or 
                        "FORMAÇÃO SOCIOCULTURAL E ÉTICA" in disciplina):
        # Estes questionários são separados, por isso não tem o sufixo 
        sufixo = "\\AA - ATIVIDADES COMPLEMENTARES"

        if "PROJETO DE ENSINO" in disciplina.upper():
            sufixo = sufixo+"\\PROJETO DE ENSINO"
        
        elif "NIVELAMENTO" in disciplina.upper():
            sufixo = sufixo+"\\NIVELAMENTO\\"+disciplina
        
        elif "TRANSVERSAL" in disciplina.upper():
            sufixo = sufixo+"\\ECT\\"+disciplina
        
        elif "FORMAÇÃO SOCIOCULTURAL" in disciplina.upper():
            sufixo = sufixo+"\\FSCE\\"+disciplina

        elif "PREPARE-SE" in disciplina.upper():
            sufixo = sufixo+"\\PREPARE-SE"
    
    else:
        sufixo = ""

        # Verfirica a pasta filha
        if "ESTÁGIO" in disciplina.upper():
            sufixo = sufixo+"\\AA - ESTÁGIO"

        elif "IMERSÃO" in disciplina.upper():
            sufixo = sufixo+"\\AA - IMERSÃO"
            
        elif any(curso_saude in nome_curso for curso_saude in lista_saude):
            sufixo = sufixo+"\\AA - SAÚDE e BEM-ESTAR"
        
        elif any(curso_engenharia in nome_curso for curso_engenharia in lista_engenharia):
            sufixo = sufixo+"\\AA - ENG"
        
        # Insere a informação se é questionário ou não
        sufixo = sufixo+"\\AA - QUESTIONARIOS" if questionario else sufixo

    return sufixo


def definir_sufixo(nome_curso,disciplina,questionario,**kwargs):

    lista_saude = [
        "BIOMEDICINA",
        "ENFERMAGEM",
        "NUTRIÇÃO",
        "FISIOTERAPIA",
        "FARMÁCIA", "FARMACIA",
        "ESTÉTICA", "ESTETICA",
        "TERAPIA OCUPACIONAL",
        "INTEGRATIVA",
        "PODOLOGIA",
        "RADIOLOGIA"
    ]

    lista_engenharia = [
        "ENGENHARIA",
        "INDUSTRIAL",
        "AGRONOMIA",
        "ARQUITETURA"
    ]

    if nome_curso == "GERAL" or ("ESTUDO CONTEMPORÂNEO E TRANSVERSAL" in disciplina or 
                        "FORMAÇÃO SOCIOCULTURAL E ÉTICA" in disciplina):
        # Estes questionários são separados, por isso não tem o sufixo 
        sufixo = "\\AA - ATIVIDADES COMPLEMENTARES"

        if "PROJETO DE ENSINO" in disciplina.upper():
            sufixo = sufixo+"\\PROJETO DE ENSINO"
        
        elif "NIVELAMENTO" in disciplina.upper():
            sufixo = sufixo+"\\NIVELAMENTO\\"+disciplina
        
        elif "TRANSVERSAL" in disciplina.upper():
            sufixo = sufixo+"\\ECT\\"+disciplina
        
        elif "FORMAÇÃO SOCIOCULTURAL" in disciplina.upper():
            sufixo = sufixo+"\\FSCE\\"+disciplina

        elif "PREPARE-SE" in disciplina.upper():
            sufixo = sufixo+"\\PREPARE-SE"
    
    else:
        sufixo = ""

        # Verfirica a pasta filha
        if "ESTÁGIO" in disciplina.upper():
            sufixo = sufixo+"\\AA - ESTÁGIO"

        elif "IMERSÃO" in disciplina.upper():
            sufixo = sufixo+"\\AA - IMERSÃO"

        elif "CONCLUSÃO DE CURSO" in disciplina.upper():
            sufixo = sufixo+"\\AA - TCC"
        
        elif "TCC" in disciplina.upper():
            sufixo = sufixo+"\\AA - TCC"

        elif "TÉCNICO" in nome_curso.upper() or "PROFISSIONALIZANTE" in nome_curso.upper() :
            sufixo = sufixo+"\\AA - CURSOS TÉCNICOS E PROFISSIONALIZANTE"

        elif "PÓS-" in nome_curso.upper():
            sufixo = sufixo+"\\AA - PÓS-GRADUAÇÃO"

        elif any(curso_saude in nome_curso for curso_saude in lista_saude):
            sufixo = sufixo+"\\AA - SAÚDE e BEM-ESTAR"
        
        elif any(curso_engenharia in nome_curso for curso_engenharia in lista_engenharia):
            sufixo = sufixo+"\\AA - ENG"
        
        # Insere a informação se é questionário ou não
        sufixo = sufixo+"\\AA - QUESTIONARIOS" if questionario else sufixo

    return sufixo[1:]

def renomear_drive(modulo):

    # Caminho base onde está a pasta "drive"
    base_path = rf"C:\Users\blitz\Desktop\Papiron\{modulo}\drive"

    # Prefixo que será removido
    prefix_to_remove = "EGRAD_"

    # Percorre todos os diretórios e arquivos
    for root, dirs, files in os.walk(base_path, topdown=False):
        # Renomeia arquivos
        for filename in files:
            if filename.startswith(prefix_to_remove):
                old_path = os.path.join(root, filename)
                new_filename = filename[len(prefix_to_remove):]
                new_path = os.path.join(root, new_filename)
                os.rename(old_path, new_path)
                print(f"Arquivo renomeado: {filename} -> {new_filename}")

        # Renomeia diretórios
        for dirname in dirs:
            if dirname.startswith(prefix_to_remove):
                old_dir = os.path.join(root, dirname)
                new_dirname = dirname[len(prefix_to_remove):]
                new_dir = os.path.join(root, new_dirname)
                os.rename(old_dir, new_dir)
                print(f"Pasta renomeada: {dirname} -> {new_dirname}")

