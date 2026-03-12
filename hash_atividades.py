import hashlib
import re
import html

from bs4 import BeautifulSoup
# from system.logger import log_grava

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
        # log_grava(err=err, msg = str(f"\n\n   >>{atual}\n\n"))
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
    # print(hash_base)
    hash_final = hashlib.sha256(hash_base.encode('utf-8')).hexdigest()
    return hash_final

def hash_questionario(lista):
    
    # ordena a lista
    lista_ordenada = sorted(lista)

    # Transforma ela em texto
    concatenada = ''.join(lista_ordenada)
    
    return hashlib.sha256(concatenada.encode()).hexdigest()


############# Funções diferentes do AppEquipe ###########

def normalizar_alternativa(texto):
    """Remove acentos, espaços, quebra de linha e caracteres invisíveis"""
    # Remove caracteres invisíveis e espaços extras
    texto = re.sub(r'\s+', ' ', texto)  # Substitui qualquer whitespace por espaço simples
    texto = texto.strip()
    return texto

def limpar_mantendo_img(texto):
    # Remove todas as tags HTML, exceto <img>
    texto_sem_tags = re.sub(r'<(?!img\b)[^>]*>', '', texto)
    return texto_sem_tags

def normalizar_imagem(texto):
    # Aplica o regex para normalizar nomes dos arquivos de imagem
    padrao = r'(QUE_)\d+(_\d+_\d+\.\w+)'
    return re.sub(padrao, r'\1\2', texto)

def comparar_gabarito(alternativas, gabarito):
    # Limpa e normaliza o gabarito recebido
    gabarito_texto = gabarito
    gabarito_unescape = retirar_todos_unescapes(gabarito_texto)
    gabarito_limpo = limpar_mantendo_img(gabarito_unescape)
    gabarito_norm = normalizar_imagem(gabarito_limpo).strip().lower()

    # print("    >>> GABARITO:",gabarito_norm)
    
    for alt in alternativas:
        # Limpa e normaliza cada alternativa para comparar iguais.
        alt_unescape = retirar_todos_unescapes(alt['descricao'])
        alt_limpo = limpar_mantendo_img(alt_unescape)
        alt_norm = normalizar_imagem(alt_limpo).strip().lower()
        if alt_norm == gabarito_norm:
            return alt['idAlternativa']
    return None