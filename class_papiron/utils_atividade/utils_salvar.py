import json
import os
import shutil
from pathlib import Path

import requests
from class_papiron.utils_atividade.utils import (
    ajustar_nome_arquivo,
    formatar_data_ms_to_date,
    gerar_hash_concatenado,
    limpar_idurl_errado,
    limpar_nome,
    verificar_data_inicio,
)
from class_papiron.utils_atividade.utils_downloads import salvar_atividade
from class_papiron.utils_atividade.utils_gabarito import verificar_gabarito
from class_papiron.utils_atividade.utils_json import (
    abrir_arquivo_path_drive_json,
    atualizar_dict_atividades,
    caminho_completo,
    obter_path_file_drive_json,
)
from class_papiron.utils_atividade.utils_postar import (
    postar_atividade,
    postar_questionario,
)
from function_bd import abre_json, save_json
from system.logger import log_grava
from system.pastas import definir_sufixo, localizar_desktop
from system.system import t


def montar_nome_pasta(base, disciplina):
    """Monta o nome final da pasta com a disciplina."""
    return f"{base} - {limpar_nome(disciplina)}"

def recuperando_dados_salvos_disciplina_descricao(**kwargs):
    """
    Recupera dados já salvos no arquivos das disciplinas
    """
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    disciplina_rastreio = kwargs['disciplina_rastreio']
    atividades_req = kwargs['atividades_req']
    
    # Carregando o arquivo local (se existir)
    path = Path(
        caminho_completo(
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            curso_rastreio=curso_rastreio,
            disciplina_rastreio=disciplina_rastreio,
        )
    )

    print(f"   caminho onde deve ser salvo>> {path}")
    
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            dados_antigos = json.load(f)
    else:
        dados_antigos = []

    try:
        # Indexando pelo campo desejado
        atividades_antigas = { str(item["descricao"]) : item for item in dados_antigos}
        atividades_novas =   { str(item["descricao"]): item for item in atividades_req}
        
        #  Atualiza o gabarito caso ele seja fornecido desta vez
        if dados_antigos:
            print( "   > Atualizando dados da Disciplina")
            atividades_antigas = atualizar_dict_atividades(atividades_antigas,atividades_novas)
            atividades = limpar_idurl_errado(list(atividades_antigas.values()))
            atividades_novas = list(atividades_novas.values())
            print(f"    >> Dados atualizados com sucesso")
        else:
            print( "   > Primeiro RASTREIO da Disciplina!")
            atividades = limpar_idurl_errado(list(atividades_novas.values()))
            print(f"    >> Dados verificados com sucesso")

    except TypeError as err:
        log_grava(err=err)
        raise TypeError
    
    return atividades

def recuperando_dados_salvos_disciplina_legenda(**kwargs):
    """
    Recupera dados já salvos no arquivos das disciplinas
    """
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    disciplina_rastreio = kwargs['disciplina_rastreio']
    atividades_req = kwargs['atividades_req']
    
    # Carregando o arquivo local (se existir)
    path = Path(
        caminho_completo(
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            curso_rastreio=curso_rastreio,
            disciplina_rastreio=disciplina_rastreio,
        )
    )

    print(f"   caminho onde deve ser salvo>> {path}")
    
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            dados_antigos = json.load(f)
    else:
        dados_antigos = []

    try:
        # Indexando pelo campo desejado
        atividades_antigas = { str(item["legenda"]) : item for item in dados_antigos}
        atividades_novas =   { str(item["legenda"]): item for item in atividades_req}
        
        #  Atualiza o gabarito caso ele seja fornecido desta vez
        if dados_antigos:
            print( "   > Atualizando dados da Disciplina")
            save_json(data=atividades_antigas,path_file="00/at_atg.json")
            save_json(data=atividades_novas,path_file="00/at_nv.json")
            atividades_antigas = atualizar_dict_atividades(atividades_antigas,atividades_novas)
            atividades = limpar_idurl_errado(list(atividades_antigas.values()))
            atividades_novas = list(atividades_novas.values())
            print(f"    >> Dados atualizados com sucesso")
        else:
            print( "   > Primeiro RASTREIO da Disciplina!")
            atividades = limpar_idurl_errado(list(atividades_novas.values()))
            print(f"    >> Dados verificados com sucesso")

    except TypeError as err:
        log_grava(err=err)
        raise TypeError
    
    return atividades
                  
