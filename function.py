import fnmatch
import json
import os
import shutil
import time
import traceback
from datetime import datetime

from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    JavascriptException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from class_papiron.class_error import BrainlyError, DisciplinaError, MaterialError
from system.system import t
from dict_lista_curso import dict_curso_sigla
from function_bd import abre_json, save_json
from system.chrome import atualizar_soup, f5, iniciar_sesssao_chrome, login, ult_div
from functions.curso import dict_curso
from system.logger import log_grava
from system.pastas import (
    definir_sufixo_legado,
    escapa_palavras,
    escapa_path,
    verifica_pastas,
)
from function_tela_atividades import progresso_lista
from class_papiron.class_dados_aluno import Disciplina

URL_AVISO = "https://studeo.unicesumar.edu.br/#!/access/rules"

# DECORADOR
from functools import wraps

def rename_download_file(filename):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            path = result['path']
            if os.path.exists(path):
                new_path = os.path.join(os.path.dirname(path), filename)
                os.rename(path, new_path)
                result['path'] = new_path
            return result
        return wrapper
    return decorator

def entra_disciplina(driver,disciplina):
    """
    Clica na Disciplina do curso
    """
    repetir = True
    cont = 3
    while repetir:

        try:
            driver.find_element(By.XPATH, f'//span[contains(text(), "{disciplina.disciplina}")]')

            target_element = driver.find_element(By.XPATH, f'//span[contains(text(), "{disciplina.disciplina}")]')

            # Simulate a click on the element
            driver.execute_script("arguments[0].click();", target_element)

            break

        except NoSuchElementException:
            print(f"         > Aguardar 4s para tentar encontrar a disciplina no painel: {disciplina.disciplina}")
            t(4)

            # Find the <a> element that contains the target_text
            print(f"\n\n xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n\n      AQUI DEU ERRO - {disciplina.disciplina}      \n\n  xxxxxxxxxxxxxxxxxxxxxxxXXXXXXXXXXXXXXXXXXX")
        
        except Exception as err:
            t(4)
            log_grava(err=err)

        cont -= 1
        if cont:
            break

def entra_disciplina_painel(driver,disciplina):

    import re
    from bs4 import BeautifulSoup

    # Parâmetros que você quer localizar
    nome_desejado = disciplina.disciplina
    modulo_desejado = disciplina.modulo
    padrao_ano_modulo = re.compile(r'^\d{4}/\d{2}$')

    # Pega o HTML da página atual
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Encontra todos os cards de disciplinas matriculadas
    cards = soup.find_all('div', class_='card-disciplina')

    encontrado = False

    for card in cards:
        # Pega o nome da disciplina
        nome_tag = card.find('span', class_='bold all-caps font-montserrat ng-binding')
        nome_disciplina = nome_tag.text.strip() if nome_tag else ''

        # Busca todos os <p> para localizar o Ano/Módulo
        p_tags = card.find_all('p', class_='all-caps font-montserrat semi-bold no-margin ng-binding')

        ano_modulo = None
        for p in p_tags:
            texto = p.text.strip()
            if padrao_ano_modulo.match(texto):
                ano_modulo = texto
                break
        
        # Essas disciplinas não contém módulo próprio
        if any(keyword in disciplina.disciplina for keyword in [
            "SEMANA DE CONHECIMENTOS GERAIS",
            "PROJETO DE ENSINO",
            "PREPARE-SE"
            ]):
            ano_modulo = modulo_desejado
       
        # Confere se ambos batem
        if nome_disciplina == nome_desejado and ano_modulo == modulo_desejado:
            print(f"    >> Encontrada: {nome_disciplina} - {ano_modulo}")

            # Pega o <a> associado e o atributo aria-label
            link_tag = card.find('a')
            if link_tag:
                aria_label = link_tag.get('aria-label')
                # print(f"Clicando no link com aria-label: {aria_label}")

                # Usa Selenium para encontrar e clicar
                elemento = driver.find_element('xpath', f"//a[@aria-label=\"{aria_label}\"]")
                driver.execute_script("arguments[0].click();", elemento)
                encontrado = True
                break

    if not encontrado:
        print("❌ Não foi encontrada a disciplina desejada com o módulo especificado.")

def entra_atividade(driver, atividade):
    """
    Clica na Atividade da Disciplina
    """
    try:
        target_element = driver.find_element(By.XPATH, f'//p[contains(text(), "{atividade}")]')
        driver.execute_script("arguments[0].click();", target_element)
        css_titulo_atividade = "div.panel-title.cursor.ng-binding"
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_titulo_atividade)))
        return True

    except TimeoutException:
        print("\n\nNão foi POSSÍVEL identificar os elementos necessários da Atividade!", atividade,"\n\n\n")
        driver.back()
        return False

def entra_atividade_xpath(driver, atividade):
    """
    Clica na Atividade da Disciplina
    """
    cont = 3
    while cont:
        try:
            t(2)
            atividade.click() 
            ult_div(driver=driver)
            soup = atualizar_soup(driver=driver)
            if "QUESTÃO 1" in soup.text or "Questão 1" in soup.text:
                print("        -> Achou Questão 1")
                return True

            css_titulo_atividade = "div.panel-title.cursor.ng-binding"
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_titulo_atividade)))
            return True

        except TimeoutException:
            cont -= 1
            try:
                print("\nERRO: Ainda não foi POSSÍVEL identificar os elementos necessários da Atividade!\n")



                atividade.click()
                css_titulo_atividade = "div.panel-title.cursor.ng-binding"
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_titulo_atividade)))
                return True

            except TimeoutException:
                cont -= 1
                print("\n\nNão foi POSSÍVEL de fato identificar os elementos necessários da Atividade!\n")
                driver.back()
                return False
        
        except StaleElementReferenceException:
            cont -= 1
            print("   Tentou clicar com Script")
            driver.execute_script("arguments[0].click();", atividade)

        except ElementClickInterceptedException:
            print("   Tentou clicar com Script [2]")
            driver.maximize_window()
            driver.execute_script("arguments[0].click();", atividade)

    return False

def entra_atividade_script(driver, atividade):
    """
    Clica na Atividade da Disciplina
    """
    cont = 3
    while cont:
        try:
            driver.execute_script("arguments[0].click();", atividade)
            print("     -->> Acabou de clicar")
            ult_div(driver=driver)
            soup = atualizar_soup(driver=driver)
            
            if "QUESTÃO 1" in soup.text or "Questão 1" in soup.text:
                print("        -> Achou Questão 1")
                return True

            css_titulo_atividade = "div.panel-title.cursor.ng-binding"
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_titulo_atividade)))
            return True

        except TimeoutException:
            cont -= 1
        
        except StaleElementReferenceException:
            cont -= 1
            print("   Tentou clicar com Script")
            driver.execute_script("arguments[0].click();", atividade)

    return False

def escape_html(texto:str):
    texto = str(texto).replace("\n"," ").replace("\\xa0"," ").replace("\\xa1"," ").replace("\\u200b"," ").replace("\xa0"," ").replace("\u200b"," ").replace("\xa1"," ")
    # .replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&quot;","\"").
    return str(texto)

def verifica_aviso(driver):
    """
    Verifica se aparece o AVISO principalmente após o login
    """
    # print("Inicia verificação de AVISO.", driver.current_url)
    url_aviso = "https://studeo.unicesumar.edu.br/#!/access/rules"
    t(1)
    ult_div(driver)
    T=30
    dt = 1 # Não utilizar float, pois com as iterações o número T começa a ter casas decimais 
    while T:
        try:
            if driver.current_url == url_aviso:
                xpath_btn = "//button[@ng-click='$ctrl.pularRegras()']" 
                wait = WebDriverWait(driver,0.1)
                btn_aviso = wait.until(EC.presence_of_element_located((By.XPATH,xpath_btn)))
                # print("  > Localizou Aviso!")
                driver.execute_script("arguments[0].click();", btn_aviso)
                return True
        except TimeoutException:
            pass
        T-=dt
        time.sleep(dt/10)

    # print("  > Aviso NÃO Localizado!")
    return False

def atualiza_lista_sigla_nome():

    # gera a lista de cursos e nomes de cursos, p.e, 'Graduação de Administração' : 'Administração',
    path_file = os.getcwd()+'\\BD\\cursos\\curso_nome.json'
    try:
        with open(path_file, encoding='utf-8') as json_file:
            curso_nome = json.load(json_file)
    except:
        curso_nome = {}

    # gera a lista de cursos e nomes de cursos, p.e, 'Graduação de Administração' : 'ADM',
    path_file_1 = os.getcwd()+'\\BD\\cursos\\curso_sigla.json'
    try:
        with open(path_file_1, encoding='utf-8') as json_file:
            curso_sigla = json.load(json_file)
    except:
        curso_sigla = {}

    # Atualiza arquivo sigla nome
    path_file_2 = os.getcwd()+'\\BD\\cursos\\curso_sigla_nome.json'

    data = {}
    for sigla in curso_sigla:
        data[curso_sigla[sigla]]=curso_nome[sigla]

    save_json(data,path_file_2)
    
def novo_curso(novo):
    # Obtem os registros salvos do usuário
    path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
    data = abre_json(path_file)

    # Se não tiver cria o dado de user_code
    if not "user_code" in data:
        import random
        n=str(random.randint(1000,9999))
        data["user_code"]=n
    save_json(data=data,path_file=path_file)

    # Verifica a existência da pasta
    verifica_pastas(pasta=os.path.abspath(os.getcwd())+"\\BD\\compartilhados")

    path_file = os.path.abspath(os.getcwd())+"\\BD\\compartilhados\\novo_curso_"+data["user_code"]+".txt"
    if not os.path.isfile(path_file):
        with open(path_file, 'w', encoding='utf-8') as arquivo:
            arquivo.close()
    
    with open(path_file, 'a', encoding='utf-8') as arquivo:
        arquivo.writelines(novo+"\n")
    arquivo.close()

