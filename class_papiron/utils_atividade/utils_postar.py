import json
import random
import string
import traceback

import requests as rq
from bs4 import BeautifulSoup as BS
from functions.curso import dict_curso
from requests.exceptions import ConnectionError, ConnectTimeout
from requests_toolbelt import MultipartEncoder
from system.logger import log_grava
from system.system import t


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
            gabarito:str
        )->str:

    cont = 10
    while cont:
        try:
            url = "https://www.papiron.com.br/atividades/form/pergunta_automatica_v2"
            r = rq.get(url, headers=headers , allow_redirects=False)
            soup = BS(r.content, "html.parser")
            csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})['value']
            dict_cursos_nome = dict_curso(opcao=5)
            curso_nome = dict_cursos_nome[curso]
            fields = {
                'csrfmiddlewaretoken': csrfmiddlewaretoken,
                'conteudo':'new',
                'faculdade':faculdade,
                'curso':curso_nome,
                'disciplina':disciplina,
                'titulo':titulo,
                'pergunta':enunciado,
                'atividade':atividade,   
                'questao':questao,
                'dt_inicio': dt_inicio_str, 
                'dt_fim': dt_fim_str,
                'alternativas': alternativas,  # pode ser dict ou "null"; a função resolve
                'mod_ano':mod_ano,
                'mod_ref':mod_ref,
                'gabarito':gabarito,           # None será removido
            }

            fields = _prepare_fields_for_post(fields, is_questionario=bool(cb_questionario))
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
                "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica_v2",
                "Content-Type": m.content_type,
                "Upgrade-Insecure-Requests": "1"
            }            
            r = rq.post(url,headers=headers_b, data = m , allow_redirects=False,timeout=180)

            id_url = _extract_id_from_location(r)


            return id_url

        except (ConnectTimeout,ConnectionError,KeyError,TypeError) as err:
            cont-=1
            if not cont:
                msg1 = f"     Falha GERAL de envio na atividade {titulo}\n"
                print(msg1)
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"  >> Falha em enviar a atividade: "+str(cont)
                log_grava(err=err,msg=msg1+msg)
                return None
            print(f"     Falha de envio na atividade {titulo}")
            log_grava(err=err)
            t(60)
        
        except Exception as err:
            log_grava(err=err)
            raise Exception
            
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

    url = "https://www.papiron.com.br/atividades/form/pergunta_automatica_quest_v2"

    cont = 10
    try:
        while cont:
            r_entrando = rq.get(url, headers=headers, allow_redirects=False)
            soup = BS(r_entrando.content, "html.parser")
            csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})['value']
            dict_cursos_nome = dict_curso(opcao=5)
            curso_nome = dict_cursos_nome[curso]
            fields = {
                'csrfmiddlewaretoken': csrfmiddlewaretoken,
                # 'ids_url': str(ids_url),
                'ids_url':json.dumps(ids_url),
                'faculdade':faculdade,
                'curso':curso_nome,
                'disciplina':disciplina,
                'atividade':atividade,
                'questao':questao,
                'titulo':titulo,
                'estilo':'on',
                'dt_inicio': dt_inicio_str, 
                'dt_fim': dt_fim_str,
                'mod_ano':str(mod_ano),
                'mod_ref':str(mod_ref),
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
                "Referer": "https://www.papiron.com.br/atividades/form/pergunta_automatica_quest_v2",
                "Content-Type": m.content_type,
                "Upgrade-Insecure-Requests": "1"
            } 
            
            r_postanto = rq.post(url, headers=headers_b , data = m , allow_redirects=False,timeout=120)

            id_url = _extract_id_from_location(r_postanto)

            return id_url
        
    except (ConnectTimeout,ConnectionError,KeyError,TypeError) as err:
        cont-=1
        t(60)
        if cont==0:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"  >> Falha em enviar o questionário COMPLETO:"
            print(msg)
            return None

    
    except Exception as err:
        log_grava(err=err)
        raise Exception
    
def _prepare_fields_for_post(fields: dict, is_questionario: bool) -> dict:

    out = {}
    for k, v in fields.items():
        if v is None:
            # não envia chaves nulas; evita "None" ir para o servidor
            continue

        if k == 'alternativas':
            # v pode ser dict, string "null", etc.
            if isinstance(v, (dict, list)):
                out[k] = json.dumps(v, ensure_ascii=False)
            else:
                s = str(v).strip()
                # trata "null", "", "[]" como vazio
                if s.lower() in ('null', '', '[]'):
                    out[k] = '{}'
                else:
                    # se parecer JSON bom, manda do jeito que veio; senão, envolve como {}
                    out[k] = s if s.startswith('{') else '{}'
            continue

        # valores normais como string
        out[k] = str(v)

    if is_questionario:
        out['estilo'] = 'on'
    else:
        out.pop('estilo', None)

    return out


def _extract_id_from_location(resp, default=None):
    """
    resp: objeto Response do requests
    retorna o id_url contido no Location (último segmento do path)
    """
    from urllib.parse import urlparse
    loc = resp.headers.get('Location')
    if not loc:
        raise ConnectionError
    path = urlparse(loc).path              # funciona p/ URL absoluta ou relativa
    parts = [p for p in path.split('/') if p]
    return parts[-1] if parts else default

# def verificar_atividade_site(questao):
#     """
    
#     Verifica se acha a questão no site

#     """
#     try:
#         url = f"https://www.papiron.com.br/atividades/localizar/{questao}"
#         req = rq.get(url=url)
#         return True if req.status_code == 200 else False
    
#     except Exception as err:
#         log_grava(err=err)
#         raise Exception
