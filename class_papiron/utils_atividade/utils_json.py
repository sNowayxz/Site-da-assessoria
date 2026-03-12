import json
import os
from pathlib import Path

from class_papiron.utils_atividade.utils import (
    totalizador_rastreio,
    totalizador_rastreio_aluno,
    totalizador_rastreio_ect,
)
from function_bd import abre_json, save_json
from system.logger import log_grava
from system.pastas import localizar_desktop
from system.system import t
from copy import deepcopy

path_rastreio = Path('bd/atividades/rastreio.json')
path_rastreio_aluno = Path('bd/atividades/rastreio_aluno.json')
path_rastreio_ect = Path('bd/atividades/rastreio_ect.json')

def atualizar_dict_atividades(dict_antigo, dict_novo):
    # Atualiza os gabaritos e adiciona questões novas!
    for desc, atividade_nova in dict_novo.items():

        if desc in dict_antigo:
            
            atividade_antiga = dict_antigo[desc]

            save_json(data=atividade_antiga,path_file="00/at1_atg.json")

            # Atualiza idQuestionario caso tenha mudado
            if atividade_antiga.get('idQuestionario') != atividade_nova.get('idQuestionario'):
                atividade_antiga['idQuestionario'] = atividade_nova.get('idQuestionario')
            #############################################################################
            # pré-condições mínimas (opcional)
            # if not isinstance(atividade_antiga, dict) or not isinstance(atividade_nova, dict):
            #     raise TypeError("atividade_antiga e atividade_nova devem ser dict")

            # questoes_antigas = atividade_antiga.setdefault('QUESTOES', {})
            # questoes_novas = atividade_nova.get('QUESTOES', {})

            # for hash_questao, q_nova in questoes_novas.items():
            #     if not q_nova:
            #         continue  # ignora questão vazia/falsy

            #     q_antiga = questoes_antigas.get(hash_questao)

            #     if q_antiga is not None and isinstance(q_antiga, dict):
            #         changed = False

            #         if 'gabarito' in q_nova and q_antiga.get('gabarito') != q_nova['gabarito']:
            #             q_antiga['gabarito'] = q_nova['gabarito']
            #             changed = True

            #         if 'anulada' in q_nova and q_antiga.get('anulada') != q_nova['anulada']:
            #             q_antiga['anulada'] = q_nova['anulada']
            #             changed = True

            #         if changed:
            #             q_antiga['atualizar_atividade'] = False
            #     else:
            #         # insere como cópia para evitar aliasing indesejado
            #         questoes_antigas[hash_questao] = deepcopy(q_nova)
            ################################################################################
            # # Atualiza QUESTOES
            for hash_questao, questao_nova in atividade_nova.get('QUESTOES', {}).items():
                
                if not questao_nova:
                    # Para casos onde se tem a noticia de nova questao, mas ainda está vazia
                    # sem a key 'QUESTOES'
                    continue

                if hash_questao in atividade_antiga.get('QUESTOES', {}):
                    # Atualiza apenas campos desejados das questões já existentes
                    questao_antiga = atividade_antiga['QUESTOES'][hash_questao]
                    if questao_antiga.get('gabarito') != questao_nova.get('gabarito') or \
                       questao_antiga.get('anulada') != questao_nova.get('anulada'):
                        questao_antiga['gabarito'] = questao_nova.get('gabarito')
                        questao_antiga['anulada'] = questao_nova.get('anulada')
                        questao_antiga['atualizar_atividade'] = False
                else:
                    # ADICIONA nova questão
                    atividade_antiga.setdefault('QUESTOES', {})[hash_questao] = questao_nova
            # Se houver outros campos novos em atividade_nova, pode adicionar aqui se quiser
            #############################################################################
        else:
            # Atividade nova, adiciona inteira
            dict_antigo[desc] = deepcopy(atividade_nova)
            
    return dict_antigo

############ PODE APAGAR CASO FICAR EM DESUSO DE FATO ##############################
def atualizar_gabaritos(dict_antigo, dict_novo):
    # Passo 1: Montar um mapa para lookup rápido das atualizações
    atualizacoes = {}
    
    for q in dict_novo:
        if dict_novo[q].get('QUESTIONARIO'):
            id_q = dict_novo[q]['descricao']
            for hash_questao, questao in dict_novo[q]['QUESTOES'].items():
                atualizacoes[(id_q, hash_questao)] = {
                    'gabarito': questao.get('gabarito'),
                    'anulada': questao.get('anulada')
                }

    # Passo 2: Percorrer o dicionário original e atualizar os campos
    for q in dict_antigo:
        if dict_antigo[q].get('QUESTIONARIO'):
            id_q = dict_antigo[q]['descricao']
            for hash_questao, questao in dict_antigo[q]['QUESTOES'].items():
                chave = (id_q, hash_questao)
                if chave in atualizacoes:
                    # Atualiza apenas os campos desejados
                    if questao['gabarito'] != atualizacoes[chave]['gabarito'] or questao['anulada'] != atualizacoes[chave]['anulada']:
                        questao['gabarito'] = atualizacoes[chave]['gabarito']
                        questao['anulada'] = atualizacoes[chave]['anulada']
                        questao['atualizar_atividade'] = False

    return dict_antigo