def gerenciar_nome_drive(self, **kwargs):
    import json
    import os
    import shutil

    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    sigla_curso_rastreio=kwargs['sigla_curso_rastreio']
    atividades = kwargs['atividades']
    disciplina_rastreio = kwargs['disciplina_rastreio']
    print("\n    >> Definindo nome de pastas e arquivos")

    # ---------------------------
    # 1) Coleta dos hashes
    # ---------------------------
    atividades_discursivas = []
    atividades_questionario = []

    for atividade in list(atividades):
        if not verificar_data_inicio(atividade['dataInicial'], data_base_str=self.data_base):
            continue
        try:
            hashes_enunciado = list(atividade['QUESTOES'].keys())
            hashes_enunciado.sort()

            if disciplina_rastreio == "SEMANA DE CONHECIMENTOS GERAIS":
                continue
            elif "ESTUDO CONTEMPORÂNEO E TRANSVERSAL" in disciplina_rastreio and atividade.get('legenda') == "AV":
                pass
            else:
                if atividade.get("QUESTIONARIO"):
                    atividades_questionario.extend(hashes_enunciado)
                else:
                    atividades_discursivas.extend(hashes_enunciado)

        except KeyError:
            continue
        except Exception as err:
            log_grava(err=err)

    atividades_discursivas = sorted(set(atividades_discursivas))
    atividades_questionario = sorted(set(atividades_questionario))

    # ---------------------------
    # 2) Abre JSON geral
    # ---------------------------
    dados_drive_geral = abrir_arquivo_path_drive_json(
        self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio
    )

    # ---------------------------
    # 3) Casos especiais
    # ---------------------------
    

    # ---------------------------
    # 4) Hashes do curso/disciplina
    # ---------------------------
    dados_drive_disciplina = {
        'discursiva': gerar_hash_concatenado(atividades_discursivas),
        'questionario': gerar_hash_concatenado(atividades_questionario)
    }

    # ---------------------------
    # 5) Loop (discursiva / questionário)
    # ---------------------------
    for item in dados_drive_disciplina:
        try:
            hash_atividade = dados_drive_disciplina[item]
            if not hash_atividade:
                print(f"      > [{item}] - Não possui atividades do tipo para que sejam gerados HASH")
                continue

            # Garante entrada no JSON para este hash
            if hash_atividade not in dados_drive_geral:
                dados_drive_geral[hash_atividade] = {
                    'cursos': [sigla_curso_rastreio],
                    'questionario': (item == 'questionario'),
                    'drive': ''
                }
            else:
                # adiciona curso se necessário
                if sigla_curso_rastreio not in dados_drive_geral[hash_atividade]['cursos']:
                    dados_drive_geral[hash_atividade]['cursos'].append(sigla_curso_rastreio)
                dados_drive_geral[hash_atividade]['cursos'].sort()

            # >>> PATCH: capture o caminho ANTIGO antes de alterar qualquer coisa
            old_base = dados_drive_geral[hash_atividade].get('drive', '') or ''
            old_base = ajustar_nome_arquivo(old_base).replace("\\ - ", "")
            disciplina_limpa = limpar_nome(disciplina_rastreio)
            old_full = (f"{old_base} - {disciplina_limpa}") if old_base else ""

            # monta sufixo de pasta (com sua regra)
            cursos = dados_drive_geral[hash_atividade]['cursos']
            num_cursos = len(cursos)
            if num_cursos == 1:
                sufixo_lista_curso = cursos[0]
            elif num_cursos <= 5:
                sufixo_lista_curso = " - ".join(cursos)
            elif num_cursos <= 10:
                a_maior = num_cursos - 5
                sufixo_lista_curso = "AAB - " + "-".join(cursos[:5]) + f" + {a_maior}"
            else:
                sufixo_lista_curso = "AAA - GERAL"

            sufixo = definir_sufixo(
                nome_curso=curso_rastreio,
                disciplina=disciplina_limpa,
                questionario=dados_drive_geral[hash_atividade]['questionario']
            )

            # subpastas especiais
            if "PREPARE-SE" in disciplina_rastreio:
                subpasta = "PREPARE-SE"
            elif "PROJETO DE ENSINO" in disciplina_rastreio:
                subpasta = "PROJETO DE ENSINO"
            elif "NIVELAMENTO" in disciplina_rastreio:
                subpasta = os.path.join("NIVELAMENTO", disciplina_rastreio)
            else:
                subpasta = None

            # caminho base NOVO (sem a parte " - disciplina")
            new_base = os.path.join(
                localizar_desktop(), "Papiron", "drive",
                f"drive_{ano_rastreio}_{modulo_rastreio}",
                "AA - ATIVIDADES COMPLEMENTARES" if subpasta else sufixo,
                subpasta if subpasta else sufixo_lista_curso
            )
            new_base = ajustar_nome_arquivo(new_base).replace("\\ - ", "")
            new_full = f"{new_base} - {disciplina_limpa}"

            # Se for subpasta especial, não concatena a disciplina no nome final mostrado
            if subpasta:
                # apenas define o base e salva
                dados_drive_geral[hash_atividade]['drive'] = new_base
                print(
                    f"      > Atribuído o nome da pasta [{item}] : {new_base}"
                    if subpasta != "PREPARE-SE"
                    else f"      > Atribuído o nome da pasta [{item}] : {new_base} - {disciplina_limpa}"
                )
                continue

            # >>> PATCH: decide por diferença real de caminhos
            needs_move = bool(old_full) and (old_full != new_full)

            try:
                if needs_move:
                    # garante pasta-mãe no destino
                    os.makedirs(os.path.dirname(new_full), exist_ok=True)
                    # tenta rename atômico na mesma unidade
                    try:
                        os.replace(old_full, new_full)
                    except OSError:
                        # fallback: pode cruzar unidades
                        shutil.move(old_full, new_full)

                elif not old_full:
                    # primeira vez: garanta existência do destino
                    os.makedirs(new_full, exist_ok=True)

                # atualiza JSON somente após mover/criar
                dados_drive_geral[hash_atividade]['drive'] = new_base
                print(f"      > Atribuído o nome da pasta [{item}] : {new_base} - {disciplina_limpa}"
                      + ("  (renomeada)" if needs_move else ""))

            except FileNotFoundError:
                # origem não existe: apenas cria destino
                os.makedirs(new_full, exist_ok=True)
                dados_drive_geral[hash_atividade]['drive'] = new_base

            except FileExistsError:
                # destino já existe; se a origem ainda existir e for diferente, remova origem
                if needs_move and os.path.isdir(old_full) and os.path.isdir(new_full):
                    shutil.rmtree(old_full)
                dados_drive_geral[hash_atividade]['drive'] = new_base

            except Exception as err:
                log_grava(err=err)

        except Exception as err:
            log_grava(err=err)

    # ---------------------------
    # 6) Salva JSON
    # ---------------------------
    save_json(
        data=dados_drive_geral,
        path_file=obter_path_file_drive_json(
            self,
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio
        )
    )

    return dados_drive_disciplina

