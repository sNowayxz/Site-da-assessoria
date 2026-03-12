import json
import re

import requests
from class_papiron.utils_atividade.utils import remover_tags, retirar_todos_unescapes
from function_bd import save_json
from system.system import t


def verificar_gabarito(self, **kwargs):

    atividade = kwargs['atividade']
    sigla_curso_rastreio = kwargs['sigla_curso_rastreio']
    questoes = atividade['QUESTOES']
    titulo = atividade.get('descricao')

    for questao in questoes:
        
        try:
            # Extrair alternativas da questão, caso não tenha, pula para próxima
            alternativas = questoes[questao].get('alternativaList')
            
            if not alternativas:
                continue
            else:
                print(f"\n       ALTERNATIVAS - [{titulo}] - {sigla_curso_rastreio}")
                for alternativa in alternativas:
                    print(f"       - {alternativa['idAlternativa']} - {remover_tags(retirar_todos_unescapes(alternativa['descricao']))}")


            # Obter o gabarito:
            gabarito = questoes[questao].get('gabarito', None)
            if gabarito:
                print(f"       >>> Gabarito Oficial divulgado: {remover_tags(retirar_todos_unescapes(gabarito))}")
                continue

            else:
                # Verifica se encontra uma questão com gabarito com 
                url = f"https://www.papiron.com.br/atividades/localizar/{questao}"
                req = requests.get(url=url)

                if req.status_code == 200:
                    post_site = req.json()
                    id_url = post_site['id_url']
                    gabarito_site = comparar_gabarito(alternativas, post_site)
                    questoes[questao]['id_url'] = id_url
                    questoes[questao]['atividade_atualizada'] = post_site['atividade_atualizada']
                    print(f"       >>> Gabarito Site: {gabarito_site}")

                    
                else:
                    print(f"    >>>>> Não foi localizado gabarito nem Oficial nem no site")
                    gabarito_site = None
                    questoes[questao]['id_url'] = None
                    questoes[questao]['atividade_atualizada'] = False
            
            
                if not gabarito_site:

                    questoes[questao]['gabarito'] = None

                    questoes[questao]['gabarito_id'] = None

                else:
                    
                    questoes[questao]['gabarito'] = next(
                        (alt['descricao'] for alt in alternativas if alt['idAlternativa'] == gabarito_site),
                        None
                    )

                    questoes[questao]['gabarito_id'] = next(
                        (alt['idAlternativa'] for alt in alternativas if alt['idAlternativa'] == gabarito_site),
                        None
                    )

        except AttributeError as err:
            continue

    atividade['QUESTOES'] = questoes
    return atividade

def limpar_mantendo_img(texto):
    # Remove todas as tags HTML, exceto <img>
    texto_sem_tags = re.sub(r'<(?!img\b)[^>]*>', '', texto)
    return texto_sem_tags

def normalizar_imagem(texto):
    # Aplica o regex para normalizar nomes dos arquivos de imagem
    padrao = r'(QUE_)\d+(_\d+_\d+\.\w+)'
    return re.sub(padrao, r'\1\2', texto)

def comparar_gabarito(alternativas, post):
    # Limpa e normaliza o gabarito recebido
    gabarito_texto = post["gabarito"]
    gabarito_unescape = retirar_todos_unescapes(gabarito_texto)
    gabarito_limpo = limpar_mantendo_img(gabarito_unescape)
    gabarito_norm = normalizar_imagem(gabarito_limpo).strip().lower()

    # print("    >>> GABARITO:",gabarito_norm)
    
    for alt in alternativas:
        # Limpa e normaliza cada alternativa para comparar iguais.
        alt_unescape = retirar_todos_unescapes(alt['descricao'])
        alt_limpo = limpar_mantendo_img(alt_unescape)
        alt_norm = normalizar_imagem(alt_limpo).strip().lower()
        # print("    >>> ALTER:",alt_norm == gabarito_norm, alt_norm)
        if alt_norm == gabarito_norm:
            return alt['idAlternativa']
    return None
