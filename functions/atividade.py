
import json
import math
import os
import shutil
import traceback
from copy import deepcopy
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup as BS
from function import salvar_drive
from function_bd import abre_json, save_json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from system.bd import deep_merge
from system.chrome import atualizar_soup, ult_div
from system.hash import hash_quest, hash_text
from system.logger import log_grava
from system.pastas import definir_sufixo_legado, escapa_path, verifica_pastas
from system.system import t

from functions.curso import dict_curso
from functions.escape import escape_html


def extrair_dados_basicos(driver):
    # Extrai informações do enunciado!
    ult_div(driver)
    soup = atualizar_soup(driver)
    css_enunciado = "#cabecalhoQuestao > div.panel-body.p-t-20.b-t.b-grey > div.enunciado.ng-binding"                
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR,css_enunciado)))

    enunciado = soup.find('div', class_="enunciado ng-binding") # enunciado tem que ser com tag para extrair o hash

    if not enunciado.text:
        # Se não tem enunciado, atividade não liberada ainda
        return enunciado, None, None, [], None, None

    titulo_div = soup.find('div', {"ng-bind": "vm.questionario.descricao"})
    
    titulo = titulo_div.text if titulo_div else None

    # Listas as alternativas se a questão for do tipo QUESTIONÁRIO
    lista_alternativas_div = soup.find_all('div',{"class":"inline-block m-t-10 ng-binding", "ng-bind-html":"alternativa.descricao  | mathJaxFix"})

    # Verifica se é ou não questionário
    alternativas = listar_alternativas(driver, lista_alternativas_div)
    questionario = True  if lista_alternativas_div else False

    texto_completo=escape_html(enunciado)
    if questionario:
        for alternativa in alternativas:
            # Adiciona o conteúdo da alternativa no enunciado, já "escapada"
            texto_completo = texto_completo+alternativa
        questao_n=hash_quest(texto_completo)
    else:
        questao_n= hash_text(texto_completo)
    
    return  enunciado, titulo, questao_n, lista_alternativas_div, alternativas, questionario

def alocar_chaves(chave_data, hash_questao, questionario,dt_inicio_atividade,dt_fim_atividade):

    # Insere as informações de prazo limite no BD
    chave_data['DT_INICIO'] = dt_inicio_atividade.strftime('%Y-%m-%d')
    chave_data['DT_FIM'] = dt_fim_atividade.strftime('%Y-%m-%d')

    # Verifica se a questão já não está gravada (para não apagar os dados já coletados anteriormente)
    if hash_questao not in chave_data:

        chave_data['STATUS_ATIVIDADE'] = "ABERTA"

        # Aloca o espaço para receber as Questões da Atividade
        chave_data[hash_questao]={}

        # Insere a key [ID_URL]
        chave_data[hash_questao]['ID_URL'] = None

        if questionario:
            chave_data[hash_questao]['ESTILO']="QUESTIONARIO"
            chave_data[hash_questao]['ALTERNATIVAS'] = {}

def extrair_enunciado(driver, soup):

    soup = atualizar_soup(driver)
    enunciado =  soup.find('div',{"class":"enunciado ng-binding"})
    return enunciado

def definir_data_atividades(self, driver, questionario):
    
    # Data de hoje, pode ser inserida uma antecipação ou atraso no dia, para ajustar a atividade ativa
    hoje = datetime.now().date() + timedelta(days=self.config['deslocar_dias']) # para deslocar a data de varredura

    soup = atualizar_soup(driver)   
    dt_inicio_atividade =   datetime.strptime(soup.find("span",{"ng-bind":"vm.questionario.dataInicial | serverDate:'dd/MM/yyyy HH:mm'"}).text[:10],'%d/%m/%Y')
    dt_fim_atividade    =   datetime.strptime(soup.find("span",{"ng-bind":"vm.questionario.dataFinal | serverDate:'dd/MM/yyyy HH:mm'"}).text[:10],'%d/%m/%Y')
    try:
        dt_gabarito=datetime.strptime(soup.find("span",{"ng-bind":"vm.questionario.dataGabarito | serverDate:'dd/MM/yyyy'"}).text[:10],'%d/%m/%Y').date()
    except Exception as err:
        import traceback
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", err)
        dt_gabarito="Não disponível"

    return hoje, dt_inicio_atividade.date(), dt_fim_atividade.date(), dt_gabarito 