def gerenciar_nome_drive_complementar(self, **kwargs):

    disciplina_rastreio = kwargs['disciplina_rastreio']
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    estilo = kwargs['estilo']
    print(f"\n    >> Definindo nome da pasta do {estilo}: {disciplina_rastreio}")
    
    # Carrega o arquivo com os hashes atuais ( opção =1)
    dados_drive_geral = abrir_arquivo_path_drive_json(
        self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio
    )

    hash_disciplina =  gerar_hash_concatenado(f"{disciplina_rastreio}|{ano_rastreio}|{modulo_rastreio}") 

    path_complemento = "ECT - FSCE - ATIV INTEGRADORAS" if estilo=="ETC" else "SCG"
    
    caminho_atividade_drive_ect = os.path.join(
            localizar_desktop(), 
            "Papiron", 
            "drive",
            f"drive_{ano_rastreio}_{modulo_rastreio}",
            "AA - ATIVIDADES COMPLEMENTARES",
            path_complemento,
            ajustar_nome_arquivo(disciplina_rastreio)
        )

    # Monta o dict da disciplina no arquivo json do ano_modulo
    dados_drive_geral.setdefault(hash_disciplina, {
        "cursos": ["GERAL"],
        "questionario": True,
        "drive": caminho_atividade_drive_ect,
    })

    # Obtém o caminho do arquivo do json que contém dados de cada disciplina
    path_file = obter_path_file_drive_json(
        self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio
    )
    
    # Salva dados do caminho das pastas do disciplina dentro do JSON
    save_json(
        data=dados_drive_geral,
        path_file=path_file
    )

    # Cria dados da localização da disciplina no drive para ser utlizado
    # na rotina de salvamento local. Este dict é um dos componentes do 
    # JSON que compões "dados_drive_geral"
    dados_drive_disciplina = {
        'discursiva': None,
        'questionario': hash_disciplina
    }

    return dados_drive_disciplina

