import re , html
from datetime import datetime,date
import hashlib

from class_papiron.class_error import DisciplinaScrappedError
from function_bd import abre_json
from functions.escape import escape_html
from bs4 import BeautifulSoup

from system.logger import log_grava
from system.system import t

def verificar_lista_disciplinas(self,disciplina_ra):

    if self.config['disciplina_unica']:
        texto = self.config['disciplina_unica']
        lista = re.split(r'[;]\s*', texto.upper())
        if disciplina_ra['nm_disciplina'] not in lista:
            raise DisciplinaScrappedError
        else:
            print(f"     >>>> LOCALIZOU, irá iniciar o rastreio")

def totalizador_rastreio(self):
    """
    Calcula o total de disciplinas presentes no arquivo de rastreio.

    Este método lê o arquivo JSON de rastreio em 'BD/atividades/rastreio.json' e percorre toda a estrutura de dados,
    somando a quantidade de disciplinas listadas para cada curso, módulo e ano, na chave correspondente à data de hoje
    (armazenada em self.data_hoje).

    Returns
    -------
    int
        O total de disciplinas encontradas no rastreio para a data informada.

    """
    total_disciplinas = 0
    dados = abre_json('BD/atividades/rastreio.json')

    if self.data_hoje not in dados:
        return 0

    for ano in dados[self.data_hoje].values():
        for modulo in ano.values():
            for curso, lista_disciplinas in modulo.items():
                total_disciplinas += len(lista_disciplinas)

    return total_disciplinas

def totalizador_rastreio_ect(self):
    """
    Calcula o total de disciplinas presentes no arquivo de rastreio.

    Este método lê o arquivo JSON de rastreio em 'BD/atividades/rastreio.json' e percorre toda a estrutura de dados,
    somando a quantidade de disciplinas listadas para cada curso, módulo e ano, na chave correspondente à data de hoje
    (armazenada em self.data_hoje).

    Returns
    -------
    int
        O total de disciplinas encontradas no rastreio para a data informada.

    """
    total_ras = 0
    dados = abre_json('BD/atividades/rastreio_ect.json')

    if self.data_hoje not in dados:
        return 0

    for ano in dados[self.data_hoje].values():
        for modulo in ano.values():
            total_ras += len(modulo)

    return total_ras

def totalizador_rastreio_aluno(self):
    """
    Calcula o total de disciplinas presentes no arquivo de rastreio.

    Este método lê o arquivo JSON de rastreio em 'BD/atividades/rastreio.json' e percorre toda a estrutura de dados,
    somando a quantidade de disciplinas listadas para cada curso, módulo e ano, na chave correspondente à data de hoje
    (armazenada em self.data_hoje).

    Returns
    -------
    int
        O total de disciplinas encontradas no rastreio para a data informada.

    """

    dados = abre_json('BD/atividades/rastreio_aluno.json')

    lista_ra_rastreados = dados.setdefault(self.data_hoje, [])

    return len(lista_ra_rastreados)

def gerar_hash_concatenado(lista_hashes):
    try:
        if lista_hashes:
            texto = '|'.join(lista_hashes)
            return hashlib.sha256(texto.encode('utf-8')).hexdigest()
        else:
            return None
    except TypeError:
        print(lista_hashes)
        t(180)

def limpar_nome(nome):
    nome = str(nome).strip()
    # Remove caracteres inválidos para arquivo
    nome = re.sub(r'[\\/:*?"<>|\x00-\x1f\u200B\u200C\u200D\u200E\u200F\uFEFF]', '', nome)
    return nome

def ajustar_nome_arquivo(nome_arquivo):
    # Diminui nomes muito extensos
    nome_arquivo = nome_arquivo.replace("ESTUDO CONTEMPORÂNEO E TRANSVERSAL","ECT - ").replace("FORMAÇÃO SOCIOCULTURAL E ÉTICA II","FSCE II").replace("FORMAÇÃO SOCIOCULTURAL E ÉTICA I","FSCE I")
    return nome_arquivo

def formatar_enunciado(self, atividade):
    
    atividade_utf = retirar_todos_unescapes(atividade)

    atividade_utf = f"<div class=\"enunciado ng-binding\" ng-bind-html=\"vm.questaoAtual.descricaoHtml  | mathJaxFix\">{atividade_utf}</div>"

    atividade_utf = remover_attr_bs(atividade_utf, 'class')

    atividade_utf = remover_attr_bs(atividade_utf, 'style')

    atividade_utf = remover_tags(atividade_utf)

    atividade_utf = atividade_utf.replace("<br />","<br/>").replace("https://","http://")
                                        
    atividade_formatada = escape_html(texto=atividade_utf)

    return atividade_formatada

def formatar_alternativa(self, alternativa):

    alternativa_base = retirar_todos_unescapes(alternativa)

    alternativa_formatada = remover_attr_bs(alternativa_base, 'class')

    alternativa_formatada = remover_tags(alternativa_formatada)

    alternativa_formatada = alternativa_formatada.replace("https://","http://")

    alternativa_formatada = escape_html(alternativa_formatada)

    alternativa_formatada = retirar_todos_unescapes(alternativa_formatada)

    return alternativa_formatada