def gabarito_atividade(
        aluno,
        curso,
        disciplina,
        soup,
        enunciado,
        atividade,
        questao_n,
        lista_alternativas,
    ):
    
    # Extrai o gabarito, se houver
    try:
        # Primeira tentativa de buscar é caso tenha o gabarito dentro da atividade.
        # Caso não encontre alternativa correta!
        alternativa_correta = None
        gabarito_site = None

        # Se o Aluno errou é assim
        try:
            alternativa_correta = soup.find("label",{"class":"cursor padding-5 block b-grey b-a m-b-15 ng-scope resposta-gabarito"}).find("p").decode_contents()
            print("        > Possui Gabarito , aluno errou", alternativa_correta)
            return escape_html(alternativa_correta), gabarito_site
        except AttributeError:
            alternativa_correta = soup.find("label",{"class":"cursor padding-5 block b-grey b-a m-b-15 ng-scope resposta-gabarito"})\
                .find('div',{"class":"inline-block m-t-10 ng-binding", "ng-bind-html":"alternativa.descricao  | mathJaxFix"})\
                .decode_contents() 
            print("        > Possui Gabarito sem P, aluno errou", alternativa_correta)
            return escape_html(alternativa_correta), gabarito_site
    
    except AttributeError:    
        
        try:

            # Se o aluno acertou fica assim:
            try:
                alternativa_correta = soup.find("label",{"class":"cursor padding-5 block b-grey b-a m-b-15 ng-scope resposta-gabarito resposta-correta"}).find("p").decode_contents()
                print("        > Possui Gabarito, aluno acertou", alternativa_correta)
                return escape_html(alternativa_correta), gabarito_site
            except AttributeError:

                alternativa_correta = soup.find("label",{"class":"cursor padding-5 block b-grey b-a m-b-15 ng-scope resposta-gabarito resposta-correta"})\
                    .find('div',{"class":"inline-block m-t-10 ng-binding", "ng-bind-html":"alternativa.descricao  | mathJaxFix"})\
                    .decode_contents()
                print("        > Possui Gabarito sem P, aluno acertou", alternativa_correta)
                return escape_html(alternativa_correta), gabarito_site

        except AttributeError:
            
            # Como ainda o gabarito não foi liberado
            # Vai procurar se tem gabarito no site
            try:
                gabarito_site = procurar_gabarito_site(
                    enunciado= escape_html(enunciado), 
                    lista_alternativas=lista_alternativas,
                    soup=soup,
                    disciplina=disciplina
                )
            except Exception as err:
                log_grava(
                    err=err,
                    msg= "INVESTIGAR Gab: "+curso[aluno.curso]+" - "+disciplina.modulo+" - "+disciplina.disciplina+" - "+atividade+" - "+questao_n+" - "+enunciado.text[:20]
                )
            
            if gabarito_site:
                print("        > Gabarito localizado no site", gabarito_site)
            else:
                alternativa_correta = None
                print("        > Sem Gabarito algum")
        

    except Exception as err:
        
        log_grava(
            err=err,
            msg= curso[aluno.curso]+" - "+disciplina.modulo+" - "+disciplina.disciplina+" - "+atividade+" - "+questao_n
        )

        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)

    return alternativa_correta, gabarito_site

