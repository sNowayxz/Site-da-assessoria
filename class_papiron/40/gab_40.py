# url_gabarito = f"{self.url_base}/atividades/form/gabarito_automatico"


from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import traceback

import random
import string

import requests as rq
from requests_toolbelt import MultipartEncoder
from bs4 import BeautifulSoup as BS

from function_bd import integridade_bd
from dict_lista_curso import dict_curso_sigla_nome
from function_bd import save_json
from functions.curso import dict_curso
from system.chrome import login_papiron, t
from system.logger import log_grava

# path_dir = os.getcwd()

keys_exclusao =  ["STATUS_ATIVIDADE","ID_URL","LISTA_ID_URL","DT_INICIO", "DT_FIM"]

FACULDADE = "UNICESUMAR"

class Rotinas_Gabarito(QObject):
    finished = pyqtSignal()

    updateProgress_gabarito = pyqtSignal(int, str)

    def __init__(self, ui , cursos, modulo, username, password, i, config) :

        super().__init__()

        self.ui = ui
        self.cursos = cursos
        self.username = username
        self.password = password
        self.i = i
        self.config = config
        self.modulos_abertos = config['MODULOS_ABERTOS']
        
    def run_enviar_gabaritos(self):

        # urls 
        url_base ="https://www.modelitos.com.br"

        # Cria sessão em Papiron
        headers = login_papiron(self.username,self.password,url_base)

        lista_exclusiva = []
        if self.config['postar_cursos']:
            lista_exclusiva = [item.strip().upper() for item in self.config['postar_cursos'].split(",") if item.strip()]

        print("lista:", lista_exclusiva)

        try:
    
            cursos_apelido = dict_curso(opcao=5)

            for sigla in self.cursos:

                # print(sigla)

                for modulo in self.modulos_abertos:

                    #Verifica a integridade e a existência do BD da curso (sigla)
                    data , path_file = integridade_bd(sigla, modulo)

                    # Verifica se existe arquivo do curso, se não houver passa para o próximo curso
                    if not data:
                        self.updateProgress_gabarito.emit(1 , "Não há dados do Curso: "+sigla)
                        continue
                    elif not data[sigla]:
                        self.updateProgress_gabarito.emit(1 , "Não há dados: "+sigla)
                        continue

                    if data:

                        for curso in data:
                            
                            # Caso esteja inserido pelo meno um curso
                            if lista_exclusiva:
                                if curso not in lista_exclusiva:
                                    continue
                            
                            if curso == 'GERAL':
                                if not self.config['cb_geral']:
                                    print("     Vai para o próximo pois é GERAL")
                                    continue

                            print(f"\n  - {self.i}: INICIANDO O ENVIO DOS GABARITOS EM:",cursos_apelido[sigla])

                            for disciplina in data[curso]:

                                print("   >", disciplina)

                                # Se for inserida uma disciplina específica:
                                if self.config['disciplina_unica']:
                                    print("   >> Foi inserida disciplina exclusiva")
                                    if self.config['disciplina_unica'].upper()!=disciplina.upper():
                                        continue
                                
                                # Caso esteja marcada a opção SCG, irá fazer apenas essa atividade
                                if self.config['cb_scg']:
                                    if "SEMANA DE CONHECIMENTOS GERAIS" not in disciplina:
                                        continue
                                else:
                                    if "SEMANA DE CONHECIMENTOS GERAIS" in disciplina:
                                        continue

                                if modulo in data[curso][disciplina]:

                                    for atividade in list(data[curso][disciplina][modulo]['ATIVIDADE']):
               
                                        # Chave não relacionada a atividade
                                        if atividade in keys_exclusao:
                                            continue
                                        
                                        data_atividade = data[curso][disciplina][modulo]['ATIVIDADE'][atividade]
                                        
                                        print("    >>", atividade)
                                        
                                        for questao in list(data_atividade): 

                                            # caso seja uma key indesejada, vai para a próxima
                                            if questao in keys_exclusao:
                                                continue

                                            data_questao = data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]

                                            # Se a questão não for questionário, vá para próxima
                                            if data_questao['ESTILO'] != 'QUESTIONARIO':
                                                print("       -> Discursiva\n", atividade)
                                                continue
                                            
                                            # obtém ID_URL e verifica se existe
                                            id_url_questao = data_questao.get('ID_URL')
                                            if not id_url_questao:
                                                # Não encontrou, então irá continuar a rotina para criar novo ID_URL
                                                print(f"     >> Questão ainda não foi enviada - {questao}")
                                                continue
                                            
                                            # Verifica se o Gabarito já foi enviado em outra oportunidade
                                            gabarito_enviado = data_questao.get("GABARITO_OK")
                                            print(" Njfrga", gabarito_enviado)
                                            gabarito = data_questao.get('GABARITO')
                                            if not gabarito:
                                                print(f"    >> {modulo}|{curso}|{atividade}|{questao}|{id_url_questao} - Não possui gabarito")
                                                continue
                                                
                                            elif gabarito_enviado:

                                                print("111111111",self.config['cb_corrige_gabarito'])
                                                t(3)

                                                if self.config['cb_corrige_gabarito']:

                                                    print("111.222")

                                                    try:
                                                        self.corrigir_gabarito(
                                                            headers,
                                                            data,
                                                            data_questao,
                                                            path_file,
                                                            atividade, 
                                                            questao,
                                                            id_url_questao
                                                        )
                                                    except InterruptedError:
                                                        print("111.44")
                                                        continue

                                                    except Exception as err:
                                                        log_grava(err=err)
                                                        continue

                                                else:
                                                    print("111.333")
                                                    # Gabarito já foi enviado e não está marcado que é para corrigir
                                                    continue
                                            
                                            elif not gabarito_enviado and gabarito:
                                                # não consta como gabarito enviado ainda e já tem o gabarito
                                                print("ddddffff")
                                                t(10)
                                                # URL no site para enviar o gabarito
                                                url_form_gabarito = url_base+"/atividades/form/gabarito_automatico"
                                                r_gab_enviado = self.enviar_gabarito(
                                                                        headers,
                                                                        id_url_questao,
                                                                        gabarito,
                                                                        url_form_gabarito,
                                                                        questao)
                                                    
                                                    
                                                    
                                                    # headers,id_url_questao,gabarito,url_form_gabarito,questao)
                                                
                                                if r_gab_enviado.status_code == 200:
                                                    data_questao['GABARITO_OK'] = "OK"
                                                    print(f"         >> Envio do gabarito finalizado com sucesso: {curso} - {disciplina} - {atividade} {id_url_questao}" )

                                                else:
                                                    print("         >> ERRO AO ENVIAR O GABARITO [CODE00]: "+id_url_questao )
                                                    t(30)
                                            
                                            else:
                                                continue

                                            save_json(data,path_file)

                        self.updateProgress_gabarito.emit(1 ,  "["+curso+"] Salvando informações no Banco de Dados:")
                        save_json(data,path_file)
                    
                    print(f"Finalizou: {sigla}\n x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x ")
        
        except KeyError as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"Falha no login Papiron"
            self.updateProgress_gabarito.emit(1000 , "[PAPIRON] - Falha no login Papiron")
            self.finished.emit()
            print(msg)
            return None

        except Exception as err:
            try:
                sigla = sigla
                
            except UnboundLocalError:
                sigla = "SEM SIGLA"

            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"XXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxxx\n\n>>>>>> FALHA NO CURSO:  "+sigla+"\n\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            print(msg)
            return None
    
    def enviar_gabarito(
            headers,
            id_url_questao,
            gabarito,
            url,
            questao
        ):

        print("!uadfld",  url , questao)

        r = rq.get(url,headers=headers)
        soup = BS(r.content, "html.parser")
        csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})['value']
                                
        fields = {
                'csrfmiddlewaretoken': csrfmiddlewaretoken,
                'id_url':id_url_questao,
                'gabarito':gabarito,
                'hash_quest': questao, 
                }
        
        boundary = '----WebKitFormBoundary' \
                + ''.join(random.sample(string.ascii_letters + string.digits, 16))
        m = MultipartEncoder(fields=fields, boundary=boundary)

        headers_b={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",   
            "Cookie": headers['Cookie'],
            "Content-Length":str(len(str(m))),
            "Host": "www.papiron.com.br",
            "Origin": "https://www.papiron.com.br",
            "Referer": url,
            "Content-Type": m.content_type,
            "Upgrade-Insecure-Requests": "1"}
        
        r = rq.post(url, headers=headers_b , data = m , allow_redirects=False,timeout=60)

        return r

    def corrigir_gabarito(
            self,
            headers,
            data,
            data_questao,
            path_file,
            atividade, 
            questao,
            id_url_questao
        ):

        print("111.222.1111" , id_url_questao)

        # urls 
        url_base ="https://www.modelitos.com.br"
        url_pergunta = url_base+"/atividades/"
        url = "https://www.modelitos.com.br/atividades/idurl/"+id_url_questao

        try:
            print("     >> Verificar se a questão está publicada:", atividade, questao)    
            
            # Envia a requisição ao site
            r = rq.get(url)
            print(f"       Resultado do gabarito a ser corrigido: {r}")

            if r.status_code == 404:
                # Como não localizou, vai a próxima, não adianta enviar se a questão
                # saiu do site, apaga o registro o id_url para quando for realizar em outro
                # outro momento.
                data_questao['ID_URL'] = None
                print(f"\n\n >>> [ATENÇÃO]: ID_URL NÃO Localizada no site: {id_url_questao}\n\n")
                raise InterruptedError
            
            elif r.status_code!=200:
                # Se for algum erro de servidor, ignora, apenas aguarde algum tempo para restabelecer
                t(60)
            
            else:
                # A questão já está publicada, segue para a verificação do gabarito (r.code=200)
                url_gabarito = url_pergunta+"gabarito/"+id_url_questao
                r_gab = rq.get(url_gabarito,headers=headers)
                print(f"        [{r_gab}]")

                if r_gab.status_code == 404 or r_gab.status_code == 200:

                    if r_gab.status_code == 404:
                        print("         Gabarito a ser enviado:", id_url_questao)
                    else:
                        print("         Gabarito sendo reenviado:", id_url_questao)

                    gabarito = data_questao['GABARITO']

                    r_gab_enviado = self.enviar_gabarito(
                        headers,
                        gabarito,
                        questao,
                        id_url_questao,
                    )
                    
                    if r_gab_enviado.status_code == 200:
                        data_questao['GABARITO_OK'] = "OK"
                        print("         >> Reenvio do gabarito finalizado com sucesso: "+id_url_questao )
                        save_json(data,path_file)

                    else:
                        print("         >> ERRO AO ENVIAR O GABARITO [CODE00]: "+id_url_questao )
                        t(30)
                    alternativas = data_questao['ALTERNATIVAS']
                    print(F" -- {atividade} - {questao}")
                    print(F"    {alternativas}")

                elif r.status_code == 500:
                    print("Usuário não logou")
                    quit()

                elif r.status_code == 200:
                    print("         Gabarito já enviado, mas não estava salvo! ", id_url_questao )
                    data_questao['GABARITO_OK'] = "OK"
                    save_json(data,path_file)

                else:
                    print(f"    >>> Code Status: {r_gab.status_code}" )
                               
        
        except TypeError as err:
            print("    >>>> Erro de TypeError: ", atividade,questao)
            log_grava(err=err)

        except rq.ReadTimeout as err:
            print("    >>>> Demora na resposta do servidor")
            log_grava(err=err)

        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print("Erro1: ",msg)
            log_grava(err=err)