def salvar_dados_rastreio_geral(self,**kwargs):

    ano_rastreio=kwargs['ano_rastreio']
    modulo_rastreio=kwargs['modulo_rastreio']
    mod_curso_rastreio=kwargs['mod_curso_rastreio']
    curso_rastreio=kwargs['curso_rastreio']
    sigla_curso_rastreio=kwargs['sigla_curso_rastreio']
    atividades=kwargs['atividades']
    disciplina_rastreio=kwargs['disciplina_rastreio']
    dados_drive_disciplina=kwargs.get('dados_drive_disciplina')

    with open(caminho_completo(
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            curso_rastreio=curso_rastreio,
            disciplina_rastreio=disciplina_rastreio,
        ), 'w', encoding='utf-8') as f:
        json.dump(list(atividades), f, ensure_ascii=False, indent=2)

    # gerenciar_nome_drive(self)

    # Imprime de uma vez todas as questões de SCG ou de AV Digital do ECT
    # Salvar dados Localmente
    salvar_dados_rastreio_local(
        self,                                
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio,
        curso_rastreio=curso_rastreio,
        sigla_curso_rastreio=sigla_curso_rastreio,
        disciplina_salvamento=disciplina_rastreio,
        atividades=atividades,
        dados_drive_disciplina=dados_drive_disciplina
    )

    # Salvar dados Remotamente
    # arrumar
    salvar_dados_rastreio_remoto(self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio,
        mod_curso_rastreio=mod_curso_rastreio,
        curso_rastreio=curso_rastreio,
        sigla_curso_rastreio=sigla_curso_rastreio,
        atividades=atividades,
        disciplina_rastreio=disciplina_rastreio,
    )

    with open(caminho_completo(
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            curso_rastreio=curso_rastreio,
            disciplina_rastreio=disciplina_rastreio,
        ), 'w', encoding='utf-8') as f:
        json.dump(list(atividades), f, ensure_ascii=False, indent=2)

def salvar_dados_rastreio_ect(self,**kwargs):
    # Salva dados locais e remoto do ECT

    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    mod_curso_rastreio = kwargs['mod_curso_rastreio']
    sigla_curso_rastreio=kwargs['sigla_curso_rastreio']
    dict_atividades_ect = kwargs['dict_atividades_ect']
    
    for disciplina_etc in dict_atividades_ect:

        dados_drive_disciplina = gerenciar_nome_drive_complementar(
            self=self,
            disciplina_rastreio=disciplina_etc,
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            estilo = "ETC"
        )
        
        try:
            salvar_dados_rastreio_local(
                self,                            
                ano_rastreio=ano_rastreio,
                modulo_rastreio=modulo_rastreio,
                curso_rastreio=curso_rastreio,
                sigla_curso_rastreio=sigla_curso_rastreio,
                disciplina_salvamento=disciplina_etc,
                dados_drive_disciplina=dados_drive_disciplina,
                atividades=dict_atividades_ect[disciplina_etc],
            )
            
            # Salvar dados Remotamente
            salvar_dados_rastreio_remoto(self,
                ano_rastreio=ano_rastreio,
                modulo_rastreio=modulo_rastreio,
                mod_curso_rastreio=mod_curso_rastreio,
                curso_rastreio=curso_rastreio,
                sigla_curso_rastreio=sigla_curso_rastreio,
                atividades=dict_atividades_ect[disciplina_etc],
                disciplina_rastreio=disciplina_etc,
            )
        
        except Exception as err:
            log_grava(msg="[ERRO 1947] - Estudar", err=err)