def procurar_gabarito_site(**kwargs):
    import requests as rq
    from requests.exceptions import (
        ConnectTimeout,
        ReadTimeout,
        RequestException,
        Timeout,
    )

    enunciado = kwargs.get('enunciado', None)
    lista_alternativas = kwargs.get('lista_alternativas', None)
    soup = kwargs.get('soup', None)
    disciplina = kwargs.get('disciplina', None)

    url_base ="https://www.papiron.com.br"

    # Formatar Lista de Alternativas, ela vem com html
    lista_formatada = []
    for alternativa in lista_alternativas:
        try:
            lista_formatada.append(alternativa.find('p').decode_contents())
        
        except AttributeError:
            lista_formatada.append(alternativa.decode_contents())   

    if lista_formatada:
        enunciado_completo = enunciado
        for alternativa in lista_formatada:
            enunciado_completo = enunciado_completo+alternativa
        hash_enunciado = hash_quest(enunciado_completo)
    
    else:
        return None
    
    # print("ENUNCIADO0","  |||",enunciado,"||| ")
    # print("ENUNCIADO1","  |||",enunciado_completo,"||| ")
    # print("ENUNCIADO2","  |||",lista_formatada,"||| ")
    # print("ENUNCIADO3","  |||",hash_enunciado,"||| ")

    url_hash = url_base+"/atividades/gabarito_hash/"+hash_enunciado
    cont = 4
    while cont:
        try:
            
            r = rq.get(url_hash, allow_redirects=False,timeout=100)

            if r.status_code != 200:
                print("      >> Não tem enunciado igual no site")
                return None
            
            else:
                print("      >> Localizou enunciado idêntico com questionários idênticos")

                data_enunciados = r.json()

                gabarito = data_enunciados['0']['gabarito']

                print("\n           ", 
                        list(data_enunciados['0']['alternativas'].values()) == lista_formatada,
                        "\n       >> "+str(list(data_enunciados['0']['alternativas'].values()))+"\n      >> "+str(lista_formatada))
                
                return gabarito
            

        except KeyError as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            log_grava(msg=msg+enunciado[:150]+"=======================\n\n"+str(data_enunciados)+"=============================\n\n")  
            cont-=1
            if not cont:
                return None
        
        except ConnectTimeout:
            t(90)
            print("Erro: conexão com o servidor expirou (ConnectTimeout).")

        except ReadTimeout:
            print("Erro: o servidor demorou muito para responder (ReadTimeout).")

        except Timeout:
            t(60)
            print("Erro: tempo limite de requisição excedido.")

        except rq.exceptions.HTTPError as errh:
            print(f"Erro HTTP: {errh.response.status_code} - {errh.response.reason}")

        except rq.exceptions.ConnectionError:
            t(90)
            print("Erro: falha na conexão. Verifique sua internet ou o domínio.")

        except RequestException as err:
            print(f"Erro inesperado ao fazer requisição: {err}")
        
        except Exception as err:
            log_grava(
                err=err,
                msg= "INVESTIGAR: "+disciplina.modulo+" - "+disciplina.disciplina+"\n"+enunciado
            )
                                
        cont-=1
        if not cont:
            return None

def listar_alternativas(driver, lista_alternativas_div):

    alternativas = []
    for m, alternativa in enumerate(lista_alternativas_div):
                        
        try:
            # Grande parte das alternativas são obtidas atravês deste formato da tag <P>
            alternativa_formatada = alternativa.find("p").decode_contents()
        except AttributeError:
            t(k=2)
            soup = atualizar_soup(driver=driver)
            try:
                lista_alternativas_secundaria = soup.find_all('div',{"class":"inline-block m-t-10 ng-binding", "ng-bind-html":"alternativa.descricao  | mathJaxFix"})
                alternativa_formatada = lista_alternativas_secundaria[m].decode_contents()
            except AttributeError:
                try:
                    # Verifica se o parágrafo do enunciado não tem <p> e pega somente o texto.
                    alternativa_sem_p = BS(str(lista_alternativas_secundaria[m]), 'html.parser')
                    alternativa_formatada = alternativa_sem_p.decode_contents()

                except AttributeError:
                    alternativa_formatada = "<B>ATENÇÃO: </B>NÃO FOI POSSÍVEL REALIZA A LEITURA DA ALTERNATIVA."

        # Adiciona a alternativa na list
        alternativas.append(escape_html(alternativa_formatada))

    return alternativas