def registra_curso(nome_curso:str) -> str:
    """
    Registra provisoriamente um novo curso

    ##### ARGS:
    - nome_curso -> nome completo do curso
    """

    # CRIA SIGLA TEMP
    sigla_list = nome_curso.split()
    novo_curso(nome_curso)

    if sigla_list[len(sigla_list)-2].upper() in ["DE","DA","DO"]:
        sigla = sigla_list[len(sigla_list)-1][:3].upper()
        apelido = sigla_list[len(sigla_list)-3]+" "+sigla_list[len(sigla_list)-2]+" "+sigla_list[len(sigla_list)-1]
        apelido = apelido.upper()
    else:
        sigla = sigla_list[len(sigla_list)-1][:3].upper()
        apelido = sigla_list[len(sigla_list)-1].upper()

    path_file_curso_nome = os.path.abspath(os.getcwd())+'\\BD\\cursos\\curso_nome.json'
    path_file_curso_sigla_nome = os.path.abspath(os.getcwd())+'\\BD\\cursos\\curso_sigla_nome.json'
    path_file_curso_sigla = os.path.abspath(os.getcwd())+'\\BD\\cursos\\curso_sigla.json'

    # Atualiza o arquivo CURSO_NOME
    with open(path_file_curso_nome, encoding='utf-8') as json_file:
        data_curso_nome = json.load(json_file)
    data_curso_nome[nome_curso] = apelido
    save_json(data_curso_nome,path_file_curso_nome)


    # Atualiza o arquivo SIGLA_NOME
    with open(path_file_curso_sigla_nome, encoding='utf-8') as json_file:
        data_curso_sigla_nome = json.load(json_file)
    data_curso_sigla_nome[sigla] = apelido
    save_json(data_curso_sigla_nome, path_file_curso_sigla_nome)

    # Atualiza o arquivo CURSO_SIGLA
    with open(path_file_curso_sigla, encoding='utf-8') as json_file:
        data_curso_sigla = json.load(json_file)
    data_curso_sigla[nome_curso] = sigla
    save_json(data_curso_sigla, path_file_curso_sigla)

    return sigla

def lista_cursos_atividades() -> list:
    """
    Retorna em lista a sigla de todos os cursos, em ordem alfabética
    """
    
    # Dados dos cursos curso->sigla
    # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla.json"
    # with open(path_file_curso, encoding='utf-8') as json_file:
    #     cursos = json.load(json_file)
    
    cursos = dict_curso(opcao=6)

    lista_cursos = []

    for curso in cursos:
        lista_cursos.append(cursos[curso])
    
    lista_cursos = sorted(lista_cursos)

    return lista_cursos

def separa_contas(divisao:int):
    """
    Separa os cursos de acordo com a quantidade de alunos cadastrados em cada curso
    Assim há um equilíbrio entre a repartição das lista

    - divisao: int, informa a quantidade de listas a serem retornadas
    """
    
    # Dados dos alunos
    path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
    with open(path_file, encoding='utf-8') as json_file:
        alunos = json.load(json_file)
    
    # Obtém Sigla dos cursos
    cursos = dict_curso(opcao=6)

    # Verifica o número a relação de contas x curso
    lista_cursos = {}
    num_contas = 0

    for ra in alunos:
        # Dados do aluno
        curso = alunos[ra]['CURSO']
        verifica_senha = alunos[ra]['SENHA_OK']

        if  verifica_senha == "OK": 
            lista_cursos[curso] = (lista_cursos[curso] + 1) if curso in lista_cursos else 1
            num_contas += 1
        
    # Coloca a lista em ordem crescente pela quantidade de contas em cada curso
    lista_cursos = dict(sorted(lista_cursos.items(), key=lambda x: x[1]))

    cursos_separados = []
    for i in range(divisao):
        cursos_separados.append([])

    # Verifica o tamanho de cada lista gerada, quantos cadastros tem cada lista
    for i, curso in enumerate(lista_cursos):
        try:
            cursos_separados[i%divisao].append(cursos[curso])
        except KeyError:
            pass
    
    len_separados = []
    for tamanho in cursos_separados:
        len_separados.append(len(tamanho))
 
    print(f" nº contas:{num_contas} -> CURSOS: {len(cursos_separados)} - {cursos_separados}")
    return cursos_separados, num_contas

def separa_contas_alunos(divisao:int):
    """
    Ainda tenho que desenvolver essa parte
    
    - divisao: int, informa a quantidade de listas a serem retornadas
    """
    
    # Dados dos alunos
    path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno.json"
    with open(path_file, encoding='utf-8') as json_file:
        alunos = json.load(json_file)

    # Dados dos cursos curso->sigla
    # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla.json"
    # with open(path_file_curso, encoding='utf-8') as json_file:
    #     cursos = json.load(json_file)
    cursos = dict_curso(opcao=6)

    # Verifica o número a relação de contas x curso
    lista_cursos = {}
    num_contas = 0

    for aluno in alunos:
        # Dados do aluno
        curso = alunos[aluno]['CURSO']
        verifica_senha = alunos[aluno]['SENHA_OK']
        situacao = alunos[aluno]['SITUAÇÃO']

        if  verifica_senha == "OK" and\
            situacao == "CURSANDO":
            
            if curso in lista_cursos:
                lista_cursos[curso] = lista_cursos[curso] + 1 
            else:
                lista_cursos[curso] = 1

            num_contas += 1
        

    # Coloca a lista em ordem crescente pela quantidade de contas em cada curso
    lista_cursos = dict(sorted(lista_cursos.items(), key=lambda x: x[1]))

    
    cursos_separados = []
    for i in range(divisao):
        cursos_separados.append([])

    # Verifica o tamanho de cada lista gerada, quantos cadastros tem cada lista
    len_separados = []
    for i, curso in enumerate(lista_cursos):
        cursos_separados[i%divisao].append(cursos[curso])
    
    for tamanho in cursos_separados:
        len_separados.append(len(tamanho))

    return cursos_separados, num_contas

def separa_contas2():
    
    # Dados dos alunos
    path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno.json"
    with open(path_file, encoding='utf-8') as json_file:
        alunos = json.load(json_file)

    # Dados dos cursos curso->sigla
    # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla.json"
    # with open(path_file_curso, encoding='utf-8') as json_file:
        # cursos = json.load(json_file)

    # Verifica o número a relação de contas x curso
    lista_cursos = {}
    num_contas = 0

    for aluno in alunos:
        # Dados do aluno
        curso = alunos[aluno]['CURSO']
        verifica_senha = alunos[aluno]['SENHA_OK']
        situacao = alunos[aluno]['SITUAÇÃO']

        if  verifica_senha == "OK" and\
            situacao == "CURSANDO":
            
            if curso in lista_cursos:
                lista_cursos[curso] = lista_cursos[curso] + 1 
            else:
                lista_cursos[curso] = 1

            num_contas += 1

def separa_cursos(cursos:list , n:int):

    # Calcula o tamanho de cada sublista. Note que isso pode resultar em algumas sublistas
    # tendo um item a mais do que outras se o tamanho de 'lista' não for divisível por 'n'
    k = len(cursos)
    tamanho_sublista = (k + n - 1) // n  # Arredonda para cima para garantir que todos os itens sejam incluídos
    
    # Cria as sublistas usando compreensão de lista e fatiamento
    sublistas = [cursos[i*tamanho_sublista:(i+1)*tamanho_sublista] for i in range(n)]
    
    return sublistas

def situacao_aluno(**kwargs) -> None:
    """
    Salva no BD as informações relativas a:
        - Dados Cadastrais
        - Status das disciplinas
    """
    import json

    aluno_nome = kwargs.get('aluno_nome',None)
    ra = kwargs.get('ra',None)
    senha = kwargs.get('senha',None)
    senha_ok = kwargs.get('senha_ok','OK')
    curso = kwargs.get('curso',None)
    disciplinas = kwargs.get('disciplinas',None)

    # Abre arvuivo de Alunos BD
    cont = 3
    while cont:
        try:
            path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
            if not os.path.isfile(path_file):
                alunos = {}
                with open(path_file, 'w', encoding='utf-8') as f:
                    json.dump(alunos, f ,ensure_ascii=False)
            else:
                with open(path_file, encoding='utf-8') as json_file:
                    alunos = json.load(json_file)
            break
        except json.JSONDecodeError:
            # Em casos de duplicidade de acesso ao BD
            cont-=1
            time.sleep(5)

    # Espelha os dados do BD de alunos em um espelho
    alunos_temp = dict(alunos)

    # Cria o Dict do Aluno atual
    aluno_dict = {ra:{}}
    try:
        aluno_dict[ra]["NOME"] = aluno_nome if aluno_nome else alunos[ra]["NOME"] if alunos[ra]["NOME"] else "NÃO RASTREADO" 
        aluno_dict[ra]["CURSO"] = curso if curso else alunos[ra]["CURSO"] if alunos[ra]["CURSO"] else "NÃO RASTREADO" 
    except KeyError:
        aluno_dict[ra]["NOME"] = "NÃO RASTREADO" 
        aluno_dict[ra]["CURSO"] = "NÃO RASTREADO"

    aluno_dict[ra]["RA"] = ra
    aluno_dict[ra]["SENHA"] = senha
    aluno_dict[ra]["SENHA_OK"] = senha_ok

    print("Aluno:", aluno_dict)
    # Verifica se aluno está CURSANDO ou FORMADO
    if disciplinas and senha_ok == "OK":
        aluno_dict[ra]['SITUAÇÃO'] = "FORMADO"
        
        # Se tiver disciplinas Pendentes e se não houver disciplinas Matriculadas
        # indica que o aluno trancou a Matrícula
        for disc in disciplinas:
            if disc.status == "PENDENTE":
                aluno_dict[ra]['SITUAÇÃO'] = "TRANCADO"
                break

        # Verifica se tem Disciplinas em andamento 
        for disc in disciplinas:
            if disc.status == "MATRICULADA" or disc.status == "SUB":
                aluno_dict[ra]['SITUAÇÃO'] = "CURSANDO"
                break

        
        # Registra as disciplinas na base do aluno, somente
        aluno_dict[ra]['DISCIPLINAS']= {}
            
        # Registra a série ideal do aluno 
        # disciplinas_serie_ideal(ra, curso, disciplinas)
        
        for disciplina in disciplinas:
            # print(nome, disciplina.status, disciplina.disciplina,disciplina.modulo)
            
            if disciplina.status not in aluno_dict[ra]['DISCIPLINAS']:
                aluno_dict[ra]['DISCIPLINAS'][disciplina.status] = {}

            aluno_dict[ra]['DISCIPLINAS'][disciplina.status][disciplina.disciplina] = {}
            aluno_dict[ra]['DISCIPLINAS'][disciplina.status][disciplina.disciplina]['DT_INICIO'] = disciplina.dt_inicio
            aluno_dict[ra]['DISCIPLINAS'][disciplina.status][disciplina.disciplina]['MODULO'] = disciplina.modulo
            aluno_dict[ra]['DISCIPLINAS'][disciplina.status][disciplina.disciplina]['STATUS'] = disciplina.status
            aluno_dict[ra]['DISCIPLINAS'][disciplina.status][disciplina.disciplina]['SÉRIE IDEAL'] = disciplina.serie_ideal
            
    else:
        aluno_dict[ra]['SITUAÇÃO'] = "INDEFINIDO"
        aluno_dict[ra]['DISCIPLINAS']= {}

    # atualiza o Dict geral de alunos
    alunos_temp.update(aluno_dict)

    save_json(alunos_temp,path_file)

