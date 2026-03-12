import time

from bs4 import BeautifulSoup as BS
from genericpath import isfile
from requests.exceptions import ConnectionError
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchWindowException,
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import MaxRetryError

from class_papiron.class_error import SenhaError
from system.logger import log_grava
from system.pastas import construir_path_chromedriver


def chromedriverVersion(options):
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    # Configurando o gerenciador de driver do Chrome
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=options)
    driver.quit()

def chrome_view():
    """
    Atualiza a visualização do Chrome conforme seleção do usuário 
    """
    import os

    from function_bd import abre_json

    try:
        # Obtem os registros salvos do usuário
        path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
        data = abre_json(path_file)

        try:
            # Retorna a seleção atualizado do usuário
            return data["cb_chrome_view"]
        except KeyError:
            return True
    
    except FileNotFoundError:

        return True

def iniciar_sesssao_chrome(**kwargs):
    import os
    import shutil
    import traceback
    from pathlib import Path

    # from seleniumwire import webdriver
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    n_thread = str(kwargs.get("n_thread",""))

    # Instancia um objeto Options do webdriver
    options = webdriver.ChromeOptions()

    # Verifica o modo do Chromedriver
    view = kwargs.get('view',chrome_view())
    
    if not view:
        options.add_argument("--headless") #become Chrome hidden
    else:
        options.add_argument("--start-minimized")

    # Informa o local de DOWNLOAD
    path_download = str(Path.home())+"\\Desktop\\Papiron\\Downloads\\Temp"
    
    # Configurações Iniciais do Webdriver
    prefs = {
        "download.default_directory": path_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        # "safebrowsing.enabled": True,
        "safebrowsing_for_trusted_sources_enabled": False,
        "safebrowsing.enabled": False,
        "profile.default_content_setting_values.automatic_downloads": 3,
    }
    # Atribuindo as config iniciais
    options.add_experimental_option('prefs', prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--kiosk-printing') # Ativa o modo kiosk
    options.add_argument('--disable-print-preview') # Desabilita a pré-visualização da impressão
    options.add_argument('--disable-dev-shm-usage') # Evita problemas de memória
    options.add_argument("--log-level=4")
    cont = 3
    driver = None
    while cont:
        # Monta o local de onde deve estar localizado o arquivo do Chromedriver
        
        try:
            file , file_origin = construir_path_chromedriver(n_thread=n_thread)
            if not os.path.isfile(file): shutil.copyfile(file_origin, file)
            driver = webdriver.Chrome(executable_path=file , options=options)
            break

        except (PermissionError, ConnectionError, TypeError, SessionNotCreatedException) as err:
            """
            TypeError - não há nada na pasta do Chromedriver, instalações novas.
            """
            try:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f"\n\nErro 1501: {msg}")
                driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                break
            
            except (PermissionError, ConnectionError, TypeError, SessionNotCreatedException) as err:
                # Monta novamento o local de onde deve estar localizado o arquivo do NOVO Chromedriver
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f"\n\nErro 1502: {msg}")
                try:
                    file , file_origin = construir_path_chromedriver(n_thread=n_thread)
                    if not os.path.isfile(file): shutil.copyfile(file_origin, file)
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    driver = webdriver.Chrome(executable_path=file , options=options)
                    break
                except Exception as err:
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    print(f"\n\nErro 1503: {msg}")

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f"Erro 1504 NÃO PREVISTO : {msg}")
                raise Exception

        driver = chrome_encerra(driver)
        cont -=1
    
    if driver:
        # driver.minimize_window()
        driver.maximize_window()
        return driver 
    else:
        print("Erro fatal Chromedriver >>> Verifique se há atualizações no Chrome")
        return None