def contar_gabaritos(self,data):

    questoes = data['QUESTOES'].values()

    qtd_gabarito = 0
    qtd_anulada = 0

    for q in questoes:
        try:
            # Conta se tem gabarito (não nulo)
            if q.get("gabarito") is not None:
                qtd_gabarito += 1
            # Conta se está anulada (True)
            if q.get("anulada") is True:
                qtd_anulada += 1

            if q.get("gabarito") is not None and q.get("anulada") is True:
                qtd_gabarito -= 1

        except AttributeError:
            print(f">>>>>utils qq {q}\n\n{questoes}")

    return qtd_anulada + qtd_gabarito

def limpar_dict(dados):
    # Campos para remover:
    chaves_para_remover = [
        'diffDataFinal',
        'diffDataFinalEspecial',
        'tempoMax',
        'especialPorcentagem',
        'especialDataFinal',
        'dataAlunoLiberado',
        'feedback',
        'dataFeedback',
        'dependenteVisualiza',
        'idTipoEvento',
        'notaQuestionario',
    ]

    for item in dados:

        for chave in chaves_para_remover:
            item.pop(chave, None)
        
        item['descricao']=limpar_egrad(item)

    return dados

def limpar_egrad(item):
    """
    Normaliza o EGRAD para juntas possíveis diferentes descrições da mesma atividade
    """
    if 'EGRAD' in item['descricao']:
        item['descricao'] = re.sub(r'EGRAD_\w+', item["legenda"], item["descricao"])
        item['descricao'] = item['descricao'][:90]
    
    return item['descricao']

def limpar_idurl_errado(data):

    for q in data:
        if 'QUESTOES' in q and isinstance(q['QUESTOES'], dict):
            questoes = q['QUESTOES']
            # Remove somente se id_url está nesse nível (e não dentro das questões)
            if 'id_url' in questoes:
                log_grava(msg = f" Apagou id url errado: {questoes['id_url']}")
                del questoes['id_url']
    
    return data

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

def remover_tags(html):

    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(True): # True = todas as tags
            if tag.name != "img" and tag.name != "http" and tag.name != "https":
                tag.unwrap() 

        return str(soup)
    
    except TypeError:
        return html

    except Exception as err:
        log_grava(err=err, msg = str(f"\n\n   >>> {html}\n\n"))
        return html

def normalizar_espacos(texto):
    import re

    try:
        # Remove múltiplos espaços, tabs e quebras de linha
        return re.sub(r'\s+', ' ', texto).strip()

    except TypeError:
        return texto
    
    except Exception as err:
        log_grava(err=err, msg = str(f"\n\n   >>>> {texto}\n\n"))
        return texto

def formatar_data_ms_to_date(timestamp_ms):

    # Converter para segundos (dividindo por 1000)
    timestamp_s = timestamp_ms / 1000

    # Converter para datetime
    data = datetime.fromtimestamp(timestamp_s)

    return data.strftime('%Y-%m-%d')  # formato ISO

def formatar_data_ms_iso(timestamp_ms):

    timestamp_s = timestamp_ms / 1000

    data = datetime.fromtimestamp(timestamp_s)

    return data.strftime('%Y-%m-%d')  # formato ISO

def verificar_data_inicio(data_inicial_ms, data_base_str=None):
    """
    True se:
      - data_inicial <= agora
      - ou (se houver data_base) data_inicial <= data_base
    data_base_str no formato 'YYYY-MM-DD'
    """
    data_inicial = datetime.fromtimestamp(data_inicial_ms / 1000)
    hoje = datetime.now()

    # print(f"\n   >> data_inicial = {data_inicial}")
    # print(f"   >> data_base = {data_base_str}")

    if data_base_str:
        try:
            # vira meia-noite do dia informado, no horário local
            data_base = datetime.strptime(data_base_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("data_base deve estar no formato 'AAAA-MM-DD'")
        
        # print(f"   >> limite = {hoje} >>> {data_inicial <= hoje} , {data_inicial>=data_base}\n\n")
        if data_inicial <= hoje:

            return data_inicial>=data_base
        
        else:
            return False

    else:    
        # print(f"   >> limite = {hoje} >>> {data_inicial <= hoje}")
        # t(8)
        return data_inicial <= hoje
    
def hora_atual_texto():
    agora = datetime.now()
    hora_formatada = agora.strftime("%H:%M:%S")
    return f"{hora_formatada}"

def trimestre():

    QUARTER_BY_MONTH = {
            1: 1, 2: 1, 3: 1,
            4: 2, 5: 2, 6: 2,
            7: 3, 8: 3, 9: 3,
            10: 4, 11: 4, 12: 4
            }    
    d = date.today()
    return QUARTER_BY_MONTH[d.month]