def situacao_aluno_mensalista(**kwargs) -> None:
    """
    Salva no BD as informações relativas a:
        - Dados Cadastrais
        - Status das disciplinas
    """
    import json

    print(0)

    aluno_nome = kwargs.get('aluno_nome',None)

    ra = kwargs.get('ra',None)
    senha = kwargs.get('senha',None)
    senha_ok = kwargs.get('senha_ok','OK')
    curso = kwargs.get('curso',None)
    disciplinas = kwargs.get('disciplinas',None)
    atividades = kwargs.get('atividades',[])
    erro = kwargs.get('erro',None)
    print(1)
    # Abre arquivo de Alunos BD
    cont = 3
    while cont:
        try:
            path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_mensalista.json"
            if not os.path.isfile(path_file):
                alunos = {}
                with open(path_file, 'w', encoding='utf-8') as f:
                    json.dump(alunos, f ,ensure_ascii=False)
            else:
                with open(path_file, encoding='utf-8') as json_file:
                    alunos = json.load(json_file)
            break
        except json.JSONDecodeError:
            # Em casos de duplicidade de acesso ao BD
            cont-=1
            time.sleep(5)

    # Espelha os dados do BD de alunos em um espelho
    alunos_temp = dict(alunos)
    print(2)
    # Cria o Dict do Aluno atual
    aluno_dict = {ra:{}}
    try:
        aluno_dict[ra]["NOME"] = aluno_nome if aluno_nome else alunos[ra]["NOME"] if alunos[ra]["NOME"] else "NÃO RASTREADO" 
    except KeyError:
        aluno_dict[ra]["NOME"] = "NÃO RASTREADO" 
    
    try:            
         aluno_dict[ra]["CURSO"] = curso if curso else alunos[ra]["CURSO"] if alunos[ra]["CURSO"] else "NÃO RASTREADO"

    except KeyError:
        aluno_dict[ra]["CURSO"] = "NÃO RASTREADO"

    aluno_dict[ra]["RA"] = ra
    aluno_dict[ra]["SENHA"] = senha
    aluno_dict[ra]["ERRO"] = erro  
    aluno_dict[ra]["ATIVIDADES"] = {}  

    print("Aluno:", aluno_dict)

    if atividades:
        for atividade in atividades:
            print("     - atividade:", atividade)
            aluno_dict[ra]["ATIVIDADES"][atividade[0].text]= atividade[1].text

                    
    print("XXX:", aluno_dict)

    # atualiza o Dict geral de alunos
    alunos_temp.update(aluno_dict)

    save_json(alunos_temp,path_file)

def painel_inicio(driver):
    # Entra no ambiente das disciplinas
    url = "https://studeo.unicesumar.edu.br/#!/app/studeo/aluno/ambiente/disciplina"
    driver.get(url)
    ult_div(driver)
    f5(driver)
    # ignorar_aviso(driver,aviso)
    if driver.current_url == URL_AVISO:
        verifica_aviso(driver)
    cont=2
    while cont:
        try: 
            print("")
            WebDriverWait(driver,20-3*cont).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            css_nome_aluno = "body > div.full-height.ng-scope > div > div.ng-scope > div > div.container-fluid.relative > div.pull-right.full-height.visible-sm.visible-xs > div > div > uni-user-menu > div > ul > li.padding-20.m-b-10.bg-master-lighter > dl > h5"
            WebDriverWait(driver,20-3*cont).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_nome_aluno)))
            html = driver.page_source
            soup = BS(html, 'html.parser')
            break
        except:
            cont-=1
            driver.refresh()
            t(1)
            ult_div(driver)
            html = driver.page_source
            soup = BS(html, 'html.parser')
    return driver,soup

def painel_disciplinas(driver, **kwargs):


    """
    Vai para a tela do painel de disciplinas
    """
    disciplina= kwargs.get('disciplina','')

    # Entra no ambiente das disciplinas
    url = "https://studeo.unicesumar.edu.br/#!/app/studeo/aluno/ambiente/disciplina"
    cont = 3
    while cont:
        try:
            driver.get(url)
            ult_div(driver)          
            print(f"    Entrando Painel Disciplinas")
            cont_painel = 3
            
            while cont_painel:
                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,'MATRICULADA')))
                    print("    > Entrou no Painel de Disciplinas Geral.")
                    break
                except TimeoutException:
                    cont_painel -=1


                print(f"  >> Ainda não localizou Painel de disciplinas: {cont_painel} - {disciplina}" )
            ult_div(driver)
            break

        except TimeoutException as err:
            print(f"            >> falhou em acessar o painel de atividades [{str(4-cont)} - {disciplina}]")
            cont-=1
            if not cont:
                import traceback
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(msg+str(cont))
                raise TimeoutException
        
        except Exception as err:
                cont-=1
                import traceback
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(msg+str(cont))
                quit()