def iniciar_sesssao_chrome_fb(path_profile, **kwargs):
    import os
    import shutil
    import traceback

    # from seleniumwire import webdriver
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    # log.s setLevel('CRITICAL')
    from system.pastas import pasta_mais_recente

    # Instancia um objeto Options do webdriver
    options = webdriver.ChromeOptions()

    import logging

    from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
    seleniumLogger.setLevel(logging.WARNING)
    # Set the threshold for urllib3 to WARNING
    from urllib3.connectionpool import log as urllibLogger
    urllibLogger.setLevel(logging.WARNING)  

    # Verifica o modo do Chromedriver
    view = kwargs.get('view',)

    n_thread = "01"
    
    if not view:
        options.add_argument("--headless")
    else:
        options.add_argument("--start-minimized")
    
    options.add_argument("user-data-dir="+path_profile)
    cont = 3
    driver = None
    while cont:
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
            driver.minimize_window()
            break

        except (PermissionError, ConnectionError, SessionNotCreatedException) as err:
            dir_chrome = os.path.join(os.path.expanduser("~"),"")+".wdm\\drivers\\chromedriver\\win64\\"
            dir_exe = dir_chrome+pasta_mais_recente(dir_chrome)+"chromedriver-win32\\"
            file_origin = dir_exe+"chromedriver.exe"
            file = dir_exe+"chromedriver"+n_thread+".exe"
            
            try:
                if not os.path.isfile(file): shutil.copyfile(file_origin, file)
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                # print("ERRO x:", msg, "\nFILE:", file)
                driver = webdriver.Chrome(executable_path=file , options=options)
                driver.minimize_window()
                break
            except Exception as err:
                print("ERRO: VERFICAR:", str(err))
            
    if driver:
        print("Abriu Chrome")
        if view:
            driver.maximize_window()
        else:
            driver.minimize_window()
        return driver 
    else:
        print("Erro fatal Chromedriver >>> Verifique se há atualizações no Chrome")
        return None


def chrome_encerra(driver): 
    try: driver.quit() 
    except Exception: pass
    
def login(driver,username:str,password:str):
    from system.system import t

    # Navega para a página que deseja
    url = "https://studeo.unicesumar.edu.br/#!/access/login"
    cont_driver = 2 ; dt=0
    cont_delta = 1  ; 

    while cont_driver:
        try:
            
            # Verifica se tem um driver ativo, se não tiver, inicia.
            if not driver:
                import random
                print("Reiniciando o Chromedriver novamente:", driver)
                driver = iniciar_sesssao_chrome(n_thread = random.randint(0,50))
                dt = 13
            delta_espera = 10 + dt
            # Aguarde encontrar todos os elementos para o campo de login, 
            # campo de senha e botão de confirmação
            driver.get(url)
            print("Procurando e inserindo nos elementos") 
            wait = WebDriverWait(driver, 30)
            campo_login = wait.until(EC.presence_of_element_located((By.ID, "username")))
            campo_senha = wait.until(EC.presence_of_element_located((By.ID, "password")))
            css_btn_confirm = "#login-form-studeo > div:nth-child(3) > form > div.row > div > button[type='submit']"
            botao_confirmar = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_btn_confirm)))
            campo_login.clear()
            campo_senha.clear()
            campo_login.send_keys(username)
            campo_senha.send_keys(password)
            # Clique no botão de confirmação
            time_i = time.time()
            driver.execute_script("arguments[0].click();", botao_confirmar)
            
            # Espera até que sai da página de login
            ult_div(driver)
            url_new = url
            delta = 0
            while url == url_new:

                # Verifica se houve mudança na URL
                url_new = driver.current_url
                
                # Calcula o tempo decorrido da execução
                time_f = time.time()
                delta = time_f - time_i
                delta = round(delta,2)
                
                if delta>delta_espera:
                    
                    if cont_delta:
                        raise TimeoutError
                    
                    else:
                        print("Falhou Login", delta>delta_espera, delta)
                        log_grava(msg="[LOGIN]: Falhou login: "+ username +" - "+ password + "delta:["+str(delta_espera)+"]")
                        raise SenhaError

            print("   >>> LOGIN EFETUADO COM SUCESSO", delta, url_new)
            return driver 

        
            
        except TimeoutError as err:

            # Verifica se houve falha mesmo:
            t(5)
            list_urls = ["https://studeo.unicesumar.edu.br/#!/access/rules", "https://studeo.unicesumar.edu.br/#!/app/home"]
            if driver.current_url in list_urls: return driver
            
            cont_delta = None ; dt = 12 ; driver.get(url); t(0.5); ult_div(driver)

            # Refaz a ligação do Chromedriver
            cont_driver -= 1
            driver = chrome_encerra(driver) 
            print("Falhou login, primeira tentativa.")
            if not cont_driver: print("   >> ERRO: Erro de Senha") ; raise SenhaError
        
        # Caso a janela feche ou ocorra algum erro
        except (WebDriverException, NoSuchWindowException, MaxRetryError, TimeoutException) as err:
            cont_driver -= 1
            driver = chrome_encerra(driver)
            print(f"Driver Exception - {cont_driver} : {err}")  
            if not cont_driver: 
                print("   >> ERRO: Erro de Chromedriver") 
                return None


    return None

