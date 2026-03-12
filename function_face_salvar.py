import json
from selenium.common.exceptions import SessionNotCreatedException, ElementNotInteractableException

from system.chrome import iniciar_sesssao_chrome_fb

import traceback, requests

from utils.utils_facebook import type_in_contenteditable

view_chromedriver = False 
# view_chromedriver = True # para Oculto e True para exibir navegador

try:
    import os
    import random
    import time

    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    from function_bd import abre_json
    from system.chrome import iniciar_sesssao_chrome_fb
    from system.crypto import recodification

except Exception as err:
    import traceback
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print(msg)
    time.sleep(15)

def t(k):
    time.sleep(k)

def entrar_fb(driver, wait):

    # Verifica se já não está logado
    cont = 10
    wait_verifica=WebDriverWait(driver, 0.5)
    while cont:
        try:
            wait_verifica.until(EC.presence_of_element_located((By.XPATH,"//span[text()='Amigos']")))
            print("Achou AMIGOS")
            break
        except TimeoutException:

            try:
                print(" Não encontrou \"Amigos\" ")
                wait_verifica.until(EC.presence_of_element_located((By.XPATH,"//span[text()='Criar story']")))
                print("Achou CRIAR STORY")
                break
            except TimeoutException:
                print(" Não encontrou \"Criar Story\" ")

            try:
                # Se não estiver loga
                campo_login = wait.until(EC.presence_of_element_located((By.NAME, "email")))
                campo_senha = wait.until(EC.presence_of_element_located((By.NAME, "pass")))
                botao_confirmar = wait.until(EC.presence_of_element_located((By.NAME, "login")))
                campo_login.clear()
                campo_senha.clear()
                print("    - Inserindo Login/Senha")
                campo_login.send_keys(username)
                campo_senha.send_keys(password)
                driver.execute_script("arguments[0].click();", botao_confirmar)
                break

            except TimeoutException:
                cont-=1

    if not cont:
        print("Vai tentar dar um de louco e tentar postar, vai que tá logado")
        # raise TimeoutException
    
def clicar_input_texto(driver,wait):

    # element = wait.until(EC.presence_of_element_located((By.XPATH,"//span[contains(@style, '-webkit-box-orient: vertical') and contains(@style, '-webkit-line-clamp: 2') and contains(@style, 'display: -webkit-box')]")))
    body = wait.until(EC.presence_of_element_located((By.TAG_NAME,'body')))
    body.send_keys(Keys.ESCAPE)
    # driver.execute_script("arguments[0].click();", element)
    print("    - Entrou no GRUPO")
    try:
        elemento = wait.until(EC.presence_of_element_located((By.XPATH,"//span[text()='Escreva algo...']")))
        driver.execute_script("arguments[0].click();", elemento)
        print("    - Clicou na Caixa de Texto: \"Escreva Algo...\"")
    except TimeoutException:
        print("   ==>> Não localizou a caixa de texto.")
        raise TimeoutException

def clicar_bg(driver,wait):
    try:
        print("       -> Clicando")
        xpath_fundo = "//img[@src='/images/composer/SATP_Aa_square-2x.png']"
        btn_fundo=wait.until(EC.presence_of_element_located((By.XPATH,xpath_fundo)))
        driver.execute_script("arguments[0].click();", btn_fundo)
    except TimeoutException:
        print("Não encontrou o elemento de Plano de Fundo")

def escolher_bg(driver,wait):
    try:
        print("       -> Verificando opçoes")
        xpath_opcoes_plano_fundo = "//div[@aria-label='Opções de plano de fundo']"
        btn_opcoes_plano_fundo=wait.until(EC.presence_of_element_located((By.XPATH,xpath_opcoes_plano_fundo)))
        driver.execute_script("arguments[0].click();", btn_opcoes_plano_fundo)
    except:
        print("Não encontrou + Planos de Fundo")

def selecionar_bg(driver,wait):
    from system.chrome import atualizar_soup

    print("       -> Selecionando uma opção")
    t(4)
    soup = atualizar_soup(driver)

    # Obtém os labels com os BG disponíveis
    labels = soup.find_all("div",{"aria-current":"false"})
    lista = []


    for label in labels:
        try:
            if "marrom" in label.get("aria-label"):# or "sólido" in label.get("aria-label"):
                continue
            lista.append(label.get("aria-label"))
        except TypeError:
            pass
    
    # for elm in lista:
    #     print(f" - {elm}")

    bg = random.choice(lista)

    try:
        xpath_fundo_selecao = "//div[@aria-label='"+bg+"']"
        xpath_fundo_selecao=wait.until(EC.presence_of_element_located((By.XPATH,xpath_fundo_selecao)))
        driver.execute_script("arguments[0].click();", xpath_fundo_selecao)
        print(f"       -> Background Selecionado: {bg} de {len(lista)}")
    
    except TimeoutException:
        print("Não conseguiu clicar no BG")
    
    t(2)

def enviar_link(driver,wait,link_grupo):
    cont = 3
    while cont:
        try:
            css = "span[data-offset-key]"
            popup=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,css)))
            driver.execute_script("arguments[0].click();", popup)
            print("    - Escrevendo link na caixa de texto")
            t(1)
            popup.send_keys(link_grupo)
            print("      ==> Finalizou a escrita.")
            break
        
        except ElementNotInteractableException as err:
            cont-=1
            print("   ==>> Elemento de Pop-up não carregou")
            t(8)
            
        except TimeoutException as err:
            cont-=1
            print("   ==>> Não foi possível inserir o link, pois Pop-up não carregou")
            SELECTOR = "div[aria-label='Escreva algo...'][contenteditable='true']"
            type_in_contenteditable(driver, link_grupo, selector=SELECTOR, timeout=15)
            t(8)
            break
        
        if not cont:
            raise Exception