def lista_disciplinas(driver:webdriver) -> list:
    #Abas de disciplinas
    #Disciplinas concluidas:
    cont=3
    while cont:
        try:
            # Acessa o painel de disciplinas
            painel_disciplinas(driver)
            t(1)
            soup = atualizar_soup(driver)

            # Scrapped DISCIPLINAS MATRICULADAS
            ano = ""
            matriculadas_disc = []
            lista_disc_matriculadas = soup.find("div",{"id":"panel1"}).find_all('span',{"ng-bind":"disciplina.nmDisciplina"})
            for disc in lista_disc_matriculadas:
                matriculadas_disc.append(disc.text)
            
            datas = soup.find("div",{"id":"panel1"}).find_all("div",{"class":"col-xs-6"})
            matriculadas_dt_inicio = []
            matriculadas_mod = []
            for j , data in enumerate(datas):
                modulo = data.text
                if j % 2:
                    matriculadas_mod.append(modulo.split(" ")[3])
                else:
                    matriculadas_dt_inicio.append(modulo.split(" ")[3])
            
            disciplinas = []
            for i, disc in enumerate(matriculadas_disc):
                modulo = matriculadas_mod[i]
                ano = modulo[:4]
                dt_inicio = matriculadas_dt_inicio[i]
                disciplinas.append(Disciplina(disc,modulo,dt_inicio, None, "MATRICULADA"))
                # print("asdfdddd", disc,modulo,dt_inicio, None, "MATRICULADA")

                       
            # Scrapped DISCIPLINAS COM SUB
            matriculadas_sub_disc = []
            lista_disc_matriculadas_sub = soup.find("div",{"id":"panel1"}).find_all('span',{"ng-bind":"disciplinas.disciplina.nmDisciplina"})
            for disc in lista_disc_matriculadas_sub:
                matriculadas_sub_disc.append(disc.text)
            
            # Caso tenha disciplina SUB pendente ele irá verificar
            try:
                datas_sub = soup.find("div",{"ng-if":"vm.disciplinasMapaSub.length > 0"}).find_all("div",{"class":"col-xs-6"})     
                matriculadas_sub_dt_inicio = []
                matriculadas_sub_mod = []
                for j , data in enumerate(datas_sub):
                    modulo = data.text
                    if j % 2:
                        matriculadas_sub_mod.append(modulo.split(" ")[3])
                    else:
                        matriculadas_sub_dt_inicio.append(modulo.split(" ")[3])

                for i, disc in enumerate(matriculadas_sub_disc):
                    modulo = matriculadas_sub_mod[i]
                    ano = modulo[:4]
                    dt_inicio = matriculadas_sub_dt_inicio[i]
                    disciplinas.append(Disciplina(disc,modulo,dt_inicio, None, "SUB"))

            except AttributeError:
                pass

            # Scrapped DISCIPLINAS CURSADAS
            cursadas_disc = []
            lista_disc_cursadas = soup.find("div",{"id":"panel3"}).find_all('span',{"ng-bind":"disciplina.nmDisciplina"})
            for disc in lista_disc_cursadas:
                cursadas_disc.append(disc.text)

            datas = soup.find("div",{"id":"panel3"}).find_all("div",{"class":"col-xs-6"})
            cursadas_dt_inicio = []
            cursadas_mod = []
            for j , data in enumerate(datas):
                modulo = data.text
                if j % 2:
                    cursadas_mod.append(modulo.split(" ")[3])
                else:
                    cursadas_dt_inicio.append(modulo.split(" ")[3])
            
            for i, disc in enumerate(cursadas_disc):
                modulo = cursadas_mod[i]
                dt_inicio = cursadas_dt_inicio[i]
                disciplinas.append(Disciplina(disc,modulo,dt_inicio, None, "CURSADA"))


            # Scrapped DISCIPLINAS PENDENTES
            pendentes_disc = []
            lista_disc_pendentes = soup.find("div",{"id":"panel4"}).find_all('span',{"ng-bind":"disciplina.nome"})
            for disc in lista_disc_pendentes:
                pendentes_disc.append(disc.text)

            datas = soup.find("div",{"id":"panel4"}).find_all("div",{"class":"col-xs-6"}) #[i].find_all('p',{"class":"all-caps font-montserrat semi-bold no-margin ng-binding"})
            pendentes_serie = []
            for j , data in enumerate(datas):
                serie = data.text.replace("\n","").replace("\r","").replace("\s","")
                if not j % 2:
                    pendentes_serie.append(serie.split(" ")[3])

            for i, disc in enumerate(pendentes_disc):
                serie_ideal = pendentes_serie[i]
                disciplinas.append(Disciplina(disc, None, None, serie_ideal, "PENDENTE"))
            

            # Scrapped DISCIPLINAS NIVELAMENTO
            nivelamento_disc = []
            lista_disc_nivelamento = soup.find("div",{"id":"panel2"}).find_all('span',{"ng-bind":"disciplina.nmDisciplina"})
            for disc in lista_disc_nivelamento:
                # print(disc.text)
                nivelamento_disc.append(disc.text)

            datas = soup.find("div",{"id":"panel2"}).find_all("div",{"class":"col-xs-6"})
            nivelamento_dt_inicio = []
            nivelamento_mod = []
            for j , data in enumerate(datas):
                modulo = data.text
                if j % 2:
                    nivelamento_mod.append(modulo.split(" ")[3])
                else:
                    nivelamento_dt_inicio.append(modulo.split(" ")[3])

            # Para ober o MODULO da disciplina
            for i, disc in enumerate(nivelamento_disc):
                try:
                    print("\n\n ANO", ano, "\n\n")
                    ano_atual=ano
                    ano_antes = str(int(ano_atual)-1)
                    ano_depois = str(int(ano_atual)+1)
                except ValueError:
                    # Obter o ano atual
                    ano_atual = str(datetime.now().year)
                    ano_antes = str(int(ano_atual)-1)
                    ano_depois = str(int(ano_atual)+1)
               
                
                
                if ano_atual in disc:
                    modulo=ano_atual+"/51" if "51" in disc else ano_atual+"/52" if "52" in disc else ano_atual+"/53" if "53" in disc else ano_atual+"/54"
                elif ano_antes in disc:
                    modulo=ano_antes+"/51" if "51" in disc else ano_antes+"/52" if "52" in disc else ano_antes+"/53" if "53" in disc else ano_antes+"/54"
                elif ano_depois in disc:
                    modulo=ano_depois+"/51" if "51" in disc else ano_depois+"/52" if "52" in disc else ano_depois+"/53" if "53" in disc else ano_depois+"/54"
                else:
                    modulo=ano_atual+"/51" if "51" in disc else ano_atual+"/52" if "52" in disc else ano_atual+"/53" if "53" in disc else ano_atual+"/54"

                dt_inicio = nivelamento_dt_inicio[i]
                disciplinas.append(Disciplina(disc,modulo,dt_inicio, None, "NIVELAMENTO"))
            

            return disciplinas

        except TimeoutException:
            cont-=1

        except AttributeError:
            cont-=1
            if not cont:
                raise DisciplinaError

    if not cont:
        print("   Ocorreu erro no carregamento das disciplinas do Aluno")
        raise TypeError

def painel_avaliacao_digital(driver, aluno, modulo):
    """
    Vai para a tela do painel de Avaliação Digital

    """
    modulo = modulo[-2:]+"/"+modulo[:4]

    print(f"    MÓDULO: {modulo}")

    url = "https://studeo.unicesumar.edu.br/#!/app/studeo/aluno/ambiente/agendamento-prova-digital"
    cont = 3
    while cont:
        try:
            driver.get(url)
            t(2)
            ult_div(driver)
            soup = atualizar_soup(driver)
            
            # Define o texto que você está esperando aparecer na página
            periodo = "PERIODO: "

            # Aguarda até que o texto especificado esteja presente na página
            # Você pode ajustar o seletor CSS ('body') para ser mais específico conforme necessário
            WebDriverWait(driver, 30).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), periodo)
            )

            # Aguarda até que os elementos estejam visíveis
            WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "p[class='lista-periodo m-b-0 ng-binding']"))
            )

            WebDriverWait(driver, 15).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div[ng-repeat='le in vm.listaEncerrada']"))
            )

            # Encontra todas as divs que representam os períodos
            divs_periodos = driver.find_elements(By.CSS_SELECTOR, "div[ng-repeat='le in vm.listaEncerrada']")
            

            for div in divs_periodos:
                # Verifica se a div contém o texto "PERIODO: ModuloCorrespondente"
                
                print("PERIODO: "+modulo in div.text, div.text+"\nX--------------------------------------------------X\n")
                if "PERIODO: "+modulo in div.text:
                    try:
                        # Dentro da div encontrada, procura pelo botão "Cópia de prova" e clica nele
                        # css_btn_copia = div.find_element(By.CSS_SELECTOR, )
                        print(f"   >> Período avaliativo encontrado: {modulo}")
                        css_btn_copia = "a[ng-click*='copiaProva']"
                        btn_copia_prova =  WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, css_btn_copia))
                        )

                        print(f"   >> Prova Finalizada: Encontrada")
                        driver.execute_script("arguments[0].click();", btn_copia_prova)
                        # Mudar o foco para o iframe antes de fazer o scraping do seu conteúdo
                        iframe = WebDriverWait(driver, 15).until(
                            EC.visibility_of_any_elements_located((By.ID, 'iframeCopiaProva'))
                        )
                        # Muda o foco para o primeiro (e único) da lista
                        driver.switch_to.frame(iframe[0])
                        t(2)
                        soup = atualizar_soup(driver)

                        # Obtém a disciplina
                        disciplina = driver.find_element(By.CSS_SELECTOR, "td[class='disciplina-nome']").text
                        print("    DISCIPLINA:", disciplina)

                        driver.switch_to.default_content() 
                        t(1)
                        css_btn_fechar = "button[ng-click='$ctrl.cancel()']"
                        btn_fechar =  WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, css_btn_fechar))
                        )
                        driver.execute_script("arguments[0].click();", btn_fechar)

                        salva_prova(soup=soup, aluno=aluno, disciplina=disciplina)

                        # Quando terminar, volte ao conteúdo principal da página

                    except TimeoutException:
                        print(f"            >> Não foram encontradas provas finalizadas ")
                        

                    except Exception as e:
                        log_grava(err=err)
                        print(f"   Erro: {str(e)} ")
                        

                else:
                    # print("   >> Não há período avaliativo para este MÓDULO!\n"+div.text)
                    continue

                try:
                    driver.switch_to.default_content()
                except:
                    pass
            # Encerra o while
            break

        except Exception as err:
            import traceback
            log_grava(err=err)
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg+str(cont))
            cont-=1

