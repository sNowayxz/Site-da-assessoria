import os

import requests as rq
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from function_bd import integridade_bd

import json
import random
import string
import traceback

from requests.exceptions import ConnectTimeout, ConnectionError

from requests_toolbelt import MultipartEncoder

from dict_lista_curso import dict_curso_sigla_nome
from function_bd import save_json
from system.chrome import login_papiron, t


from bs4 import BeautifulSoup as BS

from system.logger import log_grava

path_dir = os.getcwd()

keys_exclusao =  ["STATUS_ATIVIDADE","ID_URL","LISTA_ID_URL","DT_INICIO", "DT_FIM"]

FACULDADE = "UNICESUMAR"

class Rotinas_PostarAtividades(QObject):
    finished = pyqtSignal()
    updateProgress_postar = pyqtSignal(int, str)

    def __init__(self,ui,config,cursos,i) :

        super().__init__()

        self.ui = ui
        self.config = config
        self.cursos = cursos
        self.username = self.config['username']
        self.password = self.config['password']        
        self.modulos_abertos = config['MODULOS_ABERTOS']
        self.i = i
        
    def run_postar_atividades(self):

        lista_exclusiva = []
        if self.config['postar_cursos']:
            lista_exclusiva = [item.strip().upper() for item in self.config['postar_cursos'].split(",") if item.strip()]

        print("lista:", lista_exclusiva)

        try:
            
            # urls 
            url_base ="https://www.modelitos.com.br"
            self.url_base ="https://www.modelitos.com.br/"
            self.url_pergunta = self.url_base+"atividades/"

            # Cria sessão em Papiron
            headers = login_papiron(self.username,self.password,url_base)

            cursos_apelido = dict_curso_sigla_nome()

            for sigla in self.cursos:

                # print(sigla)

                for modulo in self.modulos_abertos:

                    #Verifica a integridade e a existência do BD da curso (sigla)
                    data , path_file = integridade_bd(sigla, modulo)

                    # Verifica se existe arquivo do curso, se não houver passa para o próximo curso
                    if not data:
                        self.updateProgress_postar.emit(1 , "Não há dados do Curso: "+sigla)
                        continue
                    elif not data[sigla]:
                        self.updateProgress_postar.emit(1 , "Não há dados: "+sigla)
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

                            print(f"\n  - {self.i}: INICIANDO A POSTAGEM EM:",cursos_apelido[sigla])

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

                                        # Se já existe um id_url para a ATIVIDADE, então passe para a próxima atividade 
                                        # caso esteja desmarcado a verificação no site
                                        id_url_atividade = data_atividade.get("ID_URL")

                                        if not self.config['cb_verificar_idurl_site'] and id_url_atividade:

                                            print(f"\n   >> Localizada a id_url ATIVIDADE no BD: {disciplina} - {atividade} - {id_url_atividade}\n")

                                            # Verificar se ainda é o mesmo ID_URL, somente se tiver lista
                                            # atividades discursivas tem a lista Vazia, essas atividades serão verificadas na própria questão
                                            lista_id_url_verifica = data_atividade.get('ID_URL')
                                            if lista_id_url_verifica and lista_id_url_verifica:
                                                if self.verificar_lista_id_urls(id_url_atividade , lista_id_url_verifica):
                                                    continue
                                        
                                        print("    >>", atividade)
                                        
                                        # aloca lista para receber todos id_urls de questionário
                                        # id_url se refere ao id_url da atividade, seja, Questionário completo
                                        lista_id_url = []
                                        id_url = None
                                        tamanho_data_atividade = len(list(data_atividade))
                                        for questao_n, questao in enumerate(list(data_atividade)): 

                                            # caso seja uma key indesejada, vai para a próxima
                                            if questao in keys_exclusao:
                                                continue

                                            data_questao = data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]

                                            # print("     >>>> ",atividade, questao_n, questao,lista_id_url,data_questao)

                                            # Quando quiser postar apenas discursivas
                                            if self.config['cb_discursivas']:
                                                if data_atividade[questao].get('ESTILO') == "QUESTIONARIO":
                                                    continue
                                          
                                            id_url_questao = data_questao.get('ID_URL')
                                            print(f"\n     HASH Questão: {questao.upper()} : {id_url_questao}") 
    
                                            if not id_url_questao:
                                                # Não encontrou, então irá continuar a rotina para criar novo ID_URL
                                                print("     >> Questão sem ID_URL definida ainda")
                                                
                                            elif id_url_questao:

                                                if self.config['cb_verificar_idurl_site']:
                                                    try:
                                                        print("     >> Verificar se a questão está publicada:", atividade, questao)    
                                                        url = "https://www.modelitos.com.br/atividades/idurl/"+id_url_questao

                                                        r = rq.get(url)

                                                        print(f"        Requisição GET: {r}")

                                                        if r.status_code != 200:
                                                            # Como não localizaou, apaga o registro anterior
                                                            data_questao['ID_URL']=None
                                                            print(f"\n\n >>> [ATENÇÃO]: ID_URL NÃO Localizada: {id_url_questao}\n\n")
                                                        
                                                        else:
                                                            # A questão já está publicada, segue para a questão seguinte
                                                            # O id_url_questao não deve ser nulo e nem estar na lista
                                                            if id_url_questao not in lista_id_url \
                                                                and id_url_questao:
                                                                    lista_id_url.append(id_url_questao)
                                                            
                                                            print(f"         >> ID_URL Questão Localizada no site: {id_url_questao}.")
                                                            print(f"         Lista atual de ids_url: {lista_id_url}\n")

                                                            if not (questao_n == tamanho_data_atividade - 1):
                                                                print("X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X")
                                                                continue
                                                            else:
                                                                pass
                                                    
                                                    except TypeError:
                                                        print("    >>>> Erro de TypeError: ", sigla,curso,disciplina,modulo,atividade,questao)

                                                    except rq.ReadTimeout:
                                                        print("    >>>> Demora na resposta do servidor")

                                                    except Exception as err:
                                                        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                                                        print("Erro1: ",msg)

                                                else:
                                                    # Se já tem o id_url e não é para verificar, então siga para a próxima
                                                    if not (questao_n == tamanho_data_atividade - 1):
                                                        continue
                                                    else:
                                                        #prossiga para verificar o questionário global
                                                        pass
                                            
                                            try:

                                                id_url_questao = self.publicar_questao(
                                                    data = data,
                                                    path_file=path_file,
                                                    headers=headers,
                                                    data_atividade=data_atividade,
                                                    data_questao=data_questao,
                                                    curso_apelido=cursos_apelido[sigla],
                                                    modulo=modulo,
                                                    disciplina=disciplina,
                                                    atividade=atividade,
                                                    questao=questao,
                                                    lista_id_url=lista_id_url
                                                )

                                                if id_url_questao and (id_url_questao not in lista_id_url):
                                                    lista_id_url.append(id_url_questao)

                                                
                                            except InterruptedError as err:
                                                print(err)
                                                log_grava(err=err)
                                                continue

                                        try:
                                            
                                            self.publicar_lista_id_url(
                                                headers,
                                                data_atividade,
                                                atividade,
                                                lista_id_url, id_url,
                                                cursos_apelido[sigla],
                                                modulo,
                                                disciplina
                                            )

                                        except InterruptedError as err:
                                                log_grava(err=err)
                                                print(err)
                                                continue

                                        save_json(data,path_file)
                        save_json(data,path_file)
                        
                    self.updateProgress_postar.emit(1 ,  "["+curso+"] Salvando informações no Banco de Dados:")
                    print(f"Finalizou: {sigla}\n x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x - x ")
        
        except KeyError as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"Falha no login Papiron"
            self.updateProgress_postar.emit(1000 , "[PAPIRON] - Falha no login Papiron")
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
        
    def publicar_questao(self, **kwargs):

        data=kwargs.get('data', None)
        path_file=kwargs.get('path_file', None)
        headers=kwargs.get('headers', None)
        data_atividade=kwargs.get('data_atividade', None)
        data_questao=kwargs.get('data_questao', None)
        curso_apelido=kwargs.get('curso_apelido', None)
        modulo=kwargs.get('modulo', None)
        disciplina=kwargs.get('disciplina', None)
        atividade=kwargs.get('atividade', None)
        questao=kwargs.get('questao', None)
        lista_id_url=kwargs.get('lista_id_url', None)

        print(f"    Iniciando publicação de questao individual: {curso_apelido} - {atividade}")
        try:
            # Verifica se é QUESTIONÁRIO ou DISSERTATIVA
            estilo = data_questao['ESTILO']
            cb_questionario = 'on' if estilo == "QUESTIONARIO" else None
            
            # Verificar se já tem o gabarito
            gabarito = data_questao.get('GABARITO') if cb_questionario else None
            if gabarito:
                data_questao['GABARITO_OK'] = 'OK'

            # Se for atividade de questionário deve pular
            if self.config['cb_discursivas'] and estilo == "QUESTIONARIO":
                print("posta somente discursiva")
                raise InterruptedError
            
            # Cria dados da ATIVIDADE, não fazer referência ao curso, pois existem muitas atividades
            # que são as mesmas para diversos curso diferentes
            enunciado = data_questao['ENUNCIADO']
            titulo = data_questao['TITULO']
            
            # Extrai o texto puro, sem HTML, apenas para impressão
            enunciado_texto = BS(enunciado, 'html.parser').text
            print(f"\n  Postar: ", titulo)
            print(f"\n  >> ATIVIDADE A SER POSTADA:\n {enunciado_texto}\n")

            # Período ativo da Atividade
            dt_inicio_str = data_atividade['DT_INICIO']
            dt_fim_str = data_atividade['DT_FIM']

            alternativa_correta = None
            alternativas = None
            
            if cb_questionario:

                self.imprimir_alternativas(data_questao)

                # Recupera o dict das alternativas, sem o texto das Alternativas i
                alternativas = {"alternativas":data_questao['ALTERNATIVAS']} 

            else:
                print("     Não se trata de atividade de Questionário!")

            atividade_c = {
                "AE1": "ATIVIDADE 1",
                "AE2": "ATIVIDADE 2",
                "AE3": "ATIVIDADE 3",
                "AE4": "ATIVIDADE 4",
                "AE5": "ATIVIDADE 5"
            }.get(atividade, atividade)

            # realiza a postagem da atividades, se ela não tinha id_url anterior
            cont_falha_login=3
            while cont_falha_login:

                try:
                    print(f"     Enviando para o site: {disciplina} - {atividade} - {questao} ")                                                      
                    id_url_enviada = self.postar_atividade( 
                        headers= headers,
                        faculdade= FACULDADE,
                        curso= curso_apelido,
                        disciplina=disciplina,
                        titulo=titulo,
                        enunciado=enunciado,
                        atividade=atividade_c,
                        questao=questao,
                        cb_questionario=cb_questionario,
                        dt_inicio_str=dt_inicio_str, 
                        dt_fim_str=dt_fim_str, 
                        alternativas=alternativas,
                        mod_ano=modulo[:4],
                        mod_ref=modulo[-2:],
                        gabarito=gabarito
                    )

                    # Grava as ID_URL obtidas
                    with open("id_url.txt", "a") as file:
                        file.write(f"{id_url_enviada}\n")

                    break

                except KeyError as err:
                    cont_falha_login -= 1
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"Falha de acesso a Papiron"
                    self.updateProgress_postar.emit(1000 , "[PAPIRON] - Falha: "+cont_falha_login)
                    self.finished.emit()
                    print("   >>> Falha na conexão!")
                    t(120)
            

            if id_url_enviada:

                print("\n     Atribuída ID_URL: ",id_url_enviada,"\n")
                # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ID_URL'] = id_url_enviada
                data_questao['ID_URL'] = id_url_enviada
                
                # Antes de adicionar a lista, verifica se não houve erro em postar duplicado.
                if id_url_enviada and (id_url_enviada not in lista_id_url):
                    lista_id_url.append(id_url_enviada)
                    print(f"    >> Lista de ID_URLs atual: {lista_id_url} \n\n")

                save_json(data, path_file)
            
            else:

                print("\n\n    Não foi possível atribuir id_url : ",titulo,"\n\n")
            
            print(f"\n  X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X\n\n\n")

            id_url_enviada = None
        
        except KeyError as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg)
            raise InterruptedError
        
    def publicar_lista_id_url(
            self,
            headers,
            data_atividade,
            atividade,
            lista_id_url, id_url,
            curso_apelido,
            modulo,
            disciplina
        ):
    
        # Verifica o tamanho a lista de ID_URLs gerados, se for maior que 1,
        # significa que é questionário
        if len(lista_id_url)>1:

            # Verifica se a lista de id_url gerada é diferente da gravada, se for diferente refaz.
            if data_atividade.get('LISTA_ID_URL')!= lista_id_url:
                data_atividade['ID_URL'] = None
                if 'LISTA_ID_URL' in data_atividade:
                    data_atividade['LISTA_ID_URL'] = None
                else:
                    data_atividade['LISTA_ID_URL'] = lista_id_url

            # Testa para verificar se a id_url da atividade consolidada está íntegra no servidor:
            if data_atividade['ID_URL']:
                print("     lista", data_atividade['ID_URL'])
                data_atividade['ID_URL']= self.teste_lista_id_url(data_atividade)

            # Não tem ID Consolidada ou está corrompida pela falta de id publicados
            if not data_atividade['ID_URL']:
                self.publicar_questionario(
                    headers,
                    curso_apelido,
                    modulo,
                    disciplina,
                    atividade,
                    data_atividade,
                    lista_id_url
                )


            with open("id_url.txt", "a") as file:
                file.write(f"Lista geral: {lista_id_url}\n")
                    
            # Consolida as atividades
        else:
            # id_url da questão ficará igual ao pai (No caso a atividade)
            # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade]['ID_URL'] = id_url
            data_atividade['ID_URL'] = id_url

    def publicar_questionario(
            self,
            headers,
            sigla,
            modulo,
            disciplina,
            atividade,
            data_atividade,
            lista_id_url
            ):
        
        # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade]['LISTA_ID_URL'] = lista_id_url    
        data_atividade['LISTA_ID_URL']=lista_id_url                                                
        dt_inicio_str=data_atividade['DT_INICIO']
        dt_fim_str=data_atividade['DT_FIM']

        cont_falha_login=3
        while cont_falha_login and lista_id_url:
            try:
                atividade_c = {
                    "AE1": "ATIVIDADE 1",
                    "AE2": "ATIVIDADE 2",
                    "AE3": "ATIVIDADE 3",
                    "AE4": "ATIVIDADE 4",
                    "AE5": "ATIVIDADE 5"
                }.get(atividade, atividade)

                print("   Postar todas as id_urls agrupadas:\n    >> ", lista_id_url)

                titulo_quest = "QUESTIONÁRIO - "+disciplina+" - "+atividade+" - "+modulo
                
                id_url_atividade = self.postar_questionario(
                    ids_url=lista_id_url,
                    headers=headers,
                    faculdade=FACULDADE,
                    curso=sigla,
                    disciplina=disciplina,
                    atividade=atividade_c,
                    questao = "QUESTIONÁRIO",
                    titulo = titulo_quest,
                    dt_inicio_str=dt_inicio_str,
                    dt_fim_str=dt_fim_str,
                    mod_ano=modulo[:4],
                    mod_ref=modulo[-2:],
                )

                data_atividade['ID_URL'] = id_url_atividade
                
                print(f"\n  X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X\n\n\n")
                break

            except KeyError as err:
                cont_falha_login -= 1
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"Falha no login Papiron"
                # self.updateProgress_postar.emit(1000 , "[PAPIRON] - Falha no login Papiron - "+ str(cont_falha_login))
                # self.finished.emit()
                print(f"ERRO: {msg} : {cont_falha_login}")
                t(20)

    def postar_atividade(
                self,
                headers:dict,
                faculdade:str,
                curso:str,
                disciplina:str,
                titulo: str,
                enunciado:str,
                atividade:str,
                questao:str,
                cb_questionario:str,
                dt_inicio_str:str, 
                dt_fim_str:str,
                alternativas:dict,
                mod_ano:str,
                mod_ref:str,
                gabarito:str,
            )->str:

        cont = 5
        while cont:
            try:
                url = "https://www.papiron.com.br/atividades/form/pergunta_automatica"
                r = rq.get(url, headers=headers , allow_redirects=False)
                soup = BS(r.content, "html.parser")
                csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})['value']
                fields = {
                    'csrfmiddlewaretoken': csrfmiddlewaretoken,
                    'conteudo':'new',
                    'faculdade':faculdade,
                    'curso':curso,
                    'disciplina':disciplina,
                    'titulo':titulo,
                    'pergunta':enunciado,
                    'atividade':atividade,
                    'questao':questao,
                    'dt_inicio': dt_inicio_str, 
                    'dt_fim': dt_fim_str,
                    'alternativas': json.dumps(alternativas),
                    'mod_ano':mod_ano,
                    'mod_ref':mod_ref,
                    'gabarito':gabarito
                }

                if cb_questionario:
                    fields['estilo'] = 'on'
                
                
                boundary = '----WebKitFormBoundary' \
                        + ''.join(random.sample(string.ascii_letters + string.digits, 16))
                m = MultipartEncoder(fields=fields, boundary=boundary)

                headers_b={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",   
                    "Cookie": headers['Cookie'],
                    "Content-Length":str(len(str(m))),
                    "Host": "www.papiron.com.br",
                    "Origin": "https://www.papiron.com.br",
                    "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica",
                    "Content-Type": m.content_type,
                    "Upgrade-Insecure-Requests": "1"
                }            
                r = rq.post(url,headers=headers_b, data = m , allow_redirects=False,timeout=180)

                id_url = r.headers['Location'].split("/").__getitem__(2)

                return id_url

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"  >> Falha em enviar a atividade: "+str(cont)
                print(msg)
                cont-=1
                if not cont: 
                    return None
                
    def postar_questionario(
                self,
                ids_url: list,
                headers:dict,
                faculdade:str,
                curso:str,
                disciplina:str,
                atividade:str,
                questao:str,
                titulo:str,
                dt_inicio_str:str, 
                dt_fim_str:str,
                mod_ano:str,
                mod_ref:str,
            )->str:

        url = "https://www.papiron.com.br/atividades/form/pergunta_automatica_quest"

        cont = 5
        try:
            while cont:
                r_entrando = rq.get(url, headers=headers, allow_redirects=False)
                soup = BS(r_entrando.content, "html.parser")
                csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})['value']
                print("titulo:", titulo)
                fields = {
                    'csrfmiddlewaretoken': csrfmiddlewaretoken,
                    # 'ids_url': str(ids_url),
                    'ids_url':json.dumps(ids_url),
                    'faculdade':faculdade,
                    'curso':curso,
                    'disciplina':disciplina,
                    'atividade':atividade,
                    'questao':questao,
                    'titulo':titulo,
                    'estilo':'on',
                    'dt_inicio': dt_inicio_str, 
                    'dt_fim': dt_fim_str,
                    'mod_ano':mod_ano,
                    'mod_ref':mod_ref,
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
                    "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica_quest",
                    "Content-Type": m.content_type,
                    "Upgrade-Insecure-Requests": "1"
                } 
                
                r_postanto = rq.post(url, headers=headers_b , data = m , allow_redirects=False,timeout=120)

                print("R Postando:", r_postanto)

                id_url = r_postanto.headers['Location'].split("/").__getitem__(2)

                print(f"Questionário Completo: {id_url}")

                return id_url
            
        except (ConnectTimeout,ConnectionError) as err:
            cont-=1
            t(20)
            if cont==0:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"  >> Falha em enviar o questionário COMPLETO:"
                print(msg)
                return None

    def teste_lista_id_url(
            self,
            data_atividade
        ):

        
            id_url_atividade = data_atividade['ID_URL']

            try:

                print("     >> Verificar se a questão agrupada está íntegra:", id_url_atividade)  

                url = "https://www.modelitos.com.br/atividades/idurl/"+id_url_atividade

                r = rq.get(url)

                print(f"        Requisição GET {id_url_atividade}: {r}")

                if r.status_code != 200:
                    data_atividade['ID_URL']=None
                    print(f"\n\n >>> [ATENÇÃO]: ID_URL NÃO Localizada: {id_url_atividade}\n\n")
                    return None
                
                else:
                    # A questão já está publicada e íntegra, segue para a questão seguinte
                    # O id_url não deve ser nulo e nem estar na lista
                    print(f"        > ID_URL CONSOLIDADA Localizada {id_url_atividade}\n\n")
                    print(" X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X - X")
                    return id_url_atividade


            except TypeError:
                print("    >>>> Erro de TypeError: ") #, sigla,curso,disciplina,modulo,atividade,questao)

            except rq.ReadTimeout:
                print("    >>>> Demora na resposta do servidor")

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print("Erro1: ",msg)

            return None
    
    def imprimir_alternativas(self, data_questao):

        # Em caso de atividades estilo questionário, formatar as alternativas 
        if data_questao.get('ALTERNATIVAS'):

            alternativa_correta = data_questao.get('GABARITO')

            # Imprime as alternativas na tela
            alternativas_sujas = dict(data_questao['ALTERNATIVAS'])
            for i, alternativa in enumerate(alternativas_sujas):
                # Retira o texto Alternativa i do corpo da própria alternativa
                alternativa_i = "Alternativa "+str(i+1)+": "
                alternativa_formt = alternativas_sujas[alternativa].replace(alternativa_i,"")
                data_questao['ALTERNATIVAS'][str(i)] = alternativa_formt
                if alternativa:
                    print(f"\n    Alternativa {i} -{alternativa_formt}")
        
            # Imprime Gabarito na tela
            print("\n    >>> ALTERNATIVA CORRETA: ",alternativa_correta)
        
        else:
            msg =f"\nQuestão questionário sem ALTERNATIVAS: {data_questao.get('ID_URL')} = {data_questao}\n"
            log_grava(msg=msg)


    def verificar_lista_id_urls(self,id_url,lista):
        # URL do endpoint (ajuste conforme necessário)
        url = "http://www.papiron.com.br/atividades/robots/verifica_automatica_quest/" + id_url

        try:
            response = rq.get(url, timeout=10)
            response.raise_for_status()  # Lança erro se status != 200

            lista_ids = response.json()  # ✅ Converte a resposta para list Python
            print("       >>>> IDs recebidos:", lista_ids)

            lista_original = list(lista)

            lista_original.sort()

            if lista_original == lista_ids:
                return True

        except rq.exceptions.HTTPError as errh:
            print("Erro HTTP:", errh)
        except rq.exceptions.ConnectionError as errc:
            print("Erro de Conexão:", errc)
        except rq.exceptions.Timeout as errt:
            print("Timeout:", errt)
        except rq.exceptions.RequestException as err:
            print("Erro:", err)
        
        return False