def remover_previa(driver,wait):
    try:
        xpath_link_wsp = "//div[@aria-label='Remover prévia do link da sua publicação']"
        x_wsp=wait.until(EC.presence_of_element_located((By.XPATH,xpath_link_wsp)))
        driver.execute_script("arguments[0].click();", x_wsp)

        xpath_fundo = "//img[@src='/images/composer/SATP_Aa_square-2x.png']"
        x_fundo=wait.until(EC.presence_of_element_located((By.XPATH,xpath_fundo)))
        driver.execute_script("arguments[0].click();", x_fundo)
        t(3)

    except TimeoutException:
        print("      =>> Não apareceu a PRÉVIA.")

def publicar_post(driver,wait):
    try:
        print("    - Publicando Post")
        xpath_publicar = "//div[@aria-label='Postar']"
        btn_publicar=wait.until(EC.presence_of_element_located((By.XPATH,xpath_publicar)))
        driver.execute_script("arguments[0].click();", btn_publicar)
        print("    ======> POST PUBLICADO <====== ")
        t(10)
    except TimeoutException:
        print("   Botão POSTAR não localizado.")
        try:
            botao_publicar = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//span[normalize-space()='Postar']/ancestor::*[self::button or @role='button'][1]"
                ))
            )
            driver.execute_script("arguments[0].click();", botao_publicar)
        except Exception as err:
            from selenium.webdriver.common.keys import Keys

            pass


URL = "https://www.facebook.com"

try:
    import logging
    logging.getLogger('WDM').setLevel(logging.NOTSET)

    # Muda o diretório de trabalho para o diretório onde o script está localizado
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Dados do usuário
    path_file = os.getcwd()+"\\user_facebook.json"
    data_geral = abre_json(path_file=path_file)
    
    while(data_geral):
    
        # Selecionar um usuário aleatório
        chave_aleatoria = random.choice(list(data_geral.keys()))

        # Separa os dados da chave aleatória
        data = data_geral.pop(chave_aleatoria)

        username = recodification(data['usuario'])
        password = recodification(data['password'])
        print(f">> user:{username}")
        t(5)

        try:
            # Abrindo Chromedriver
            print("Abrindo Chrome")
            driver = iniciar_sesssao_chrome_fb(path_profile=data["path_profile"],view=view_chromedriver)
            print("Abriu Chrome") 
            driver.get(URL)
            wait = WebDriverWait(driver, 10)

            # entrar no perfil do face
            entrar_fb(driver=driver,wait=wait)

            for i in range(1):

                print("\n\n   NOVO POST")
                
                cont = 7
                while cont:
                    try:                
                        #entrar no grupo
                        url = "https://www.papiron.com.br/api/frases/random/?midia=grupo_facebook"
                        req = requests.get(url=url)
                        data = req.json()
                        url_grupo_fb = data["url"]
                        faculdade = data["faculdades"][0] # só tem 1 faculdade neste caso

                        url_frase = f"https://www.papiron.com.br/api/frases/random/?q={faculdade.upper()}&midia=facebook"
                        req_frase = requests.get(url=url_frase)
                        data_frase = req_frase.json()

                        frase_selecionada = data_frase["texto_completo"]

                        print(f"\n   Usuário e Grupo selecionados:\n      {username}\n      Grupo: {data['texto']}\n      Frase: {frase_selecionada}\n")
                        driver.get(url=url_grupo_fb)
                        
                        #clicar na área de postagem
                        clicar_input_texto(driver,wait)

                        # Escolher o fundo
                        print("    - Background:")
                        clicar_bg(driver,wait)
                        escolher_bg(driver,wait)
                        selecionar_bg(driver,wait)

                        # Digitar na caixa de texto o grupo
                        enviar_link(driver=driver,wait=wait,link_grupo=frase_selecionada)

                        # Remover caso prévia de link apareça
                        remover_previa(driver=driver,wait=wait)

                        # Publicar o post
                        publicar_post(driver,wait)

                        break
                    except Exception as err:
                        cont-=1
                        print(f"    Não foi possível gerar post nesta tentativa, restantes: {cont}")
                        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                        print(msg)
                        
                        if not cont:
                            import traceback 
                            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                            print("Erro:", cont , msg)
                            # depois de erros seguidos, 
                            # vai para a próxima tentativa
                            break
                
                # Tempo para esperar entre as postagens do mesmo user
                tempo_espera_postagens = random.randint(4,10)

                print(f"    Tempo de espera entre mensagens: {tempo_espera_postagens}")
                time.sleep(tempo_espera_postagens*60)


            # Tempo para esperar entre as postagens de user diferentes
            driver.quit()
            # tempo_espera_usuario = random.randint(42,93)
            tempo_espera_usuario = random.randint(5,9)
            # tempo_espera_usuario = 0
            print(f"    Tempo de espera para troca de usuário: {tempo_espera_usuario}")
            time.sleep(tempo_espera_usuario*60)

        except SessionNotCreatedException:
            print(f"\n   Falhou em abrir para {username}")


except Exception as err:
    import traceback
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print(msg)
    try:
        driver.quit()
    except NameError:
        pass
    time.sleep(15)