def salva_prova(soup, aluno , disciplina):
    from system.converter_HTML_to_PDF import html_to_pdf
    from system.pastas import diretorio_raiz, verifica_pastas

    # Verifica se existe a pasta Provas
    dir_provas = diretorio_raiz()+'\\Provas'
    verifica_pastas(pasta=dir_provas)

    # Encontra e remove o <script> específico pelo seu atributo 'src'
    script_mathjax = soup.find('script', {'src': 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML'})
    if script_mathjax:
        script_mathjax.decompose()

    # Encontra e remove todos os <script> sem atributos específicos (como o segundo script do seu exemplo)
    for script in soup.find_all('script', {'src': False}):
        if "mensagem()" in script.text:  # Verifica se o script contém a função 'mensagem()'
            script.decompose()

    # Encontra e remove o <img> específico pelos seus atributos
    img_to_remove = soup.find('img', {'class': 'img-bloq', 'src': 'spacer.gif', 'title': 'É proibida a cópia e a reprodução deste conteúdo.'})
    if img_to_remove:
        img_to_remove.decompose()

    # Encontra e remove o <img> específico pelos seus atributos
    img_to_remove = soup.find('img', {'src': 'unicesumar-logo.png'})
    if img_to_remove:
        img_to_remove.decompose()
    
    # Encontra todos os elementos <style>
    styles = soup.find_all("style")

    # Remove todos os elementos <style>, exceto o primeiro
    for style in styles[1:]:
        style.decompose()

    # Encontra o elemento <div> pela sua classe
    div_element = soup.find('div', class_='avaliacoes page')

    # Adiciona a nova classe ao elemento
    if div_element:
        div_element['class'].append('liberada')  # Adiciona 'liberada' à lista de classes


    # O HTML modificado, agora sem os elementos <script> específicos
    style = "\"ordem\" style=\"width: 30px\" "
    # style2 = "\"ordem errada\" style=\"width: 30px;height:30px\" "

    style3 = """/*
        div.alternativa .ordem.errada{
            color: #FFF !important;
            background: #dc3545 !important;
        }
        */"""

    style4 = """
        div.alternativa .ordem.errada{
            color: #FFF !important;
            background: #dc3545 !important;
        }
        """
    
    marcacao = "class=\"marcacao\">("
    marcacao_novo = "class=\"marcacao\"><br>("
    
    html_modificado = str(soup).replace('\u00a0', '').replace('\u200b', '').replace("filter: alpha(opacity=50);","color: #CCC;").replace("\"ordem\"",style).replace(style3,style4).replace(marcacao,marcacao_novo)
        
        
    # Salvar o conteúdo HTML em um arquivo
    file_html = dir_provas+"\\"+aluno.curso+" - "+disciplina+" - "+aluno.nome+".html"
    with open(file_html, 'w', encoding='utf-8') as arquivo:
        arquivo.write(html_modificado)

    file_pdf = dir_provas+"\\"+aluno.curso+" - "+disciplina+" - "+aluno.nome+".pdf"
    html_to_pdf(html=file_html, pdf=file_pdf)
    # os.remove(file_html)

def disciplinas_serie_ideal(ra, nome_curso, disciplinas):
    ra = int(ra.split("-")[0])
    # Dict de módulos
    modulo_ideal = {
        1 : "51",
        2 : "52",
        3 : "53",
        0 : "54"
        }
 
    # Abre arquivo de Alunos BD
    cont = 3
    while cont:
        try:
            path_file = os.path.abspath(os.getcwd())+"\\BD\\cursos\\serie_ideal.json"
            if not os.path.isfile(path_file):
                cursos = {}
                with open(path_file, 'w', encoding='utf-8') as f:
                    json.dump(cursos, f ,ensure_ascii=False)
            else:
                with open(path_file, encoding='utf-8') as json_file:
                    cursos = json.load(json_file)
            break
        except json.JSONDecodeError:
            # Em casos de duplicidade de acesso ao BD
            cont-=1
            time.sleep(5)

    for disciplina in disciplinas:
        if disciplina.status == "PENDENTE":
            # Verifica se existe o curso no BD
            if nome_curso not in cursos:
                cursos[nome_curso] = {}
                cursos[nome_curso][disciplina.disciplina] = {}
                cursos[nome_curso][disciplina.disciplina]['SÉRIE IDEAL'] = disciplina.serie_ideal
                cursos[nome_curso][disciplina.disciplina]['MÓDULO IDEAL'] = modulo_ideal[int(disciplina.serie_ideal)%4]
                cursos[nome_curso][disciplina.disciplina]['RA REF'] = ra

            else:
                # Se o curso está no BD, então verifica se a disciplina também está
                if disciplina.disciplina not in cursos[nome_curso]:
                    # Aloca o espaço para os dados da DISCIPLINA
                    cursos[nome_curso][disciplina.disciplina] = {}
                    cursos[nome_curso][disciplina.disciplina]['SÉRIE IDEAL'] = disciplina.serie_ideal
                    cursos[nome_curso][disciplina.disciplina]['MÓDULO IDEAL'] = modulo_ideal[int(disciplina.serie_ideal)%4]
                    cursos[nome_curso][disciplina.disciplina]['RA REF'] = ra

                else:
                    # Somente atualiza o BD se o RA for mais recente do que o atual
                    if int(cursos[nome_curso][disciplina.disciplina]['RA REF'])<int(ra):
                        cursos[nome_curso][disciplina.disciplina] = {}
                        cursos[nome_curso][disciplina.disciplina]['SÉRIE IDEAL'] = disciplina.serie_ideal
                        cursos[nome_curso][disciplina.disciplina]['MÓDULO IDEAL'] = modulo_ideal[int(disciplina.serie_ideal)%4]
                        cursos[nome_curso][disciplina.disciplina]['RA REF'] = ra

    save_json(cursos, path_file)

def salvar_drive(driver,nome_curso, disciplina, atividade, modulo, questionario,titulo):
    import base64

    from system.pastas import diretorio_raiz

    # Recupera Sigla dos Cursos
    cursos = dict_curso_sigla()

    # Sigla do Curso
    curso = cursos[nome_curso]

    # Formata disciplina, retira caracteres inválidos para formação de arquivos
    disciplina = escapa_palavras(disciplina)

    # Formata modulo
    modulo = modulo.replace("/","").replace(".","")

    # Define diretórios de trabalho
    dir_papiron = diretorio_raiz()
    dir_drive = dir_papiron+'\\'+modulo+'\\drive'

    # define o local dentro do drive onde será salvo o arquivo
    try:
        sufixo = definir_sufixo_legado(nome_curso,disciplina, questionario)
        # Cria a pasta de destino
        # Se for disciplina GERAL, não precisa separar por pastas
        # Na maioria das vezes é apenas 1 arquivo
        dir_destino = escapa_path(dir_drive+sufixo)  \
            if nome_curso=="GERAL" or ("ESTUDO CONTEMPORÂNEO E TRANSVERSAL" in disciplina or 
                        "FORMAÇÃO SOCIOCULTURAL E ÉTICA" in disciplina) \
            else escapa_path(dir_drive+sufixo+'\\'+curso+" - "+disciplina)
        

        verifica_pastas(pasta=dir_destino)
    
        # Constroí o nome do arquivo a ser gerado no drive
        # Se for prepare-se ajusta ao título da Atividade
        atividade_formatada = atividade   \
            .replace("AE1","ATIVIDADE 1") \
            .replace("AE2","ATIVIDADE 2") \
            .replace("AE3","ATIVIDADE 3") \
            .replace("AE4","ATIVIDADE 4") \
            .replace("AE5","ATIVIDADE 5") 
            
        path_file = escapa_path(dir_destino+'\\'+atividade_formatada+" - "+curso+" - "+titulo+".pdf") \
        if ("PREPARE-SE" in disciplina.upper() or "NIVELAMENTO" in disciplina.upper()) \
        else escapa_path(dir_destino+'\\'+atividade_formatada+" - "+curso+" - "+disciplina+".pdf")

        path_file = path_file.replace(" ESTUDO CONTEMPORÂNEO E TRANSVERSAL-","").replace(" - FORMAÇÃO SOCIOCULTURAL E ÉTICA I","").replace(" - FORMAÇÃO SOCIOCULTURAL E ÉTICA II","")
        
    except Exception as err:
        log_grava(err=err)
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(f"Erro 6672: \n\n{msg}\n\n\n")
    
    # Armazena a referência da aba original para voltar mais tarde
    original_tab = driver.current_window_handle

    # Clica no Botão IMPRIMIR
    btn_imprimir = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dropdown-toggle.p-b-15[data-toggle='dropdown']"))
    )
    driver.execute_script("arguments[0].click();",btn_imprimir)

    # Clica no item suspenso que aparece "ATIVIDADE AVALIATIVA COMPLETA"
    botao_ativ_avaliativa = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-link.text-left[title='Imprimir Atividade Avaliativa Completo']"))
        )
    driver.execute_script("arguments[0].click();",botao_ativ_avaliativa)

    # Função para esperar até que o número total de abas seja 2 (1 original + 1 novas)
    try:
        WebDriverWait(driver,15).until(lambda driver: len(driver.window_handles) == 2)
    except TimeoutException:
        print("Não conseguiu contar 2 abas, vai pegar a última aberta")
        pass
    # driver.switch_to.window(driver.window_handles[-1])

    # Muda o foco para a nova aba, se necessário
    driver.switch_to.window(driver.window_handles[-1])  # Troca para a segunda aba

    # Configurações para salvar a página como PDF
    pdf_settings = {
        "landscape": False,
        "printBackground": True,
        "paperWidth": 8.27,
        "paperHeight": 11.69,
        "marginTop": 0.5,
        "marginBottom": 0.5,
        "marginLeft": 0.5,
        "marginRight": 0.3
    }

    # Salvar o PDF em um arquivo
    try:
        # Gerar o PDF
        pdf = driver.execute_cdp_cmd("Page.printToPDF", pdf_settings)
        with open(path_file, "wb") as f:
            f.write(base64.b64decode(pdf['data']))
    except WebDriverException as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(f"Erro ao gerar PDF: {err}")
    except Exception as err:
        log_grava(err=err)
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(f"Erro 4592: \n\n{msg}\n\n\n")

    # Fecha as novas abas
    for handle in driver.window_handles:
        if handle != original_tab:
            try:
                driver.switch_to.window(handle)
                driver.close()
            except Exception:
                log_grava(err=err)
    
    # Retorna para a aba original
    driver.switch_to.window(original_tab)

    # Copia os templates para dentro da pasta
    if not questionario:

        # Define o caminho da pasta de origem e da pasta de destino
        dir_origem_material = escapa_path(dir_papiron+'\\'+modulo+'\\'+nome_curso+'\\'+disciplina+'\\Material')

        # print("aquigfdf: ", os.path.isdir(dir_origem_material), dir_origem_material)
        # print("aeeafdes: ", os.path.isdir(dir_destino), dir_destino)

        # Lista todos os arquivos na pasta de origem
        arquivos = os.listdir(dir_origem_material)

        # Copia cada arquivo da origem para o destino
        for arquivo in arquivos:
            # print("arquivooo:", arquivo)
            caminho_completo = escapa_path(os.path.join(dir_origem_material, arquivo))
            # print("caminh comll", os.path.isfile(caminho_completo), caminho_completo)
            if os.path.isfile(caminho_completo):
                shutil.copy(src=caminho_completo,dst=dir_destino)
                # print(f"Copiado: {arquivo}")

    else:
        # Verifica se tem o livro para responder os questionários
        # print("não tem material de tempalte", atividade, disciplina)
        dir_download_book = dir_papiron+"\\Livros Digitais"
        nome_livro = escapa_path(disciplina)
        files_livros = os.listdir(dir_download_book)

        # Verifica se o livro já foi baixado
        livro_down = False
        for livro in files_livros:
            if nome_livro in livro:
                livro_down = True
                # print("\nACHOU LIVRO para questionario")
                break
        
        if livro_down:
            # print("livro a acopiar:",dir_download_book+'\\'+nome_livro+'.pdf')
                try:
                    shutil.copy(src=dir_download_book+'\\'+nome_livro+'.pdf',dst=dir_destino+'\\MATERIAL.pdf')
                except FileNotFoundError:
                    "apenas pode não ter o livro na nossa biblioteca"