def definir_propriedades_atividade(
        soup,
        chave_data,
        chave_modulo,
        hash_questao,
        verifica_questao_anulada,
        alternativa_correta,
        dt_gabarito,
        hoje
        ):

    status_atividade = soup.find("span",{"ng-show":"vm.questionario.notaAluno == null || vm.questionario.notaAluno == undefined"}).text
    
    finalizada_atividade = soup.find("p",{"class":"ng-binding","ng-bind":"vm.questionario.situacao.descricao"}).text
    
    if finalizada_atividade == "ENCERRADO":
        
        # Atividade geral está fechada
        chave_data['STATUS_ATIVIDADE']=="FECHADA"
        
        if verifica_questao_anulada: # se tem alguma informação, significa QUESTÃO ANULADA
            chave_data[hash_questao]['STATUS_QUESTAO'] = "FECHADA"
            
        elif status_atividade == 'Não avaliado, aguarde a correção.':
            # Se for dissertativa ou se a data de gabarito for menor que a data de hoje, pode Fechar a atividade
            if dt_gabarito=="Não disponível" or dt_gabarito<hoje:
                chave_modulo = "FECHADO"
                chave_data[hash_questao]['STATUS_QUESTAO'] = "FECHADO"
            else:
                chave_modulo = "ABERTA" 
                chave_data[hash_questao]['STATUS_QUESTAO'] = "ABERTA"
            

        elif alternativa_correta:
            # Gabarito e notas liberados
            chave_data[hash_questao]['STATUS_QUESTAO'] = "FECHADA"
            
        else:
            print("  ATENÇÃO SITUAÇÃO DESCONHECIDA")
            
    else:
        # Atividade ainda não encerrada
        chave_data[hash_questao]['STATUS_QUESTAO'] = "ABERTA"

def salvar_dados_questionario(chave_data, hash_questao, enunciado, titulo, alternativas, alternativa_correta, gabarito_site):
    
    # Grava dados no banco de dados
    chave_data[hash_questao]['ENUNCIADO']=escape_html(enunciado)
    chave_data[hash_questao]['TITULO'] = titulo
    chave_data[hash_questao]['GABARITO']=alternativa_correta if alternativa_correta else gabarito_site
    
    # Grava as alternativas
    inserir_alternativas_dict(chave_data, alternativas, hash_questao)

def inserir_alternativas_dict(chave_data, alternativas, hash_questao):
    
    # Limpa alternativas existentes
    chave_data[hash_questao]['ALTERNATIVAS'] = {}

    for m, alternativa in enumerate(alternativas):
        chave_data[hash_questao]['ALTERNATIVAS'][m] = escape_html(alternativa)

def salvar_dados_dissertativa(chave_data, hash_questao, enunciado, titulo):
    chave_data[hash_questao]['ESTILO']="DISSERTATIVA"
    chave_data[hash_questao]['ENUNCIADO']=escape_html(enunciado)
    chave_data[hash_questao]['TITULO'] = titulo
    chave_data[hash_questao]['ALTERNATIVAS']=None
    chave_data[hash_questao]['GABARITO']=None
    chave_data['STATUS_ATIVIDADE'] = "FECHADA" 

def salvar_drive_atividade(
        driver,
        aluno,
        curso,
        disciplina,
        atividade,
        titulo,
        questionario,
    ):

        try:
            # print(f"\n\n       >> Insere atividade no Drive: {disciplina.disciplina} - {atividade} \n\n")
            salvar_drive(driver, aluno.curso, disciplina.disciplina, atividade, disciplina.modulo,questionario,titulo)
        except Exception as err:
            
            log_grava(
                err=err,
                msg= curso[aluno.curso]+" - "+disciplina.modulo+" - "+disciplina.disciplina+" - "+atividade
            )
            
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg)

        except (KeyError,UnboundLocalError, Exception) as err:
            """
            - KeyError: erro em obter se é questionário ou discursiva, não tem no Banco de Dados?

            - UnboundLocalError:
            
            """
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            log_grava(
                err=err,
                msg= curso[aluno.curso]+" - "+disciplina.modulo+" - "+disciplina.disciplina+" - "+atividade
            )

