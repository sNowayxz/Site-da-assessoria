from function import scrapped_id_resposta, tratar_resposta
import json
import os
import random
import string
import time
import traceback

import requests as rq
from bs4 import BeautifulSoup as BS
from requests.exceptions import ConnectionError, ProxyError, ReadTimeout
from requests_toolbelt import MultipartEncoder

from system.system import t
from function_bd import abre_json, integridade_bd, save_json
from system.chrome import login_papiron
from system.crypto import recodification, recupera_dados
from dict_lista_curso import dict_curso_sigla_nome

keys_exclusao =  ["STATUS_ATIVIDADE","ID_URL","DT_INICIO", "DT_FIM","LISTA_ID_URL"]

def comentar(self):

    url_base ="https://www.papiron.com.br"

    cursos_sigla = dict_curso_sigla_nome()

    modulo = self.modulo.replace("/","")

    path_user = os.getcwd()+'\\BD\\atividades\\user_data.json'
    
    # Obtém dados do usuário a logar
    user = abre_json(path_file= path_user)
    usuario=recodification(user["usuario"])
    password=recodification(user["password"])
    print(usuario,password)
    headers=login_papiron(
        user=usuario,
        password=password,
        url_base=url_base
    )

    try:
        
        for sigla in cursos_sigla:

            data , path_file = integridade_bd(sigla,modulo)

            data_temp = data

            if data:

                for curso in data:

                    for disciplina in data[curso]:

                        for modulo in data[curso][disciplina]:

                            for atividade in data[curso][disciplina][modulo]['ATIVIDADE']:

                                if atividade not in keys_exclusao:

                                    for questao in data[curso][disciplina][modulo]['ATIVIDADE'][atividade]:

                                        if questao not in keys_exclusao:

                                            # Comentar apenas as dissertativas
                                            if data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ESTILO'] == "DISSERTATIVA":
                                                
                                                print(f"\n\n   ==>> Iniciando nova chatGPT.\n      {curso} - {disciplina} - {atividade} - {questao}")


                                                if "ID_URL" in data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]:
                                                    id_url = data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ID_URL']
                                                    print(f"            ID_URL: {id_url} - {modulo}")

                                                    # Se não tiver id_url, para execução e vai para o próximo
                                                    if not id_url:
                                                        print(f"\n\n   ==>> Atividade sem id_url capturada.\n           {atividade} - {questao}\n           Passou para o próximo.")
                                                        continue

                                                else:
                                                    print(f"\n\n   ==>> REGISTRO COM FALHA") 
                                                    continue
                                                

                                                # Verifica se a atividade não foi apagada no site
                                                url_verifica = url_base+"/atividades/unicesumar/"+id_url
                                                r_verifica = rq.get(url_verifica,headers=headers)
                                                print(f"r_verfiicaa: {r_verifica}")
                                                t(10)
                                                if r_verifica.status_code == 404:
                                                    print(f"    => Parece que o id_url {id_url} foi apagado: {url_verifica} ")
                                                    # Apagar o registro no BD
                                                    # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ID_URL']=None
                                                    # save_json(data_temp,path_file)
                                                    continue

                                                # Verifica se tem gabarito:
                                                # try:                                                                    
                                                #     url_gabarito = url_base+"/atividades/gabarito/"+id_url
                                                #     r_gab = rq.get(url_gabarito,headers=headers)
                                                #     print(f"            GABARITO: {r_gab} ")
                                                # except TypeError:
                                                #     # Caso não haja id_url gerado pela envio da atividade
                                                #     print(f"            Não há ID_URL gerado")
                                                #     continue
                                                # if r_gab.status_code == 200:
                                                #     print(f"          >> Passou para a próximo, pois já tem gabarito")
                                                #     continue


                                                html = data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ENUNCIADO']
                                                soup = BS(html, 'html.parser')
                                                    
                                                # enunciado = soup.text[:800]                                                
                                                # id , verified , resposta = scrapped_id_resposta(enunciado)

                                                    # print("1")

                                                # if not id:
                                                #     # Não encontrou nada no Brainly, passa para a próxima
                                                #     # print("2.1")
                                                #     time.sleep(5)
                                                #     continue

                                                # Salva a resposta encontrada no BD
                                                # resposta = tratar_resposta(resposta)
                                                # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY'] = {}
                                                # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['ID'] = id
                                                # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['VERIFIED'] = verified
                                                # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['RESPOSTA'] = resposta
                                                    
                                                #     print(f"\n\n  >>  {str(verified).upper()} - {data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ID_URL']} \n {resposta} ")

                                                #     print("3")

                                                #     save_json(data_temp,path_file)
                                                
                                                # elif brainly_somente_novas:
                                                #     print("      >> Já existe um comentário e não é para revisar.")
                                                #     continue
                                                
                                                # elif data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['VERIFIED'] == False:
                                                # # Se o comentário do Brainly não foi verificado, refaz vendo se encontra um comentário verificado

                                                #     print("      >>  Comentário não verificado.")
                                                    
                                                #     html = data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ENUNCIADO']
                                                #     soup = BS(html, 'html.parser')
                                                #     enunciado = soup.text[:800]

                                                #     alternativas = ""
                                                #     if 'ALTERNATIVAS' in data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]:
                                                #         lista_alternativas = data[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ALTERNATIVAS']
                                                #         alternativas = lista_alternativas['0']+ " "+lista_alternativas['1']

                                                #     # print("a")
                                                #     id , verified , resposta = scrapped_id_resposta(enunciado+alternativas)
                                                #     # print("a1")

                                                #     if not id:
                                                #         # Não encontrou nada no Brainly, passa para a próxima
                                                #         time.sleep(7)
                                                #         continue

                                                #     resposta = tratar_resposta(resposta)

                                                #     print("            Mudou de ID Brainly?", data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['ID'] != id , id, data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['ID'])
                                                    
                                                #     if verified or data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['ID'] != id:

                                                #         data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY'] = {}
                                                #         data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['ID'] = id
                                                #         data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['VERIFIED'] = verified
                                                #         data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['RESPOSTA'] = resposta
                                                        
                                                #         print(f"\n\n  >> Renovou a resposta - {str(verified).upper()} \n {resposta}")

                                                #         nova_resposta = True

                                                #         save_json(data_temp,path_file)
                                                
                                                
                                                if not data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]["ID_URL"]:  
                                                # Como a atividade não foi postada ou não tem dados da publicação, pula para seguinte.      
                                                    print("Não foi postada! próximo" , data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]["ID_URL"])
                                                    time.sleep(1)
                                                    print("4")
                                                    continue
                                                
                                                try:
                                                    id_url = data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]["ID_URL"]
                                                    url_com = "https://www.papiron.com.br/atividades/comentario/"+id_url
                                                    url_atv = "https://www.papiron.com.br/atividades/"+id_url

                                                    r = rq.get(url_com, headers = headers, timeout=120)
                                                    
                                                    print("\n     r_com:", r, url_atv, "\n                           :" ,url_com)

                                                    if r.status_code == 404:

                                                        resposta = "teste feito"

                                                        # Prepara para entrar o papiron
                                                        url = "https://www.papiron.com.br/atividades/"+id_url
                                                        r = rq.get(url = url,  headers = headers , allow_redirects=False, timeout=120)
                                                        soup = BS(r.content, "html.parser")

                                                        # Obtem o CSRF do botão correto de "COMENTAR"
                                                        form = soup.find("form",{"id":id_url})
                                                        csrfmiddlewaretoken = form.find("input",{"name":"csrfmiddlewaretoken"})['value'] if form else soup.find("input",{"name":"csrfmiddlewaretoken"})['value']
                                                        
                                                        fields = {
                                                            'csrfmiddlewaretoken': csrfmiddlewaretoken,
                                                            'comentario':resposta,
                                                            'id_url':id_url,
                                                            'conteudo':"new",
                                                            'verificada': str(True) ,
                                                            'robot':"True"
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
                                                            "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica",
                                                            "Content-Type": m.content_type,
                                                            "Upgrade-Insecure-Requests": "1"
                                                        }     

                                                        url_comentar = "https://www.papiron.com.br/atividades/form/comentar"       
                                                        r = rq.post(url_comentar,headers=headers_b, data = m , allow_redirects=False,timeout=120)

                                                        print("Chegou aquiii", id_url)

                                                        print(x)

                                                        x=1

                                                        
                                                    # elif r.status_code == 200:

                                                    #     if nova_resposta:

                                                    #         # Apagar o comentário atual

                                                    #         print("   >> Apagando comentário anterior!")

                                                    #         url = "https://www.papiron.com.br/atividades/"+id_url
                                                    #         # r_302 = rq.get(url = url,  headers = headers , allow_redirects=False,timeout=120)
                                                    #         # location = r_302.headers['Location'].split("/").__getitem__(2)

                                                    #         # Para continuar autenticado, é necessário enviar os cookies através dos
                                                    #         # redirecionamentos, se pular para o 200, perde os dados de sessão.
                                                    #         # url_302 = "https://www.papiron.com.br/atividades/"+location
                                                    #         # r = rq.get(url = url_302,  headers = headers , allow_redirects=False,timeout=120)
                                                    #         r = rq.get(url = url,  headers = headers , allow_redirects=False,timeout=120)
                                                    #         soup = BS(r.content, "html.parser")

                                                    #         # Obtem o CSRF do botão correto de "COMENTAR"
                                                    #         form = soup.find("form",{"id":id_url})
                                                    #         csrfmiddlewaretoken = form.find("input",{"name":"csrfmiddlewaretoken"})['value'] if form else soup.find("input",{"name":"csrfmiddlewaretoken"})['value']

                                                    #         fields = {
                                                    #             'csrfmiddlewaretoken': csrfmiddlewaretoken,
                                                    #             'comentario':"",
                                                    #             'id_url':id_url,
                                                    #             'conteudo':"delete",
                                                    #         }

                                                    #         boundary = '----WebKitFormBoundary' \
                                                    #                 + ''.join(random.sample(string.ascii_letters + string.digits, 16))
                                                    #         m = MultipartEncoder(fields=fields, boundary=boundary)

                                                    #         headers_b={
                                                    #             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",   
                                                    #             "Cookie": headers['Cookie'],
                                                    #             "Content-Length":str(len(str(m))),
                                                    #             "Host": "www.papiron.com.br",
                                                    #             "Origin": "https://www.papiron.com.br",
                                                    #             "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica",
                                                    #             "Content-Type": m.content_type,
                                                    #             "Upgrade-Insecure-Requests": "1"
                                                    #         }     

                                                    #         url_comentar = "https://www.papiron.com.br/atividades/form/comentar"       
                                                    #         r = rq.post(url_comentar,headers=headers_b, data = m , allow_redirects=False,timeout=120)

                                                    #         print("     >> Comentário apagado!")

                                                    #         # Renovar comentário

                                                    #         verified = data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['VERIFIED']
                                                    #         resposta = data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['RESPOSTA']

                                                    #         url = "https://www.papiron.com.br/atividades/"+id_url
                                                    #         # r_302 = rq.get(url = url,  headers = headers , allow_redirects=False,timeout=120)
                                                    #         # location = r_302.headers['Location'].split("/").__getitem__(2)

                                                    #         print("   >> Inserindo comentário atualizado!")

                                                    #         # Para continuar autenticado, é necessário enviar os cookies através dos
                                                    #         # redirecionamentos, se pular para o 200, perde os dados de sessão.
                                                    #         # url_302 = "https://www.papiron.com.br/atividades/"+location
                                                    #         # r = rq.get(url = url_302,  headers = headers , allow_redirects=False,timeout=120)
                                                    #         r = rq.get(url = url,  headers = headers , allow_redirects=False,timeout=120)
                                                    #         soup = BS(r.content, "html.parser")


                                                    #         # Obtem o CSRF do botão correto de "COMENTAR"
                                                    #         form = soup.find("form",{"id":id_url})

                                                            
                                                    #         verified = data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['VERIFIED']
                                                    #         resposta = data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['BRAINLY']['RESPOSTA']


                                                    #         # Obtem o CSRF do botão correto de "COMENTAR"
                                                    #         form = soup.find("form",{"id":id_url})
                                                    #         csrfmiddlewaretoken = form.find("input",{"name":"csrfmiddlewaretoken"})['value'] if form else soup.find("input",{"name":"csrfmiddlewaretoken"})['value']

                                                    #         fields = {
                                                    #             'csrfmiddlewaretoken': csrfmiddlewaretoken,
                                                    #             'comentario':resposta,
                                                    #             'id_url':id_url,
                                                    #             'conteudo':"new",
                                                    #             'verificada': str(verified) ,
                                                    #             'robot':"True"
                                                    #         }

                                                    #         boundary = '----WebKitFormBoundary' \
                                                    #                 + ''.join(random.sample(string.ascii_letters + string.digits, 16))
                                                    #         m = MultipartEncoder(fields=fields, boundary=boundary)

                                                    #         headers_b={
                                                    #             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",   
                                                    #             "Cookie": headers['Cookie'],
                                                    #             "Content-Length":str(len(str(m))),
                                                    #             "Host": "www.papiron.com.br",
                                                    #             "Origin": "https://www.papiron.com.br",
                                                    #             "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica",
                                                    #             "Content-Type": m.content_type,
                                                    #             "Upgrade-Insecure-Requests": "1"
                                                    #         }     

                                                    #         url_comentar = "https://www.papiron.com.br/atividades/form/comentar"       
                                                    #         r = rq.post(url_comentar,headers=headers_b, data = m , allow_redirects=False,timeout=120)

                                                    #         print("     >> Comentario atualizado com sucesso!")
                                                    #     else:

                                                    #         time.sleep(2)
                                                    #         continue

                                                except (ConnectionError, ReadTimeout ,KeyError)as err:
                                                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                                                    print("Erro: ",msg)
                                                    print("Erro de conexão com Papiron!\n")
                                                
                                                except Exception as err:
                                                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                                                    print("Erro: ",msg)

                                                time.sleep(10)
                                                print("próximo")

    except ProxyError as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print("Erro: ",msg)

    except Exception as err:
        import traceback
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print("Erro: ",msg)
        time.sleep(30)