def salvar_dados_rastreio_local(self, **kwargs):
    # Salva os dados localmente e remotamente
    
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    sigla_curso_rastreio=kwargs['sigla_curso_rastreio']
    atividades = kwargs['atividades']
    disciplina_salvamento = kwargs['disciplina_salvamento']
    dados_drive_disciplina=kwargs['dados_drive_disciplina']

    
    for idx, atividade in enumerate(atividades):
        print("\n    >> Iniciando procedimentos de salvamento LOCAL", atividade['descricao'])

        try:

            # Só processa se a data já passou
            if not verificar_data_inicio(atividade['dataInicial'],data_base_str=self.data_base):
                print("  <<<<>>> Pulouu")
                continue

            if atividade.get('gabarito'):
                # Se a atividade já possui gabarito, não precisa procurar novamente
                # a não ser que isso seja desejável no futuro, para corrigir eventuais
                # gabaritos enviados errados
                print(f"    >>> Verificou que a questão já possui gabarito salvo no BD")
                continue
        
        except Exception as err:
            log_grava(err=err)

        # Atualiza a atividade com o gabarito conferido, caso seja questionário
        if self.config['rastrear_scg']: # SCG não possui questões repetidas então não precisa perder tempo procurando
            continue

        try:
            questionario=atividade.get('QUESTIONARIO')
            if questionario:
                atividades[idx] = verificar_gabarito(
                    self, 
                    atividade=atividade,
                    sigla_curso_rastreio=sigla_curso_rastreio
                )
                atividade = atividades[idx] # fazendo que o 'atividade' também tenha os novos valores da dict
        
        except KeyError as err:
            # Ocorreu falha na busca pelas questões da atividade
            save_json(data=atividade,path_file='00/at_ect.json')
            log_grava(msg=f" Ocorreu falha na busca pelas questões da atividade: {atividade['descricao']} \n",err=err)
            continue
        
    
    for idx, atividade in enumerate(atividades):

        print(f"\n\n    >> Salvando localmente: {atividade.get('descricao')}")

        try:
            questionario=atividade.get('QUESTIONARIO')
            questoes=atividade.get('QUESTOES')
            if not questoes:
                print(f"   >>> Atividade sem questões {atividade}")
                continue
            
            salvar_atividade(
                self,
                atividade_tipo=atividade,
                ano_rastreio=ano_rastreio,
                modulo_rastreio=modulo_rastreio,
                questionario=questionario,
                disciplina_salvamento = disciplina_salvamento,
                dados_drive_disciplina=dados_drive_disciplina
            )
            print(f"    >>>> Finalizou de salvar localmente") 

        except KeyError as err:
            save_json(data=atividade,path_file='00/ect_questio.json')
            log_grava(msg="[ERRO 3245] - Estudar erro de de key", err=err)
        
        except Exception as err:
            log_grava(msg="[ERRO 5746] - Estudar erro", err=err)

        # Salvamento intermediário
        with open(
            caminho_completo(
                ano_rastreio=ano_rastreio,
                modulo_rastreio=modulo_rastreio,
                curso_rastreio=curso_rastreio,
                disciplina_rastreio=disciplina_salvamento,
                ), 'w', encoding='utf-8') as f:
            json.dump(list(atividades), f, ensure_ascii=False, indent=2)