def salva_material_disciplina(driver, nome_curso, disciplina, modulo, config):
    import shortuuid

    from system.pastas import diretorio_raiz

    # Verifica se as pastas existem
    verifica_pastas(curso = nome_curso, disciplina = disciplina, modulo = modulo)
    
    # Recupera Sigla dos Cursos
    cursos = dict_curso_sigla()

    # Sigla do Curso
    curso = cursos[nome_curso]
    modulo = modulo.replace("/","").replace(".","")

    # Define diretórios de trabalho
    dir_papiron = diretorio_raiz()

    dir_download = dir_papiron+"\\Downloads\\Temp"
    dir_download_book = dir_papiron+"\\Livros Digitais"
    dir_destino = dir_papiron+'\\'+modulo+'\\'+nome_curso+'\\'+disciplina
    dir_destino_material = dir_destino+'\\Material'


    # Clica F5 da página
    f5(driver)

    # Baixar Livro Digital
    nome_livro = escapa_path(disciplina)
    ult_div(driver)
    soup = atualizar_soup(driver)

    # Lista os livros já baixados e compara se já tem no acervo:
    livro_down = False

    # Verifica como está a opção de baixar livros
    if config['cb_download_livros'] == True:
        files_livros = os.listdir(dir_download_book)

        # Verifica se o livro já foi baixado
        for livro in files_livros:
            if nome_livro in livro:
                livro_down = True
                print(f"\n   ACHOU LIVRO BAIXADO: {nome_livro}")
                break
    else:
        print("    >>>> A opção \"Baixar Livros\" está desabilitada!")

    if not livro_down and config['cb_download_livros'] == True:
    # if not os.path.isfile(escapa_path(dir_download_book+'\\'+nome_livro+".pdf")) and not os.path.isfile(escapa_path(dir_download_book+'\\'+nome_livro+".docx")):
        try:
            css_livro_digital = "#uni-ambiente-material-estudo > div > div > div.panel-body.no-padding > ul > li > div > div.col-sm-4.sm-text-center.text-right.sm-m-t-10 > a:nth-child(2)"
            btn_livro_digital = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.CSS_SELECTOR,css_livro_digital)))
            driver.execute_script("arguments[0].click();",btn_livro_digital)

            # Altera a configuração de Pasta de Download do Webdriver
            dir_temp_book = dir_download +"\\"+shortuuid.uuid()
            os.mkdir(dir_temp_book)
            params = {'behavior': 'allow', 'downloadPath': dir_temp_book}
            driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

            # Aguardar o início do download
            cont = 100
            while cont:
                # lista todos os arquivos da pasta de destino
                files = os.listdir(dir_temp_book)

                # filtra apenas os arquivos com as extensões .crdownload ou .part
                download_files = fnmatch.filter(files, '*.crdownload') + fnmatch.filter(files, '*.part')

                if download_files:
                    break
                
                else:
                    cont-=1
                    time.sleep(0.2)

            # Aguardar o livro digital ser baixado e transferido

            cont = 100
            while cont:
                # lista todos os arquivos da pasta de destino
                files_book = os.listdir(dir_temp_book)

                # filtra apenas os arquivos com as extensões .crdownload ou .part
                incomplete_files = fnmatch.filter(files_book, '*.crdownload') + fnmatch.filter(files_book, '*.part')

                if not incomplete_files:
                    try:
                        # print('O download do livro foi finalizado.')
                        
                        # Renomeia para o Nome Texto
                        files = os.listdir(dir_temp_book)
                        extensao = files[0][files[0].rfind("."):]
                        os.rename(escapa_path(dir_temp_book+'\\'+files[0]),escapa_path(dir_temp_book+'\\'+nome_livro+extensao))

                        # Verifica se não arquivo na pasta de destino
                        if os.path.isfile(escapa_path(dir_download_book+'\\'+nome_livro+extensao)):
                            os.remove(escapa_path(dir_download_book+'\\'+nome_livro+extensao))
                        
                        # Move para o arquivo de destino
                        shutil.move(escapa_path(dir_temp_book+'\\'+nome_livro+extensao),escapa_path(dir_download_book+'\\'+nome_livro+extensao))
                        d = False

                        # os.remove(dir_temp_book)

                    except IndexError:
                        pass

                    break

                else:
                    # print('Existem downloads em progresso.')
                    time.sleep(3)
                    cont-=1

        except (TimeoutException, JavascriptException) as err:
            print("\n\n  OBS: Não tem livro digital: "+nome_livro)
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            log_grava(msg=msg)


    try:
        # Guarda url do Painel de Disciplinas para voltar, 
        # retornar histórico (-1) não funciona
        url_painel_disciplina = driver.current_url
        soup = atualizar_soup(driver)

        # Clicar no Botão MATERIAL DA DISCIPLINA
        # Entra na página com os materiais da disciplina
        btn_material = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,"Material da Disciplina"))) 
        driver.execute_script("arguments[0].click();",btn_material)

        cont_material = 4
        count_download = []

        # lista de atividades que não tem modelo de mapas, ECT tem , mas é raro
        lista_geral = [
            "ESTUDO CONTEMPORÂNEO E TRANSVERSAL",
            "FORMAÇÃO SOCIOCULTURAL E ÉTICA",
            "SEMANA DE CONHECIMENTOS GERAIS", 
            "PROJETO DE ENSINO",
            "NIVELAMENTO DE",
            "PREPARE-SE",
        ]

        while cont_material:
            if any(disciplina_geral in disciplina.upper() for disciplina_geral in lista_geral) :
                break

            ult_div(driver)
            soup = atualizar_soup(driver)

            # Scrapped dos itens a serem efetuados os Downloads
            links_downloads = soup.find_all('span',{'alt':'fazer download'})
            count_download = len(links_downloads)
            name_download = soup.find_all('span',{'class':'bold all-caps font-montserrat fileNameCrop ng-binding'})

            # print(f"  nammeeee: {name_download}")
            if name_download:
                break
            else:
                cont_material-=1


        # Verifica se há arquivos na página para realizar o download
        # Se não houver material para download, sai e continua a rotina pai
        # if not count_download:
        #     raise MaterialError

        # Verifica se há arquivos prontos na pasta de destino:
        if os.path.isdir(escapa_path(dir_destino_material)):
            files_ready = os.listdir(escapa_path(dir_destino_material))
        else:
            os.mkdir(escapa_path(dir_destino_material))
            files_ready = []
        
        # Verifica se a quantidade atual na pasta é compatível com a esperada vista no Portal
        # Se não for irá retornar a rotina pai
        # print("FILES NO DESTINO", disciplina,  len(files_ready) != count_download,  len(files_ready) , count_download)
        if len(files_ready) != count_download and count_download:

            # Realiza o scrapped dos arquivos para download
            dir_temp = {}
            # print("   countad", count_download)
            # for i in range(count_download+1):
            for i, name in enumerate(name_download):
                
                # Nome final do arquivo, sem extensão
                # name = name_download[i].text
                name = name.text
                # print(f"    > Arquivo_{i}: {name}")
                
                # Baixar somente os materiais com MAPA no nome do arquivo
                lista_atividades =  [
                    "MAPA",
                    "PADRÃO",
                    "FORMULÁRIO",
                    "TEMPLATE",
                    "MODELO",
                    "RELATÓRIO",
                    "AE1",
                    "ATIVIDADE 1"
                ]

                lista_excluir = [
                    "COMO ENVIAR",
                    "REVISÃO DE QUESTÕES",
                    "CRACHÁ"
                ]

                if any(atividade in name.upper() for atividade in lista_atividades) and not any(excluir in name.upper() for excluir in lista_excluir):


                    # Dados iniciais da Publicação
                    dir_unity = dir_download +"\\"+shortuuid.uuid()
                    os.mkdir(dir_unity)
                    dir_temp[dir_unity] = name_download[i].text


                    # Verifica se o arquivo já foi baixado e está na pasta de destino final
                    download = True
                    for file_unity in files_ready:
                        if name in file_unity:
                            download = False
                            break
                    if not download:
                        continue

                    # Altera a configuração de Pasta de Download do Webdriver
                    params = {'behavior': 'allow', 'downloadPath': dir_unity}
                    driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

                    try:
                        ult_div(driver)
                        # filename = dir_papiron+'\\'+modulo+'\\'+curso+'\\'+disciplina+'\\'+name_download[i].text
                        soup.find_all('span',{'class':'bold all-caps font-montserrat fileNameCrop ng-binding'})
                        css_download = '#content > div > ui-view > ui-view > ui-view > div > div > div > div.container-fluid > div > div.col-lg-8 > div > ng-repeat:nth-child('+str(i+1)+') > div > div > div.panel-footer.no-border.no-padding > div > div > div > div > a > span'
                        btn_download = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,css_download)))
                        driver.execute_script("arguments[0].click();",btn_download)

                        # Aguarda Download Iniciar
                        # Verifica até ter um arquivo de download sendo baixado
                        cont = 1000
                        while cont:

                            # filtra apenas os arquivos com as extensões .crdownload ou .part
                            download_files = fnmatch.filter(os.listdir(dir_unity), '*.crdownload') + fnmatch.filter(os.listdir(dir_unity), '*.part')

                            if download_files:
                                # print(f"Arquivo de download encontrado: {dir_unity}\\{download_files}")
                                break
                            
                            else:
                                cont-=1
                                time.sleep(0.01)
                                if not cont:
                                    print("Saiu sem iniciar o download")
                        
                    except TimeoutException:
                        print("ERRO: Não encontrou o botão de Download: "+str(driver.current_url))
                        log_grava(msg="[DOWNLOAD MATERIAL]: Não encontrou o botão de DOWNLOAD")
                        continue
                else:
                    pass
                    # print(f"    > O arquivo {name} não é de interesse.\n")
            # log_grava(msg="INICIOU VERIFICAR OS ARQUIVOS NO TEMP")

            # Verifica se todos os downloads acabaram
            download_progress = True
            # print("COUNT:",count_download - len(files_ready), count_download , len(files_ready))
            n_download_ok = count_download - len(files_ready)
            tentativas = 30

            while n_download_ok:

                for download in dir_temp:

                    # filtra apenas os arquivos com as extensões .crdownload ou .part
                    files_in_download = os.listdir(download)
                    incomplete_files = fnmatch.filter(files_in_download, '*.crdownload') + fnmatch.filter(files_in_download, '*.part')
                    # print("Incomp:",incomplete_files, str(os.listdir(download)))
                          
                    if incomplete_files:
                        # print("Ainda há arquivos em Downloads:" + dir_temp[download])
                        # log_grava(msg="Ainda há arquivos em Downloads:" + dir_temp[download])
                        t(3)
                    else:
                        n_download_ok -= 1

                tentativas -= 1
                if not tentativas:
                    break

            # print("TODOS DOWNLOADS FORAM FINALIZADOS!!\n\n")
            # for dir in dir_temp:
                # print(dir)

            for download in dir_temp:
                try:
                    # Obtém a extensão do arquivo baixado
                    list_file_download = os.listdir(download)
                    # print("DOWNLOAD:", download ,"||", list_file_download, "||")
                    
                    # Caso a lista seja vazia!
                    if not list_file_download:
                        break

                    file_download = list_file_download[0]
                    extensao = os.path.splitext(file_download)[1]

                    # log_grava(msg="Extensão: "+ extensao )
                    os.rename(escapa_path(download+'\\'+file_download),escapa_path(download+'\\'+dir_temp[download]+extensao))
                    # print("renomeou")
                    # log_grava(msg=">>>>>>>>>>"+ download+'\\'+file_download+ "||||"+download+'\\'+dir_temp[download]+extensao)
                    
                    # Verifica se não há arquivo na pasta de destino
                    if os.path.isfile(escapa_path(dir_destino_material+'\\'+dir_temp[download]+extensao)):
                        os.remove(escapa_path(dir_destino_material+'\\'+dir_temp[download]+extensao))
                    
                    # Move para o arquivo de destino
                    # log_grava(msg="XXXXXXXXXX>> "+download+'\\'+dir_temp[download]+extensao + "|H|"+dir_destino_material+'|T|'+dir_temp[download]+'|X|'+download)
                    shutil.move(escapa_path(download+'\\'+dir_temp[download]+extensao),escapa_path(dir_destino_material+'\\'+dir_temp[download]+extensao))
                    
                    # Apaga a pasta temporária
                    # c = 3
                    # while c:
                    #     try:
                    #         print("Tentando remover: ", download)
                    #         t(0.5)
                    #         os.remove(download)
                    #     except PermissionError:
                    #         print("Permissão negada: ", c)
                    #         t(2)
                    #         c -= 1 

                except IndexError as err:
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    log_grava(msg=msg)
                    # print(f">> {list_file_download} ||||  extensao :{os.path.splitext(file_download)}")
                    # print("Verificar arquivo:" + download + dir_temp[download])

        else:
            raise MaterialError
                  
    except MaterialError as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        log_grava(msg=msg)
        # if count_download:
        #     log_grava(msg="[MATERIAL]: Não há material novo a ser feito download:"+curso+" - "+disciplina)
        # else:
        #     log_grava(msg="[MATERIAL]: Não há material disponibilizado para download:"+curso+" - "+disciplina)

    except TimeoutException as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print("     ERRO TimeOUT:", msg)

    except FileNotFoundError as err:
        msg = str("".join(traceback.format_exception(type(err), err, err.__traceback__)))
        print("Erro na criação da pasta do CURSO/DISCIPLINA/MATERIAL\n\n"+msg+"\nx-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x")
        log_grava(msg="[DOWNLOAD MATERIAL]: Erro na criação da pasta do CURSO/DISCIPLINA/MATERIAL\n"+msg+"\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    
    # Retorna ao Painel de Atividades de Disciplina
    driver.get(url_painel_disciplina)
    f5(driver)
    verifica_aviso(driver)
    ult_div(driver)

def verifica_proxima_questao(driver,soup):
    try:
        soup = atualizar_soup(driver = driver)
        xpath_botao_prox_questoes = '//button[@aria-label="Próxima questão"]'
        botao_prox_questao = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_botao_prox_questoes)))
        
        # Terminou de carregar o botão de próximo:
        print("             > Encontrada próxima questão de questionário.")
        soup_botao_prox_questao=soup.find('button',{"ng-click":"vm.setQuestaoAtual(vm.questaoAtual.ordem + 1, 'PRÓXIMO')"})
        
        try:
            if soup_botao_prox_questao['disabled']=='disabled':
                """
                Acabaram as questões
                """
                print("        x-x  Finalizou as questões da Atividade atual  x-x")
                return None
        except KeyError:
            """
            Ainda tem questões
            """
            driver.execute_script("arguments[0].click();",botao_prox_questao)
            t(1)
            # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_botao_prox_questoes)))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_botao_prox_questoes)))
        
        return "continua"
    except TimeoutException:
        return None