def verificar_rastreio(self,curso,disciplina,ano,modulo):
    """
    Verifica se a disciplina já foi rastreada no dia de hoje.
    Retorna True se precisa rastrear (ainda não rastreada no dia),
    e False se já foi rastreada hoje.
    """
    rastreio = carregar_rastreio(self,curso,ano,modulo)

    print("  Disciplinas já efetuado o rastreio no curso hoje:",rastreio[self.data_hoje][ano][modulo][curso])

    # Retorna False se ainda não foi rastreada (deve rastrear)
    # Retorna True se já foi rastreada (não precisa rastrear de novo)
    return disciplina in rastreio[self.data_hoje][ano][modulo][curso]

def verificar_rastreio_ect(self,ra,ano,modulo):
    """
    Verifica se a disciplina já foi rastreada no dia de hoje.
    Retorna True se precisa rastrear (ainda não rastreada no dia),
    e False se já foi rastreada hoje.
    """
    rastreio = carregar_rastreio_ect(self,ano ,modulo)

    # Retorna False se ainda não foi rastreada (deve rastrear)
    # Retorna True se já foi rastreada (não precisa rastrear de novo)
    return ra in rastreio[self.data_hoje][ano][modulo]

def gravar_rastreio(self,**kwargs):
    """
    Registra que a disciplina foi rastreada no dia atual.

    Este método grava no arquivo JSON um registro indicando que a disciplina
    (informada nos atributos do objeto) foi rastreada na data de hoje,
    organizando os dados por data, ano, módulo e curso.

    Se o rastreio já foi realizado para a disciplina no dia corrente,
    não haverá duplicidade.
    """
    curso_rastreio=kwargs['curso_rastreio']
    ano_rastreio=kwargs['ano_rastreio']
    modulo_rastreio=kwargs['modulo_rastreio']
    disciplina_rastreio=kwargs['disciplina_rastreio']
    
    # Carrega o rastreio atual
    rastreio = carregar_rastreio(self,curso_rastreio,ano_rastreio,modulo_rastreio)   

    # Adiciona disciplina se não ainda existir no rastreio do dia
    if disciplina_rastreio not in rastreio[self.data_hoje][ano_rastreio][modulo_rastreio][curso_rastreio]:
            

        rastreio[self.data_hoje][ano_rastreio][modulo_rastreio][curso_rastreio].append(disciplina_rastreio)

        # Salva de volta
        print(f"\n       >>> SALVAR Json: {curso_rastreio} - {disciplina_rastreio} - {rastreio[self.data_hoje][ano_rastreio][modulo_rastreio][curso_rastreio]}")
        with open(path_rastreio, 'w', encoding='utf-8') as f:
            json.dump(rastreio, f, ensure_ascii=False, indent=4)
   
    
    else:
        print(f"    >>> não vai salvar {curso_rastreio} - {disciplina_rastreio} - {rastreio[self.data_hoje][ano_rastreio][modulo_rastreio][curso_rastreio]}")

    # Emite o sinal 
    self.updateProgress.emit(totalizador_rastreio(self), None)

def carregar_rastreio(self,curso,ano,modulo):
    
    path = Path('bd/atividades/rastreio.json')
    # Carrega rastreio, se existir
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            rastreio = json.load(f)
    else:
        rastreio = {}

    # Garante que os níveis intermediários existem
    rastreio.setdefault(self.data_hoje, {})
    rastreio[self.data_hoje].setdefault(ano, {})
    rastreio[self.data_hoje][ano].setdefault(modulo, {})
    rastreio[self.data_hoje][ano][modulo].setdefault(curso, [])

    return rastreio

def carregar_rastreio_ect(self,ano,modulo):
    
    path = path_rastreio_ect
    # Carrega rastreio, se existir
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            rastreio = json.load(f)
    else:
        rastreio = {}

    # Garante que os níveis intermediários existem
    rastreio.setdefault(self.data_hoje, {})
    rastreio[self.data_hoje].setdefault(ano, {})
    rastreio[self.data_hoje][ano].setdefault(modulo, [])

    return rastreio