def ult_div(driver)->None:
    """
    Esperar que o último <div> seja carregado
    """
    from bs4 import BeautifulSoup as BS

    t(1.5)
    T=50
    dt=1
    while T:
        try:
            css_body = "body"
            body = WebDriverWait(driver, 0.001).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_body)))
            return True
        
        except TimeoutException:
            T-=dt
            t(dt/10)
    return False

def f5(driver):

    return False
    T = 3
    dt = 1
    while T>0:
        try:
            ult_div(driver)
            # css_f5 = "body > div.modal.stick-up.fade.ng-scope.ng-isolate-scope.in > div > div > div > div.modal-footer > button"
            xpath_btn = "//button[@ng-click='$ctrl.ok()']"
            btn_f5 = WebDriverWait(driver, 0.01).until(EC.element_to_be_clickable((By.XPATH,xpath_btn)))
            driver.execute_script("arguments[0].click();",btn_f5)
            # print("   >> F5 Localizado: ",driver.current_url)
            return True
        except TimeoutException:
            T -= dt
            time.sleep(dt/10)
    # print("   >> Tela F5 não localizada:",driver.current_url)
    return False

def atualizar_soup(driver):
    html = driver.page_source
    soup = BS(html, 'html.parser')
    return soup

def login_papiron(user:str,password:str,url_base:str)->any:
    """
    Realiza o login via RequestHTTP no site Papiron 
    
    Variáveis:
    +++
        - user: email do usuário do site
        - password: senha do site
    """
    import urllib.parse

    import requests as rq
    from bs4 import BeautifulSoup as BS

    # if "www" in url_base:
    url_host = "www.modelitos.com.br" if "modelitos" in url_base else "www.papiron.com.br"
    # else:
    #     url_host = "127.0.0.1"
    
    # Inicia a requisição no site Papiron
    url = url_base+"/usuarios/login?action=logar"
    print("ini:", url)
    r = rq.get(url)

    # Scrapped dos dados iniciais
    csrftoken = r.cookies['csrftoken']  # token da sessão da página
    soup = BS(r.content, "html.parser")
    csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})['value']  # token de segurança do form

    print("csrf:" , csrfmiddlewaretoken)

    # Cria postdata para envio das informações ao request post
    postdata = "csrfmiddlewaretoken="+csrfmiddlewaretoken+"&id=None&next=&email="+urllib.parse.quote(user)+"&senha="+urllib.parse.quote(password)

    # print("csrf:" , csrfmiddlewaretoken , postdata)

    COOKIES = "csrftoken="+csrftoken
    headers = { "Cookie":COOKIES,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding":"gzip, deflate, br",
                "Accept-Language": "pt-BR,pt;q=0.9,es;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Content-Length": str(len(postdata)),
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": url_host,
                "Origin": url_base,
                "Referer": url_base+"usuarios/login?action=logar",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
            }

    # print(headers)

    r1 = rq.post(url, headers=headers, data = postdata , allow_redirects=False, timeout=60)
    sessionid = r1.cookies['sessionid']
    csrftoken_2= r.cookies['csrftoken']
    COOKIES = "csrftoken="+csrftoken_2+";sessionid="+sessionid

    headers = { "Cookie":COOKIES,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding":"gzip, deflate, br",
                "Accept-Language": "pt-BR,pt;q=0.9,es;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Content-Length": "0",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": url_host,
                "Origin": url_base,
                "Referer": url_base+"usuarios/login?action=logar",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
            }
    r2 = rq.get(url, headers=headers , allow_redirects=False)
    soup = BS(r2.content, "html.parser")
    if r2.status_code == 200:
        print("Logou no Papiron:",r2 , r2.status_code, headers)
    else:
        print("Falhou em logar no Papiron!")
    return headers

def logout(driver):
    try:
        xpath_btn = "//a[@ui-sref='access.logout']"
        wait = WebDriverWait(driver,2)
        btn_aviso = wait.until(EC.presence_of_element_located((By.XPATH,xpath_btn)))
        driver.execute_script("arguments[0].click();", btn_aviso)
        t(1)
        ult_div(driver)
        return driver
    except TimeoutException:
        return None

def t(k):
    import time
    time.sleep(k)

def terminate_chrome_processes():
    import psutil

    # return None
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'chromedriver.exe':  # Para Chrome no Windows, altere para 'chrome' se estiver em outro SO.
        # if process.info['name'] == 'chrome.exe' or process.info['name'] == 'chromedriver.exe':  # Para Chrome no Windows, altere para 'chrome' se estiver em outro SO.
            try:
                process.terminate()
            except psutil.NoSuchProcess:
                pass