def disciplina_localiza(driver, disciplina):

    dict_status = {
        'MATRICULADA':{
                'PAINEL':'panel1',
                'SOUP':{'ng-bind':'disciplina.nmDisciplina'}
        },
        'SUB':{
                'PAINEL':'panel1',
                'SOUP':{'ng-bind':'disciplinas.disciplina.nmDisciplina'}
            },
        'CURSADA':{
                'PAINEL':'panel3',
                'SOUP':{'ng-bind':'disciplina.nmDisciplina'}
            },
        'NIVELAMENTO':{
                'PAINEL':'panel2',
                'SOUP':{'ng-bind':'disciplina.nmDisciplina'}
            }   
    }

    painel_disciplinas(driver, disciplina=disciplina)
    soup = atualizar_soup(driver)
    ult_div(driver)

    try:
        lista_disciplinas_status = soup.find('div',{'id':dict_status[disciplina.status]['PAINEL']}).\
                                    find_all('span',dict_status[disciplina.status]['SOUP'])
    except AttributeError as err:
        # Disciplina não está na lista da primeira página
        return []
    
    # Apenas formata a lista de impressão
    lista_formatada = []
    for item in lista_disciplinas_status:
        lista_formatada.append(item.text)

    for disc_lista in lista_disciplinas_status:
       
        if disciplina.disciplina in disc_lista.text:
            print(f"     >> Localizou a disciplina {disciplina.disciplina} na lista >> {lista_formatada} !!")
            print(f"     >> Disciplina {disc_lista.text}")
            return disc_lista.text

    print(f"     >> NÃO Localizou a disciplina {disciplina.disciplina} na lista >> {lista_formatada} !!")
    return []

def formata_data_disciplina(data, data_aluno, aluno, curso , disciplina ):
    try:

        dt = data_aluno[aluno.ra]['DISCIPLINAS'][disciplina.status][disciplina.disciplina]['DT_INICIO']

        if dt != "N/D":
            dt_inicio = datetime.strptime(dt,'%d/%m/%Y')

        else:
            # Apenas contorna o erro de Nivelamento não ter data de inicio
            if disciplina.status == 'NIVELAMENTO':
                dt_inicio = datetime.strptime('01/01/2024','%d/%m/%Y')
                return dt_inicio
            else:
                print("\n\n\n     >>> Verificar erro na data de início: ", disciplina.disciplina)
                return None 
        
        return dt_inicio

    except Exception as err:
        import traceback
        log_grava(err=err)
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        print("\n\n\n     >>> Erro na data: ", disciplina.disciplina)
        return None , None

def formata_data_fim_atividade(data, aluno , disciplina , curso , atividade):
    dt_fim = None
    # print("1", disciplina.disciplina in data[curso[aluno.curso]])
    if disciplina.disciplina in data[curso[aluno.curso]]:
        # print("2", atividade in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'])
        if atividade in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE']:
            # print("3", 'DT_FIM' in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade])
            if 'DT_FIM' in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]:
                dt_fim_str = data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['DT_FIM']
                dt_fim = datetime.strptime(dt_fim_str, "%Y-%m-%d")
    
    return dt_fim

def espera_atividades(driver, **kwargs):
    """
    Aguarda as atividades da disciplinas ficarem visíveis
    """
    disciplina = kwargs.get("disciplina", "xxxx")
    cont = 3
    while cont:
        try:
            soup = atualizar_soup(driver)
            t(2) , ult_div(driver)
            css_painel_atividades = "#uni-ambiente-questionario > div > div > div:nth-child(2) > div"
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_painel_atividades)))
            break
        except TimeoutException:
            if disciplina.disciplina in soup.text and "Informações Sobre A Disciplina" in soup.text : 
                print("      -->Encontrou a disciplina no soup")
                break
            print(f"    >> Parece que ainda não entrou no painel da disciplina: {disciplina.disciplina}")
            entra_disciplina(driver=driver , disciplina = disciplina)
            # f5(driver=driver)
            cont -= 1
            if cont:
                raise TimeoutException

def listar_atividades(self, driver , disciplina):

    soup = atualizar_soup(driver)
    lista_de_atividades = soup.find_all("p",{"aria-hidden":"true", "class":"no-margin bold all-caps font-montserrat fs-10 ng-binding"})

    print(f'      - Lista de Atividades:')
    lista_ativ = []
    for li in lista_de_atividades:
        lista_ativ.append(escape_html(li.text))
        print("           - ",escape_html(li.text))
    
    lista_ativ = ", ".join(lista_ativ)
    atividade_progresso = escape_html(lista_ativ)
    # progresso_lista(self,"   Lista de Atividades: "+ disciplina.disciplina +" - "+atividade_progresso)

    return lista_de_atividades

def listar_atividades_xpath(driver):
    lista_de_atividades = driver.find_elements(By.XPATH, '//div[@ng-repeat="item in $ctrl.mainList"]')
    return lista_de_atividades

def listar_atividades_script(driver):
    links = driver.find_elements(By.CSS_SELECTOR,'a.list-group-item.text-center.no-border[ng-click="$ctrl.openQuestionario(item)"]')
    return links