def verificar_rastreio_aluno(self,ra):
    """
    Verifica se a disciplina já foi rastreada no dia de hoje.
    Retorna True se precisa rastrear (ainda não rastreada no dia),
    e False se já foi rastreada hoje.
    """
    rastreio = carregar_rastreio_aluno(self)

    # Retorna False se ainda não foi rastreada (deve rastrear)
    # Retorna True se já foi rastreada (não precisa rastrear de novo)
    return ra in rastreio[self.data_hoje]

def carregar_rastreio_aluno(self):
    
    # Carrega rastreio do aluno, se existir
    if path_rastreio_aluno.exists():
        with open(path_rastreio_aluno, 'r', encoding='utf-8') as f:
            rastreio = json.load(f)
    else:
        rastreio = {}

    # Garante que os níveis intermediários existem
    rastreio.setdefault(self.data_hoje, [])
    return rastreio

def gravar_rastreio_aluno(self,ra):
    """
    Registra que a disciplina foi rastreada no dia atual.

    Este método grava no arquivo JSON um registro indicando que a disciplina
    (informada nos atributos do objeto) foi rastreada na data de hoje,
    organizando os dados por data, ano, módulo e curso.

    Se o rastreio já foi realizado para a disciplina no dia corrente,
    não haverá duplicidade.
    """
    print(f"   Gravando rastreio do aluno {ra}")
    
    # Carrega o rastreio atual
    rastreio = carregar_rastreio_aluno(self)   

    # Adiciona disciplina se não ainda existir no rastreio do dia
    if ra not in rastreio[self.data_hoje]:
            
        rastreio[self.data_hoje].append(ra)

        # Salva de volta
        print(f"\n       >>> SALVAR Json: {ra}")
        with open(path_rastreio_aluno, 'w', encoding='utf-8') as f:
            json.dump(rastreio, f, ensure_ascii=False, indent=4)
   
    else:
        print(f"    >>> não vai salvar {ra}")

    # Emite o sinal 
    self.updateProgress.emit(totalizador_rastreio_aluno(self), None)

def gravar_rastreio_ect(self,ano,modulo,ra):
    """
    Registra que a disciplina foi rastreada no dia atual.

    Este método grava no arquivo JSON um registro indicando que a disciplina
    (informada nos atributos do objeto) foi rastreada na data de hoje,
    organizando os dados por data, ano, módulo e curso.

    Se o rastreio já foi realizado para a disciplina no dia corrente,
    não haverá duplicidade.
    """
    print(f"   Gravando rastreio do aluno {ra}")
    
    # Carrega o rastreio atual
    rastreio = carregar_rastreio_ect(self,ano,modulo)

    # Adiciona disciplina se não ainda existir no rastreio do dia
    if ra not in rastreio[self.data_hoje][ano][modulo]:
            
        rastreio[self.data_hoje][ano][modulo].append(ra)

        # Salva de volta
        print(f"\n       >>> SALVAR Json: {ra}")
        with open(path_rastreio_ect, 'w', encoding='utf-8') as f:
            json.dump(rastreio, f, ensure_ascii=False, indent=4)
   
    else:
        print(f"    >>> não vai salvar {ra}")

    # Emite o sinal 
    self.updateProgress.emit(totalizador_rastreio_ect(self), None)

def abrir_arquivo_path_drive_json(self,**kwargs):
    """
    Abre o arquivo que contém os dados de hash de cada disciplina
    
    """
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']

    caminho_drive_json = os.path.join(
            localizar_desktop(), 
            "Papiron",
            "drive",
            f"drive_{ano_rastreio}_{modulo_rastreio}",
            f"drive_{ano_rastreio}_{modulo_rastreio}.json"
        )
    
    data = abre_json(path_file=caminho_drive_json)

    return data


def obter_path_file_drive_json(self,**kwargs):
    """
    Envia o caminho completo do arquivo que contém os dados de hash de cada disciplina
    
    """
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']

    caminho_drive_json = os.path.join(
            localizar_desktop(), 
            "Papiron",
            "drive",
            f"drive_{ano_rastreio}_{modulo_rastreio}",
            f"drive_{ano_rastreio}_{modulo_rastreio}.json"
        )

    return caminho_drive_json

def caminho_completo(**kwargs):
    # Crie o caminho da pasta onde será ou está salvo o arquivo json da disciplina
    
    
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    disciplina_rastreio = kwargs['disciplina_rastreio']
    
    caminho_pasta = os.path.join(
        "BD", 
        "Atividades", 
        str(ano_rastreio), 
        str(modulo_rastreio), 
        curso_rastreio
    )

    # Certifique-se de que o diretório existe
    os.makedirs(caminho_pasta, exist_ok=True)

    # Nome do arquivo .json
    arquivo_json = f"{disciplina_rastreio}.json"

    # Retorna caminho completo do arquivo
    return os.path.join(caminho_pasta, arquivo_json)
