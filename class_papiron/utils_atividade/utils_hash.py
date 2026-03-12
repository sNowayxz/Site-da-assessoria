import hashlib
import re
import html

from bs4 import BeautifulSoup
from system.logger import log_grava

def retirar_todos_unescapes(atual):
    try:
        anterior = None
        while anterior != atual:
            anterior = atual
            atual = html.unescape(atual)
        return atual
        
    except TypeError:
        return atual
    
    except Exception as err:
        log_grava(err=err, msg = str(f"\n\n   >>{atual}\n\n"))
        return atual

def remover_attr_bs(html,attr):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):  # True pega todas as tags
        if attr in tag.attrs:
            del tag.attrs[attr]
    return str(soup)

def limpar_html(texto):
    """Remove todas as tags HTML exceto <img>"""
    # Mantém <img ...>
    texto = re.sub(r'<(?!img\b)[^>]*>', '', texto)
    return texto

def normalizar_texto(texto):
    import unicodedata, re

    # Remove espaços e caracteres invisíveis comuns
    for c in ['\xa0', '\u200b', '\u200c', '\u200d', '\uFEFF', '\u200e', '\u200f']:
        texto = texto.replace(c, '')
    # Remove caracteres de controle Unicode (categoria C)
    texto = ''.join(c for c in texto if not unicodedata.category(c).startswith('C'))
    # Reduz múltiplos whitespaces
    texto = re.sub(r'\s+', ' ', texto).strip()
    # Remove acentuação
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    # Tudo minúsculo
    texto = texto.lower()
    # Final, só por garantia
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def formatar_hash_img(texto)->str:
    """
    As imagens no Studeo são idênticas, exceto pelo número secundário
    que aparece na url da imagem, então retira esse número para gerar o hash
    """
    # Regex para encontrar o padrão desejado
    padrao = r'(QUE_)\d+(_\d+_\d+\.\w+)'        
    # Substitui o número pela string vazia mantendo o restante intacto
    texto_alterado = re.sub(padrao, r'\1\2', texto, flags=re.IGNORECASE)

    texto_limpo = limpar_scr_img(texto_alterado)

    return texto_limpo

def limpar_scr_img(texto):

    soup = BeautifulSoup(texto, 'html.parser')

    for img in soup.find_all('img'):
        src = img.get('src', '')
        # Substituir a tag <img> pelo valor do atributo src (pode adaptar para link ou só o texto)
        img.replace_with(src)

    texto_limpo = str(soup).replace("https","http")
    return texto_limpo

def gerar_hash_atividade(enunciado, alternativas_dict=None):
    # Limpa enunciado
    texto_enunciado = retirar_todos_unescapes(enunciado)
    texto_enunciado = remover_attr_bs(texto_enunciado,"class")
    texto_enunciado = limpar_html(texto_enunciado)
    texto_enunciado = normalizar_texto(texto_enunciado)
    texto_enunciado = formatar_hash_img(texto_enunciado)

    hash_base = texto_enunciado

    if alternativas_dict:
        # Alternativas para lista, remove html, normaliza e ordena
        alternativas_limpa = [
            formatar_hash_img(
                normalizar_texto(
                    limpar_html(
                        remover_attr_bs(
                                retirar_todos_unescapes(alt),"class")
            )))
            for alt in alternativas_dict.values()
        ]
        alternativas_ordenadas = sorted(alternativas_limpa)
        hash_base += '|' + '|'.join(alternativas_ordenadas)

    # Limpeza final
    hash_base = re.sub(r'\s+', ' ', hash_base).strip()
    hash_base = hash_base.replace(" ","")

    # Gera hash SHA256
    hash_final = hashlib.sha256(hash_base.encode('utf-8')).hexdigest()
    return hash_final

# def gerar_hash_atividade_errada(enunciado, alternativas_dict=None):
#     # Limpa enunciado
#     texto_enunciado = retirar_todos_unescapes(enunciado)
#     texto_enunciado = limpar_html(texto_enunciado)
#     texto_enunciado = normalizar_texto(texto_enunciado)
#     texto_enunciado = formatar_hash_img_errada(texto_enunciado)

#     hash_base = texto_enunciado

#     if alternativas_dict:
#         # Alternativas para lista, remove html, normaliza e ordena
#         alternativas_limpa = [
#             formatar_hash_img_errada(
#                 normalizar_texto(
#                     limpar_html(
#                         retirar_todos_unescapes(alt)
#             )))
#             for alt in alternativas_dict.values()
#         ]
#         alternativas_ordenadas = sorted(alternativas_limpa)
#         hash_base += '|' + '|'.join(alternativas_ordenadas)

#     # Gera hash SHA256
#     hash_base = re.sub(r'\s+', ' ', hash_base).strip()
#     hash_final = hashlib.sha256(hash_base.encode('utf-8')).hexdigest()
#     return hash_final

# def gerar_hash_legado(self, enunciado, alternativas):

#     lista_alternativas = []
#     lista_hash_alternativas = []
#     alternativas_str = None

#     atividade_formatada =  formatar_enunciado(self,enunciado)

#     if alternativas:

#         for alternativa in alternativas:

#             lista_alternativas.append(formatar_alternativa(self,alternativa['descricao']))

#         lista_alternativas.sort()

#     # Junta as alternativas em ordem alfabética em uma string e extrai o hash
#     alternativas_str = "".join(lista_alternativas)

#     lista_hash_alternativas.append(hash_quest(alternativas_str))

#     texto_hash = atividade_formatada+alternativas_str if alternativas_str else atividade_formatada

#     hash_legado = hash_quest(texto_hash)

#     return hash_legado

# def formatar_hash_img_errada(texto)->str:
#     """
#     As imagens no Studeo são idênticas, exceto pelo número secundário
#     que aparece na url da imagem, então retira esse número para gerar o hash
#     """
#     # Regex para encontrar o padrão desejado
#     padrao = r'(QUE_)\d+(_\d+_\d+\.\w+)'        
#     # Substitui o número pela string vazia mantendo o restante intacto
#     texto_alterado = re.sub(padrao, r'\1\2', texto)
#     return texto_alterado