def salva_tela(
        driver,
        nome_curso,
        disciplina,
        nome_atividade,
        questionario,
        modulo,
        **kwargs
    ):
    from system.converter_HTML_to_PDF import html_to_pdf
    from system.pastas import diretorio_raiz

    gabarito = kwargs.get("gabarito", [])
    titulo = kwargs.get("titulo", "")
    renumera = kwargs.get("renumera", None)
    data = kwargs.get("data", [])
    atividade_ativa = kwargs.get("atividade_ativa", [])

    # Recupera Sigla dos Cursos
    cursos = dict_curso(opcao=6)
    curso = cursos[nome_curso]

    # retoma dict da Atividade
    atividade=data[curso][disciplina][modulo]['ATIVIDADE'][nome_atividade]
    
    # Verifica se as pastas existem
    verifica_pastas(
        curso=nome_curso,
        disciplina=disciplina,
        modulo=modulo
    )

    # Recupera Apelido do Curso
    cursos_apelido = dict_curso(opcao=4)
    curso_apelido = cursos_apelido[nome_curso]

    modulo = modulo.replace("/","")
    path_papiron = os.path.join(os.path.expanduser("~"), "Desktop\\Papiron")
    
    if atividade_ativa:
        # Monta o arquivo com o gabarito para colocar no drive
        dir_papiron = diretorio_raiz()
        dir_drive = dir_papiron+'\\'+modulo+'\\drive'

        sufixo_drive=definir_sufixo_legado(
            nome_curso=curso_apelido,
            disciplina=disciplina,
            questionario=questionario
        )

        dir_destino = escapa_path(dir_drive+sufixo_drive)  \
                if nome_curso=="GERAL" or ("ESTUDO CONTEMPORÂNEO E TRANSVERSAL" in disciplina or "FORMAÇÃO SOCIOCULTURAL E ÉTICA" in disciplina)\
                else escapa_path(dir_drive+sufixo_drive+'\\'+curso+" - "+disciplina)

        verifica_pastas(pasta=dir_destino)

        dir_temp = dir_papiron+'\\'+modulo+'\\temp'
        verifica_pastas(pasta=dir_temp)
       
    # Caso tenha atividades com o mesmo nome, grava o titulo junto do nome
    if renumera:
        path_file = path_papiron+'\\'+modulo+'\\'+nome_curso+'\\'+curso+" - "+titulo+" - "+modulo
        path_file_at = path_papiron+'\\'+modulo+'\\ATIVIDADES\\'+nome_curso+' - '+titulo
    else:
        path_file = path_papiron+'\\'+modulo+'\\'+nome_curso+'\\'+disciplina+'\\'+curso+" - "+nome_atividade+" - "+disciplina+" - "+modulo
        path_file_at = path_papiron+'\\'+modulo+'\\ATIVIDADES\\'+nome_curso+' - '+disciplina+' - '+curso+" - "+nome_atividade
    

    print(f" {renumera}  \n   - {path_file} \n   - {path_file_at}")
    # Retirar estes trechos do HTML
    a = "<div class=\"alert alert-danger ng-hide\" ng-show=\"vm.tempoMax &gt; 0 &amp;&amp; !vm.questionarioDisabled &amp;&amp; !vm.questionario.finalizado\" style=\"text-align:center;margin:0 auto 15px;width:50%\"> <span>Restam <b class=\"ng-binding\"> </b> para o fim da Atividade Avaliativa</span> </div>"
    b = "<div class=\"alert alert-danger ng-hide\" ng-show=\"vm.tempoMax &gt; 0 &amp;&amp; vm.questionario.situacao.descricao !== 'ABERTO' &amp;&amp; vm.questionarioDisabled\" style=\"text-align:center;margin:0 auto 15px;width:50%\"> <span><b>Data final atingida! A Atividade Avaliativa está indisponível.</b></span> </div>" 
    c = "<div class=\"alert alert-danger ng-hide\" ng-show=\"vm.tempoMax &gt; 0 &amp;&amp; vm.questionario.situacao.descricao === 'ABERTO' &amp;&amp; vm.isTimedout\" style=\"text-align:center;margin:0 auto 15px;width:50%\"> <span><b>Tempo esgotado ! A Atividade Avaliativa está indisponível.</b></span> </div> "
    d = "<span class=\"label label-danger all-caps pull-right m-r-20 ng-hide\" ng-hide=\"!vm.questaoAtual.anulada\"> anulada </span> </div>"

    
    # Cabeçalho UNICESUMAR
    soup = atualizar_soup(driver)
    cab = str(soup.find('div',{'class':'panel panel-default ng-scope'}))

    css_string = """
        <style type="text/css" class="ng-scope">
        .labels{font-family:Calibri,Arial,Roboto Regular,sans-serif;font-size:12px}
        .alternativasBar{padding-top:15px}
        .alternativasList *{font-size:11px;font-family:Verdana}
        .tableTituloQuestionario{border:1px solid #ccc;background:#fff;font-family:Calibri,Arial,Roboto Regular,sans-serif}
        .tableTituloQuestionario tr td{font-family:Calibri,Candara,Segoe,"Segoe UI",Optima,Arial,sans-serif;font-size:14px;color:#444}
        .tableQuestao{border-bottom:1px solid #c5c5c5;margin-top:10px}
        .questTitulo{border-bottom:3px solid #2672ec;color:#283891!important;padding:7px;text-align:left;font-size:16px!important;font-family:Calibri,Candara,Segoe,"Segoe UI",Optima,Arial,sans-serif}
        .tituloAlternativas{border-bottom:3px solid #2672ec;color:#283891;font-family:Calibri;font-size:16px;font-weight:400;text-align:left;margin-top:10px}
        .alternativasList,.enunciadoQuest,.questoes{border:1px solid #ccc}
        .questoes *{font-size:14px!important}
        .questoes{padding:5px 7px}
        </style>
    """
    
    # Se for discursiva
    qtd_gab = 0
    if not questionario:
        body = soup.find('div',{"id":"cabecalhoQuestao"}) #+ css_string
    
    # Se for questionário
    else:
        body = ""

        # Percorre todas as chaves
        # Lista de chaves gerais que NÃO são questões
        chaves_gerais = ['STATUS_ATIVIDADE', 'ID_URL', 'DT_INICIO', 'DT_FIM']

        questao = 0

        for chave, conteudo in atividade.items():

            if chave in chaves_gerais:
                continue  # pula as chaves gerais
            
            questao+=1
            enunciado = conteudo.get('ENUNCIADO')
            gabarito = conteudo.get('GABARITO')
            alternativas = conteudo.get('ALTERNATIVAS')

            qtd_gab = qtd_gab + 1 if gabarito else qtd_gab

            verifica_anulada = False
            informa_anulada = False
            body = body+"<br><br><b> QUESTÃO "+str(questao)+"</b>"+str(enunciado)
            
            if alternativas:
                
                # Inclui a informa de questão anulada
                try:
                    if gabarito and not verifica_anulada:
                        if gabarito=="QUESTÃO ANULADA!":
                            body = body+"<div style=\"font-size:16px;font-weight: 900; background-color: #ffb0b0; border-radius:8px\"><br><br><b><H2>QUESTÃO ANULADA</H2></b><br><br>"
                            informa_anulada = True
                        verifica_anulada = True

                except IndexError as err:
                    msg = str(len(gabarito))+" - "+modulo+" - "+curso_apelido+" - "+disciplina
                    log_grava(msg=msg,err=err)

                for alternativa in alternativas:
                    try:

                        if gabarito == alternativas[alternativa]:
                            body = body+"<br><input type=\"checkbox\" checked> <b>ALTERNATIVA "+str(int(alternativa)+1)+"</b><br><br><div  style=\"font-size:16px;font-weight: 900; background-color: yellow;\">"+alternativas[alternativa]+"</div><br>"
                        else:
                            body = body+"<br><input type=\"checkbox\"> <b>ALTERNATIVA "+str(int(alternativa)+1)+"</b><br><br>"+alternativas[alternativa]+"<br>"
                    except IndexError as err:
                        import traceback
                        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                        print("MMM256:", msg)
                        body = body+"<br><input type=\"checkbox\"> <b>ALTERNATIVA "+str(int(alternativa)+1)+"</b><br><br>"+alternativas[alternativa]+"<br>"
            
            #Fecha o div da anulada
            if informa_anulada:
                body = body+"</div>"


    # Monta HTML da ATIVIDADE
    body = str(body).replace(a,"").replace(b,"").replace(c,"").replace(d,"")
    html_inic = """
                <!DOCTYPE html><html><head>
                <link rel=\"stylesheet\" type=\"text/css\" href=\"../../../files/unicesumar.css\">
                <link rel=\"stylesheet\" type=\"text/css\" href=\"../../files/unicesumar.css\">
                <link rel=\"stylesheet\" type=\"text/css\" href=\"../files/unicesumar.css\">
                <link rel=\"stylesheet\" type=\"text/css\" href=\"unicesumar.css\"
                <meta charset=\"UTF-8\" /><title>PAPIRON</title></head><body>
                """
    html_fim = "<br><br><br><br><br><br><br></body></html>"
    html = html_inic+"<br><br>"+'<div class=\"container\" style=\"border: 0px solid;\">'+"<br><br>"+cab+"<br><br>"+body+'</div>'+html_fim

    path_file_html = path_file[:351] + '.html'  # Ajuste para incluir extensão sem truncar
    path_file_html_at = path_file_at[:351] + '.html'
    path_file_pdf = path_file[:351] + '.pdf'

    # Constroí o nome do arquivo a ser gerado no drive
    # Se for prepare-se ajusta ao título da Atividade

    try:
        # Salva na Pasta Geral de Atividades
        with open(escapa_path(path_file_html_at), 'w', encoding='utf8') as arquivo:
            arquivo.write(html)
        
        # Salva a atividade na Pasta do Curso
        with open(escapa_path(path_file_html), 'w', encoding='utf8') as arquivo:
            arquivo.write(html)

    except FileNotFoundError:
        t(1)
        try:
            # Salva na Pasta Geral de Atividades
            with open(escapa_path(path_file_html_at), 'w', encoding='utf8') as arquivo:
                arquivo.write(html)

            # Salva a atividade na Pasta do Curso
            with open(escapa_path(path_file_html), 'w', encoding='utf8') as arquivo:
                arquivo.write(html)
        
        except FileNotFoundError:
            pass

    html_to_pdf(escapa_path(path_file_html),escapa_path(path_file_pdf))

    if atividade_ativa and questionario:

        curso_drive = " - "+curso+" - " if "GERAL" not in curso else  " - "
        titulo_drive = titulo.replace("ESTUDO CONTEMPORÂNEO E TRANSVERSAL","ECT").replace("FORMAÇÃO SOCIOCULTURAL E ÉTICA I","FSCE1").replace("FORMAÇÃO SOCIOCULTURAL E ÉTICA II","FSCE2").replace("PROJETO DE ENSINO - ","")
        disciplina_drive = disciplina.replace(" ESTUDO CONTEMPORÂNEO E TRANSVERSAL","ECT").replace(" - FORMAÇÃO SOCIOCULTURAL E ÉTICA I","FSCE1").replace(" - FORMAÇÃO SOCIOCULTURAL E ÉTICA II","FSCE2").replace("PROJETO DE ENSINO - ","")
        
        # Primeiro salva em uma pasta TEMP
        path_file_temp = escapa_path(dir_temp+str('\\GAB - '+nome_atividade+curso_drive+titulo_drive)[:100]+" - "+str(qtd_gab)+" de "+str(questao)+".pdf") \
        if ("PREPARE-SE" in disciplina.upper() or "NIVELAMENTO" in disciplina_drive.upper()) \
        else escapa_path(dir_destino+str('\\GAB - '+nome_atividade+curso_drive+disciplina_drive)[:100]+" - "+str(qtd_gab)+" de "+str(questao)+".pdf")

        html_to_pdf(escapa_path(path_file_html),escapa_path(path_file_temp))

        # Depois move para dentro do drive
        path_file_drive = escapa_path(dir_destino+str('\\GAB - '+nome_atividade+curso_drive+titulo_drive)[:100]+" - "+str(qtd_gab)+" de "+str(questao)+".pdf") \
        if ("PREPARE-SE" in disciplina.upper() or "NIVELAMENTO" in disciplina_drive.upper()) \
        else escapa_path(dir_destino+str('\\GAB - '+nome_atividade+curso_drive+disciplina_drive)[:100]+" - "+str(qtd_gab)+" de "+str(questao)+".pdf")
        
        shutil.move(path_file_temp,path_file_drive)
        # print(f"     >> GAB Drive: {path_file_drive}")

