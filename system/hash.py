
import hashlib


def hash_text(text)->str:
    import hashlib

    # Cria um objeto hash com SHA-256
    hash_object = hashlib.sha256()
    
    # Codifica o texto em UTF-8 e atualiza o objeto hash
    hash_object.update(text.encode('utf-8'))
    
    # Obtém o hash hexadecimal
    hex_dig = hash_object.hexdigest()
    
    return hex_dig


def hash_quest(texto)->str:

    import re
    
    # Regex para encontrar o padrão desejado
    padrao = r'(QUE_)\d+(_\d+_\d+\.\w+)'  

    # Substitui o número pela string vazia mantendo o restante intacto 
    texto_alterado = re.sub(padrao, r'\1\2', texto)

    hashi_quest=hash_text(texto_alterado)

    return hashi_quest

def hash_lista(lista:list):
    """
    Gera um hash a partir de uma lista não ordenada

    Listas com ordem diferentes irão produzir o mesmo hash
    
    """
    if lista:

        lista_ordenada = sorted(lista)

        # Transforma ela em texto
        concatenada = ''.join(lista_ordenada)

        return hashlib.sha256(concatenada.encode()).hexdigest()