def salvar_dados_rastreio_remoto(self, **kwargs):
    ano_rastreio=kwargs['ano_rastreio']
    modulo_rastreio=kwargs['modulo_rastreio']
    mod_curso_rastreio = kwargs['mod_curso_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    sigla_curso_rastreio = kwargs['sigla_curso_rastreio']
    atividades = kwargs['atividades']
    disciplina_rastreio = kwargs['disciplina_rastreio']
        
    print("\n    >> Iniciando procedimentos de salvamento REMOTO")
    for idx, atividade in enumerate(atividades):

        try:

            lista_id_url=[]

            # Só processa se a data já passou
            if not verificar_data_inicio(atividade['dataInicial'],data_base_str=self.data_base):
                continue

            ## Enviar para o site questões novas
            questoes = atividade.get('QUESTOES')
            if not questoes:
                import winsound
                winsound.Beep(5000,3000)
                t(30)
                continue

            print(f"\n  >>> Salvando Remotamente no site: {atividade['descricao']}")
            
            for questao in questoes:

                if questoes[questao].get('id_url') and questoes[questao].get('gabarito'):
                # if questoes[questao].get('id_url') and questoes[questao].get('gabarito'):
                    # testa se o id_url ainda está no BD
                    url_teste_idurl = f"https://www.papiron.com.br/atividades/idurl/{questoes[questao].get('id_url')}"
                    req = requests.get(url=url_teste_idurl)
                    if req.status_code==200:                   
                        # se os dados da atividade já possuem id_url e gabarito
                        # Se o id_url está ativo
                        # a princípio não tem mais o que enviar para o site,
                        # só se for eventual correção, tem que implementar
                        print(f"     >>> Ciclo da Atividade concluído.")
                        print(f"     >>>>> id_url: {atividade.get('id_url')}")
                        print(f"     >>>>> gabarito: {atividade.get('gabarito')}")
                        questoes[questao]['gabarito_enviado']=True
                        # Adiciona o id_url a listagem geral, para envio do questionário completo
                        lista_id_url.append(questoes[questao]['id_url'])
                        continue
                try:
                    enunciado = questoes[questao]['descricaoHtml']
                except TypeError as err:
                    log_grava(err=err)

                lista_alternativas = questoes[questao]['alternativaList']

                if lista_alternativas:

                    alternativas_site = {"alternativas": {str(i):alternativa['descricao'] for i, alternativa in enumerate(lista_alternativas)}}
                    
                    if questoes[questao]['gabarito']:

                        alternativas_site["gabarito"] = questoes[questao]['gabarito']

                else:
                    alternativas_site=None

                print(f"      >>> Enviando para o site: {disciplina_rastreio} - {atividade['legenda']} - {questao} ")

                try:

                    id_url_questao = questoes[questao].get('id_url')
                    if id_url_questao:
                        print(f"      >>>> Encontrada id_url_questao: {id_url_questao}")
                    else:
                        # print(f"      >>>> Ainda não enviada", questoes[questao])
                        print(f"      >>>> Ainda não enviada")
                    # Somente envia a atividade caso não tenha uma id_url ainda
                    if not id_url_questao:

                        tentativas = 3
                        while tentativas and not id_url_questao:

                            print("     >>> Enviando id url não enviada")

                            id_url_questao = postar_atividade(
                                self,
                                headers= self.headers_papiron,
                                faculdade= "UNICESUMAR",
                                curso= sigla_curso_rastreio,
                                disciplina=disciplina_rastreio,
                                titulo=atividade['descricao'],
                                enunciado=enunciado,
                                atividade=atividade['legenda'],
                                questao=questao,
                                cb_questionario=atividade['QUESTIONARIO'],
                                dt_inicio_str=formatar_data_ms_to_date(atividade['dataInicial']), 
                                dt_fim_str=formatar_data_ms_to_date(atividade['dataFinal']), 
                                alternativas=alternativas_site,
                                mod_ano=ano_rastreio,
                                mod_ref=f"{mod_curso_rastreio}{modulo_rastreio}",
                                gabarito=questoes[questao].get('gabarito'),
                                )

                            # Caso não consiga atribuir um id_url, tenta novamente
                            if not id_url_questao:
                                print(f"      >>>> Erro ao enviar para o site:")
                                tentativas -=1
                                t(60)
                                print(f"      >>>> Nova tentativa {3-tentativas}/2:")
                            else:
                                break

                        # Caso o envio já tenha o gabarito, faz o registro do envio do gabarito
                        if questoes[questao].get('gabarito'):
                            questoes[questao]['gabarito_enviado'] = True


                        if id_url_questao:
                            print(f"      >>>>> Atribuída ID_URL: {id_url_questao}")
                            # data_temp[curso][disciplina][modulo]['ATIVIDADE'][atividade][questao]['ID_URL'] = id_url_enviada
                            questoes[questao]['id_url'] = id_url_questao
                            
                            # Antes de adicionar a lista, verifica se não houve erro em postar duplicado.
                            if id_url_questao not in lista_id_url:
                                lista_id_url.append(id_url_questao)
                                str_lista_geral = f'...{str(lista_id_url)[-103:]}' if len(str(lista_id_url)[-103:])>=100 else str(lista_id_url)
                                print(f"      >>>>>>> Lista de ID_URLs atual [{len(lista_id_url)}/{len(questoes)}]: {str_lista_geral} \n")
                        
                        else:
                            print(f"      >>>>> Não foi possível atribuir ID_URL a questão: {id_url_questao}")
                            import winsound
                            winsound.Beep(5000,3000)
                            t(60)
                            log_grava(msg=f" Não foi possível atribuir ID_URL {atividade['descricao']} - {self.disciplina_rastreio}")
                
                    else:
                        # Adiciona à Lista de id geral da atividade
                        lista_id_url.append(id_url_questao)

                        print(f"      >>>>> Atividade já enviada, verificando envio Gabarito.")
                        
                        # Caso tenha a id_url, veja se o gabarito foi enviado
                        # Necessário que:
                        # -> gabarito_enviado = False
                        # -> gabarito = [não seja Nulo]
                        if (not questoes[questao].get('gabarito_enviado') and 
                                questoes[questao].get('gabarito')):
                            
                            print(f"      >>>>>>> Verificar gabarito")
                            for alt in alternativas_site['alternativas']:
                                alternativa_texto=alternativas_site['alternativas'][alt][:100]
                                print(f"       -> {alt} - {alternativa_texto}")
                            print(f"       GAB: {questoes[questao]['gabarito'][:100]}")
    
                            url_gabarito = f"https://www.papiron.com.br/ferramentas/gabarito/{id_url_questao}"
                            req_gab = requests.get(url=url_gabarito)
                            gabarito_no_site="SIM" if req_gab.status_code==200 else "NÃO"
                            print(f"      >>>> Gabarito no site? {gabarito_no_site}")
                            
                            if req_gab.status_code != 200:

                                id_url_questao = postar_atividade(
                                    self,
                                    headers= self.headers_papiron,
                                    faculdade= "UNICESUMAR",
                                    curso= sigla_curso_rastreio,
                                    disciplina=disciplina_rastreio,
                                    titulo=atividade['descricao'],
                                    enunciado=enunciado,
                                    atividade=atividade['legenda'],
                                    questao=questao,
                                    cb_questionario=atividade['QUESTIONARIO'],
                                    dt_inicio_str=formatar_data_ms_to_date(atividade['dataInicial']), 
                                    dt_fim_str=formatar_data_ms_to_date(atividade['dataFinal']), 
                                    alternativas=alternativas_site,
                                    mod_ano=ano_rastreio,
                                    mod_ref=f"{mod_curso_rastreio}{modulo_rastreio}",
                                    gabarito=questoes[questao]['gabarito']
                                )

                                if id_url_questao:
                                    print(f"      >>>>>>> Enviado com sucesso\n")
                                    questoes[questao]['gabarito_enviado'] = True

                            else:
                                # Fica constatado que já tem gabarito no site, regista no BD
                                print(f"      >>>>>>> ID URL já possui gabarito enviado\n")
                                questoes[questao]['gabarito_enviado'] = True
                            

                        elif (questoes[questao].get('gabarito_enviado') and 
                            questoes[questao].get('gabarito')):
                            # Tem Gabarito e tem a anotação que foi enviado
                            print(f"      >>>>>>> Anotações de Gabarito já finalizados\n")

                        elif (not questoes[questao].get('gabarito')):
                            print(f"      >>>>>>> Questão não possui gabarito disponível ainda\n")
                        
                        else:
                            # print(f"      >>>>>>> Questão não possui gabarito disponível ainda\n")
                            pass

                except KeyError as err:
                    msg = f"{curso_rastreio} - {disciplina_rastreio}"
                    log_grava(err=err, msg=msg)
                
                except Exception  as err:
                    log_grava(err=err)

        except Exception  as err:
                log_grava(err=err)

        # Finalizou de enviar as atividades unitárias, agora envia a global se houver
        # ou apenas atribui o mesmo id_url da questão na atividade 
        try:

            print(f"\n      >>> ENVIAR ATIVIDADE, QTD:{len(lista_id_url)}")

            if len(lista_id_url)>1:

                print("\n      >>> ENVIAR QUESTIONÁRIO COMPLETO", 'id_url' not in atividades[idx])

                cont=3
                while cont:
                    if 'id_url' not in atividades[idx]:
                        print("      >>> Enviando para Papiron")
                        id_url_atividade = postar_questionario(
                            self,
                            ids_url=lista_id_url,
                            headers=self.headers_papiron,
                            faculdade="UNICESUMAR",
                            curso=sigla_curso_rastreio,
                            disciplina=disciplina_rastreio,
                            atividade=atividade['legenda'],
                            questao = "QUESTIONÁRIO",
                            titulo = atividade['descricao'],
                            dt_inicio_str=formatar_data_ms_to_date(atividade['dataInicial']),
                            dt_fim_str=formatar_data_ms_to_date(atividade['dataFinal']),
                            mod_ano=ano_rastreio,
                            mod_ref=f"{mod_curso_rastreio}{modulo_rastreio}",
                        )

                        print(f"      >>> Enviado com sucesso, ID QUESTIONÁRIO: {id_url_atividade}")

                        # Consolida as atividades
                        atividades[idx]['id_url'] = id_url_atividade
                        break
                    
                    else:
                        cont-=1
                        if not verificar_lista_id_urls(self,atividades[idx]['id_url'],lista_id_url):
                            # Casos existam erros, retira a key e refaz o envio
                            try:
                                atividades[idx].pop('id_url', None)
                            except KeyError:
                                pass

                mensagem_fallback = "\n\n\n\n     !!!!!! Atenção, não foi possível gerar a lista de ID GERAL\n\n\n\n"
                id_url = atividades[idx].get("id_url", mensagem_fallback)
                print(f"      >>>>>>> ID URL Geral : {id_url}")

            elif len(lista_id_url)==1: 
                atividades[idx]['id_url'] = lista_id_url[0]           
            else:
                log_grava(msg=f"[erro 4502] - estudar erro: {atividade['descricao']} \n\n {atividade}")
        
        except KeyError as err:
            log_grava(err=err)

        except Exception  as err:
            log_grava(err=err)

def verificar_lista_id_urls(self,id_url,lista):
        # URL do endpoint (ajuste conforme necessário)
        
        if not id_url:
            return False
        
        url = "http://www.papiron.com.br/atividades/robots/verifica_automatica_quest/" + id_url

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lança erro se status != 200

            lista_ids = response.json()  # ✅ Converte a resposta para list Python
            print("      > IDs recebidos:", lista_ids)

            lista_original = list(lista)

            lista_original.sort()

            if lista_original == lista_ids:
                return True

        except requests.exceptions.HTTPError as errh:
            print("Erro HTTP:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Erro de Conexão:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout:", errt)
        except requests.exceptions.RequestException as err:
            print("Erro:", err)
        
        return False