def dividir_processos(dados,numero_processos):  
    
    ano, modulo = list(dados.keys())[0], list(dados.values())[0].keys()
    modulo = list(modulo)[0]  # Assumindo só 1 ano/módulo
    cursos = dados[ano][modulo]

    # Junte todas as disciplinas em uma lista [(curso, nome_disciplina, info)]
    todas = []
    for curso, disciplinas in cursos.items():
        for nome_disc, info in disciplinas.items():
            todas.append((curso, nome_disc, info))

    # Quantidade por parte (arredondado para cima)
    qtd_parte = math.ceil(len(todas) / numero_processos)

    # Gerar os splits mantendo a estrutura original
    lista_dicts = []
    for i in range(numero_processos):
        fatia = todas[i*qtd_parte : (i+1)*qtd_parte]
        novo = {ano: {modulo: {}}}
        for curso, nome_disc, info in fatia:
            if curso not in novo[ano][modulo]:
                novo[ano][modulo][curso] = {}
            novo[ano][modulo][curso][nome_disc] = info
        
        with open(f'disc_split_{i+1}.json', 'w', encoding='utf-8') as f:
            json.dump(novo, f, ensure_ascii=False, indent=2)
        print(f'Arquivo "disc_split_{i+1}.json" gerado com {len(fatia)} disciplinas.')

        lista_dicts.append(novo)
    
    return lista_dicts