def bd_registrar_atividade(data, aluno , curso , disciplina , atividade , dt_fim ):
    from datetime import datetime, timedelta
    
    if not dt_fim:
        dt_fim = datetime.now()+timedelta(days=1)
    else:
        # Porque está sendo registrado o dia final como dd-mm-aaaa 00h00
        # então pode dar problema se roda no último dia.
        dt_fim = dt_fim+timedelta(days=1)
        
    try:
        # Executa o registro no BD das atividades listadas
        if not atividade in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE']:
            data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]={}
            data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE'] = "ABERTA"
            data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['ID_URL'] = None
            print(f'\n                             Registrou no BD   >> {atividade} - {disciplina.disciplina}')

        elif data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE']=="FECHADA":
            print(f'\n                             Atividade já finalizada  >> {atividade} - {disciplina.disciplina}')
            return  "continue"

        elif dt_fim>=datetime.now() and data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE']=="ABERTA":
    
            # O código abaixo refaz algumas atividades que não tinha conteúdo mas ficaram registradas.
            if ("Questão 1" not in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]
                or "DT_FIM" not in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]
            ):
                
                print(f'\n                      REFAZER Atividade ABERTA já registrada no BD e dentro do prazo  >> {atividade} - {disciplina.disciplina}')
                print("                         BD >>>  ", "Questão 1" not in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade] , "DT_FIM" not in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade])
                return None

            else:
                print(f'\n                             Atividade ABERTA já registrada no BD e dentro do prazo  >> {atividade} - {disciplina.disciplina}')
                return  "continue"

        elif dt_fim<datetime.now() and data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE']=="ABERTA":
            print(f'\n                             Atividade está FECHADA e pronta para ser FECHADA no BD  >> {atividade} - {disciplina.disciplina}')
            return None

        else:
            print(f'\n                             Aberta Atividade já registrada no BD e pronta para ser encerrada  >> {atividade} - {disciplina.disciplina}')
            return  "continue"

    except KeyError:
        data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE'] = "NÃO INICIADA"

def scrapped_aluno(usuario,contas):
    from class_papiron.class_dados_aluno import Aluno

    try:
        # Realiza o login nc conta de um novo aluno
        driver = iniciar_sesssao_chrome()
        driver = login(driver,usuario,contas[usuario])
        ult_div(driver)
            
        # Obtém dados do Aluno
        aluno = Aluno(driver) 
        print("\n     Criou o Aluno")
        print("\n     >> Scrapped do aluno: ", aluno)

        # Obtém disciplinas
        disciplinas = None
        disciplinas = lista_disciplinas(driver,aluno) 
        
        # Registra dados dos alunos
        situacao_aluno(aluno.nome, aluno.ra, usuario, contas[usuario], aluno.curso, disciplinas)
        
        print("\n    >>> Finalizado o scrapped do Aluno: ", aluno.nome , " - ", aluno.curso, "    <<<<<<<\n")
        driver.quit()
    
     
    except KeyError as err:
        import traceback
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"XXXXXXXXXXXXXXXXXXXX\n\n>>>>>> FALHA AO ACESSAR O LOGIN:"+usuario+" - "+contas[usuario]+"\n\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        print(msg)
        disciplinas = None
        situacao_aluno(None , None, usuario, contas[usuario], None, disciplinas)
        raise KeyError

    except Exception as err:
        msg = "XXXXXXXXXXXXXXXXXXXX\n\n>>>>>> FALHA AO ACESSAR O LOGIN:"+usuario+" - "+contas[usuario]+"\n\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        log_grava(err=err, msg=msg)
        print(msg)
        disciplinas, matriculadas , cursadas , pendentes = None, None, None, None
        situacao_aluno(None, None, usuario, contas[usuario], None, disciplinas)
        try:
            driver.quit()
        except:
            pass

def scrapped_id_resposta(questao):
    import json

    import requests as rq

    data = {"query":{"text":questao},"context":{"scenario":"","supportedTypes":["question"],"requestId":""},"pagination":{"cursor":None,"limit":2}}
  
    headers = {
        "Accept": "/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Length": "255",
        "Content-Type": "text/plain;charset=UTF-8",
        "Host": "srv-unified-search.external.search-systems-production.z-dn.net",
        "Origin": "https://brainly.com.br",
        "Referer": "https://brainly.com.br/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "x-api-key": "22df2c14-f58b-4603-abf2-788ba76862a0"
    }

    # print("Qq:", questao)


    url = "https://srv-unified-search.external.search-systems-production.z-dn.net/api/v1/pt/search"

    try:

        r = rq.post(url = url, headers = headers , data = json.dumps(data))
        result = r.json()

        # print("rr:", r , len(result["results"]))

        resposta_indeferida = False

        for i in range(len(result["results"])):

            id = result["results"][i]["question"]["id"]

            verified = result["results"][i]["question"]["answer"]["verified"]

            resposta = result["results"][i]["question"]["answer"]["content"]

            if len(str(resposta)) > 150:
                # Achou uma resposta no Brainly
                break
            elif "página" in resposta or "livro" in resposta or "pag." in resposta:
                # É curta mas indicou a página do livro
                break
            else:
                print("             >>> Reposta Indeferida:", result["results"][i]["question"]["answer"]["content"])
                resposta_indeferida = True
                
        if len(str(resposta)) < 150:
            # Não achou uma resposta no Brainly
            raise BrainlyError
    
    except BrainlyError as err:
        if not resposta_indeferida:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg , "Verifique se a VPN está conectada.")
        
        return None, None, None 

    except Exception as err:
        log_grava(err=err)
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        return None, None, None 

    return id , verified , resposta 

def tratar_resposta(resposta_html):

    soup = BS(resposta_html, 'html.parser')
    tags = []
    trechos = soup.find_all()
    for paragrafo in trechos:


        lista_parada = [
            "PERGUNTA COMPLETA",
            "COMPLEMENTO DA QUESTÃO",
            "QUESTÃO COMPLETA", 
            "ALTENATIVAS QUE COMPLETAM A QUESTÃO", 
            "COMPLETAM A QUESTÃO", 
            "ENUNCIADO COMPLETO", 
            "COMPLETANDO AS QUESTÕES",
            "MAIOR CLUBE DE CURSOS",
            "COLUNISTA PORTAL - EDUCAÇÃO",

        ]

        if any(palavra in paragrafo.text.upper() for palavra in lista_parada):
            break

        if "PERGUNTA COMPLETA" in paragrafo.text.upper() or "COMPLEMENTO DA QUESTÃO" in paragrafo.text.upper() or "QUESTÃO COMPLETA" in paragrafo.text.upper():
            break

        if not "APRENDA MAIS" in paragrafo.text.upper() and  not "BRAINLY" in paragrafo.text.upper() and not "SPJ" in paragrafo.text.upper() and not "VEJA MAIS" in paragrafo.text.upper():
            n = len(tags)
            if n>=1:
                if paragrafo not in tags[n-1]:
                    tags.append(paragrafo)
            else:
                tags.append(paragrafo)
    
    resposta = ''.join(str(tag) for tag in tags)

    resposta = resposta.replace("<p><strong>Explicação:</strong></p>","").replace("<p><strong>Reposta:</strong></p>","")

    return resposta

def contar_palavras(texto):
    lista = texto.split()


# def procurar_gabarito(**kwargs):
    
#     import requests as rq

#     enunciado = kwargs.get('enunciado', None)
#     lista_alternativas = kwargs.get('lista_alternativas', None)
#     soup = kwargs.get('soup', None)
#     disciplina = kwargs.get('disciplina', None)

#     url_base ="https://www.papiron.com.br"
#     hash_enunciado = hash_quest(enunciado)
#     gabarito = ""
#     url_hash = url_base+"/atividades/gabarito_hash/"+hash_enunciado

#     # Formatar Lista de Alternativas, ela vem com html
#     lista_formatada = []
#     for alternativa in lista_alternativas:
#         try:
#             formatar_alternativa = alternativa.find("p").decode_contents()
#         except AttributeError:
#             try:
#                 formatar_alternativa = soup.find_all('div',{"class":"inline-block m-t-10 ng-binding", "ng-bind-html":"alternativa.descricao  | mathJaxFix"}).decode_contents()
#             except AttributeError:
#                 formatar_alternativa = None    
        
#         lista_formatada.append(formatar_alternativa)


#     cont = 4
#     while cont:
#         try:
#             r = rq.get(url_hash, allow_redirects=False)
#             if r.status_code != 200:
#                 print("      >> Não tem enunciado igual no site")
#                 return None
#             else:
#                 print("      >> Localizou enunciado idêntico")

#             data_enunciados = r.json()

#             print("\n           ", 
#                     list(data_enunciados['0']['alternativas'].values()) == lista_formatada,
#                     "\n       >> "+str(list(data_enunciados['0']['alternativas'].values()))+"\n      >> "+str(lista_formatada))
#             break
#         except KeyError as err:
#             msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
#             log_grava(msg=msg+enunciado[:150]+"=======================\n\n"+str(data_enunciados)+"=============================\n\n")  
#             cont-=1
#             if not cont:
#                 return None
        
#         except Exception as err:
#             log_grava(
#                 err=err,
#                 msg= "INVESTIGAR: "+disciplina.modulo+" - "+disciplina.disciplina+"\n"+enunciado
#             )
                                
#             cont-=1
#             if not cont:
#                 raise ConnectionError    

#     # obtém as alternativas do dict data_enunciados
#     alternativas_dict = data_enunciados['0']['alternativas'].values()

#     # verifica se todas as alternativas da lista estão no dict
#     todas_presentes = all(texto in alternativas_dict for texto in lista_formatada)

#     todas_presentes

#     if todas_presentes:
#         gabarito = data_enunciados['0']['gabarito']
#     else:
#         gabarito = None       

#     return gabarito