def listar_disciplinas(self):
    # Obtém as disciplinas do site
    
    lista_json = []

    for mod in self.modulos_abertos:

        try:
            ano = mod[:4]
            modulo = mod[-1]

            # Extrai a lista de todas as disciplinas por curso
            url = f"https://www.papiron.com.br/ferramentas/informar_disciplinas_json/{ano}/{modulo}"
            print("requisitou papiron",url)
            req = requests.get(url)
            dados  = req.json()
            lista_json.append(dados)

            if req.status_code!=200:

                print(req.content)

        except Exception as err:
            log_grava(err=err)
       
    try:
        merged = deepcopy(lista_json[0])
        for data in lista_json[1:]:
            deep_merge(merged, data)

    except Exception as err:
            log_grava(err=err)
    
    save_json(merged,'00/disc_merge.json')

    return merged

def lista_alunos_ra_ect(self,disc_especial):
    
    lista_json = []
    dados = {}
    for mod in self.modulos_abertos:
        try:
            ano_atual = mod[:4]
            modulo = mod[-1]

            # Extrai a lista de todas as disciplinas por curso
            url = f"https://www.papiron.com.br/ferramentas/informar_alunos_json/geral/{disc_especial}/{ano_atual}/{modulo}"
            print("requisitou papiron",url)
            req = requests.get(url)
            dados = req.json()
            lista_json.append(dados)

            if req.status_code!=200:

                print(req.content)

        except Exception as err:
            log_grava(err=err)
       
        try:
            merged = deepcopy(lista_json[0])
            for data in lista_json[1:]:
                deep_merge(merged, data)

        except Exception as err:
                log_grava(err=err)
    
    save_json(merged,'00/disc_merge_ect.json')
    return merged


def lista_alunos_ra_scg(self,disc_especial):
    
    modulo = 9
    ano_atual = datetime.now().year
    url = f"https://www.papiron.com.br/ferramentas/informar_alunos_json/geral/{disc_especial}/{ano_atual}/{modulo}"
    print(f'url >> {url}')
    req = requests.get(url=url, timeout=75)
    self.ras = req.json()

def extrair_disciplinas(data):
    """
    Extrai todas as disciplinas do JSON, mantendo o caminho completo.
    Retorna uma lista de dicionários.
    """
    disciplinas = []
    for ano, modulos in data.items():
        for modulo, cursos in modulos.items():
            for curso, dics in cursos.items():
                for disciplina, info in dics.items():
                    disciplinas.append({
                        "ano": ano,
                        "modulo": modulo,
                        "curso": curso,
                        "disciplina": disciplina,
                        "info": info
                    })
    return disciplinas

def dividir_lista(lista, n):
    """Divide uma lista em n partes aproximadamente iguais."""
    qtd_por_parte = math.ceil(len(lista) / n)
    return [lista[i*qtd_por_parte:(i+1)*qtd_por_parte] for i in range(n)]

def reconstruir_json(lista):
    """Remonta o JSON com o formato original a partir da lista de disciplinas."""
    novo = {}
    for item in lista:
        ano = item["ano"]
        modulo = item["modulo"]
        curso = item["curso"]
        disciplina = item["disciplina"]
        info = item["info"]
        novo.setdefault(ano, {}).setdefault(modulo, {}).setdefault(curso, {})[disciplina] = info
    return novo

def dividir_json_em_n_arquivos(data, output_prefix, n):
    """Processo completo de dividir o JSON em n arquivos."""
    disciplinas = extrair_disciplinas(data)
    partes = dividir_lista(disciplinas, n)
    lista_json = []
    for idx, parte in enumerate(partes):
        novo_json = reconstruir_json(parte)
        filename = f"{output_prefix}{idx+1}.json"
        lista_json.append(novo_json)
        save_json(novo_json, filename)
        print(f"Arquivo '{filename}' salvo com {len(parte)} disciplinas.")
    print("Concluído!")
    return lista_json
