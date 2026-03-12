

import html
import requests
from class_papiron.class_error import DisciplinaNotIniciadaError, RastreioError
from class_papiron.utils_atividade.utils import (
    ajustar_nome_arquivo,
    limpar_dict,
    limpar_egrad,
    limpar_nome,
    retirar_todos_unescapes,
    verificar_data_inicio,
)
from class_papiron.utils_atividade.utils_hash import gerar_hash_atividade
from class_papiron.utils_atividade.utils_json import carregar_rastreio
from class_papiron.utils_atividade.utils_salvar import recuperando_dados_salvos_disciplina_descricao
from system.logger import log_grava
from system.system import t

LISTA=[ 
    "ESTUDO CONTEMPORÂNEO E TRANSVERSAL",
    "FORMAÇÃO SOCIOCULTURAL E ÉTICA",
    "PREPARE-SE",
    "PROJETO DE ENSINO",
    "NIVELAMENTO"
]
        
def rastrear_atividades_ra(self, **kwargs):
    
    ra=kwargs.get('ra')
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    disciplina_rastreio = kwargs['disciplina_rastreio']
    cd_shortname_rastreio = kwargs['cd_shortname_rastreio']
    curso_rastreio = kwargs['curso_rastreio']
    sigla_curso_rastreio = kwargs['sigla_curso_rastreio']
    # dados_drive_disciplina=kwargs.get('dados_drive_disciplina')
    # mod_curso_rastreio = "5"
    
    cont = 3
    while cont:
        try:

            print(f"\n   RASTREIO ATUAL>> {sigla_curso_rastreio} - {disciplina_rastreio} - {cd_shortname_rastreio}")

            url_disciplina = f"https://studeoapi.unicesumar.edu.br/objeto-ensino-api-controller/api/questionario/disciplina/{cd_shortname_rastreio}"
            self.headers['Host'] = "studeoapi.unicesumar.edu.br"
            req_relacao_atividades = requests.get(url=url_disciplina, headers=self.headers)

            if req_relacao_atividades.status_code != 200:
                log_grava(msg=f"ERRO l288 {ra}")
                return
        
            # JSON das atividades da disciplina
            atividades_req = req_relacao_atividades.json()

            if atividades_req:

                atividades_req = limpar_dict(atividades_req)
                
                atividades = recuperando_dados_salvos_disciplina_descricao(
                    ano_rastreio=ano_rastreio,
                    modulo_rastreio=modulo_rastreio,
                    curso_rastreio=curso_rastreio,
                    disciplina_rastreio=disciplina_rastreio,
                    atividades_req=atividades_req
                )

                try:         
                    percorrer_atividades(
                        self,
                        disciplina_rastreio = disciplina_rastreio,
                        cd_shortname_rastreio = cd_shortname_rastreio,
                        atividades=atividades,
                    )                                                    
                
                except RastreioError:
                    raise RastreioError                                     

            else:
                print(f"    >>> Disciplina não possui Atividades abertas no portal")
                raise DisciplinaNotIniciadaError
                # não tem nenhum atividade disponível  

            return atividades
        
        except (requests.exceptions.RequestException,requests.exceptions.ConnectionError) as e:
            cont -=1
            msg = f"Erro de conexão ou requisição: {e}"
            log_grava(msg=msg)
            print(msg)
            t(300)
            if not cont:
                log_grava(msg=f"\nERRO FINAL: {msg}")
                raise RastreioError
            
        except RastreioError:
            raise RastreioError  
        
        except DisciplinaNotIniciadaError:
            raise DisciplinaNotIniciadaError
        
        except Exception as err:
            log_grava(err=err)
            raise RastreioError       

def dados_iniciais_rastreio(self,**kwargs):

    # Nomear variáveis relativas ao rastreio atual,
    # dentro do perfil do aluno
    disciplina_ra=kwargs['disciplina_ra']
    curso_rastreio = kwargs['curso']
    ra=kwargs['ra']

    ano_rastreio = str(disciplina_ra["ano"])
    modulo_rastreio = str(disciplina_ra["modulo"])
    mod_curso_rastreio = ra[-1]
    disciplina_rastreio = limpar_nome(disciplina_ra["nm_disciplina"])
    cd_shortname_rastreio = disciplina_ra['cd_shortname']
    curso_verificar_rastreio = curso_rastreio
    disciplina_verificar_rastreio = limpar_nome(disciplina_ra["nm_disciplina"])
    sigla_curso_rastreio = self.cursos_papiron[curso_rastreio]


    # Verifica se faz de uma disciplina geral, para gerar arquivos únicos
    if any(disc in disciplina_rastreio for disc in LISTA):
        sigla_curso_rastreio = "GERAL"
        curso_rastreio = "GERAL"
        disciplina_rastreio = ajustar_nome_arquivo(disciplina_rastreio)
    
    return [ano_rastreio,
        modulo_rastreio,
        mod_curso_rastreio,
        disciplina_rastreio,
        cd_shortname_rastreio,
        curso_verificar_rastreio,
        disciplina_verificar_rastreio,
        curso_rastreio,
        sigla_curso_rastreio,
    ]
        
def buscar_disciplina_de_rastreio(self,**kwargs):

    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    curso = kwargs['curso']
    curso_rastreio = kwargs['curso_rastreio']
    disciplina_rastreio = kwargs['disciplina_rastreio']
    lista_curso_disciplinas=kwargs['lista_curso_disciplinas']
    disciplina_verificar_rastreio = kwargs['disciplina_verificar_rastreio']
    curso_verificar_rastreio=kwargs['curso_verificar_rastreio']

    # Busca no JSON geral e no JSON do rastreio
    # Faz se achar no Geral E não achar no rastreio
    existe = False 
    rastreio_json = True
    
    # print(f'\n   Analisando condições de rastreio da disciplina a ser rastreada: [{self.curso}] - {self.disciplina_rastreio} MOD:{self.modulo_rastreio}_{self.ano_rastreio}')
    
    # Disciplinas Gerais fora da LISTA pulam
    if modulo_rastreio == "9":
        if not any(disc in disciplina_rastreio for disc in LISTA):
            # print(f'     >> Disciplina Geral: {disciplina_rastreio}') 
            # print(f'     >>>> Excluída do Rastreio') 
            return False
        
    if ano_rastreio in lista_curso_disciplinas:

        if modulo_rastreio in lista_curso_disciplinas[ano_rastreio]:

            # Verifica se a disciplina de rastreio está na lista geral para ser rastreada
            if disciplina_verificar_rastreio in lista_curso_disciplinas[ano_rastreio][modulo_rastreio][curso_verificar_rastreio]:
                print(f'\n   Analisando condições de rastreio da disciplina a ser rastreada: [{curso}] - {disciplina_rastreio} MOD:{modulo_rastreio}_{ano_rastreio}')
                print(f"   > Localizada na lista geral")
                existe = True
                rastreio =  carregar_rastreio(self,curso_rastreio,ano_rastreio,modulo_rastreio)
                
                # Se achou a disciplina_rastreio na lista geral, então
                # tem que verificar se ela não foi rastreada em outro momento
                if ajustar_nome_arquivo(disciplina_rastreio) not in rastreio[self.data_hoje][ano_rastreio][modulo_rastreio][curso_rastreio]:
                    print(f"   > Ainda não rastreada hoje")
                    rastreio_json = False
                else:
                    print(f"   > Já foi efetuado o rastreio hoje, pular para próxima disciplina.")
                    return False
            
            else:
                # print(f'     >> pertence a outro CURSO') 
                return False
            
        else:
            # print(f'     >> pertence a outro MÓDULO') 
            return False
            
    else:
        # print(f'     >> pertence a outro ANO') 
        return False
    
    # A disciplina_rastreio está presenta na lista geral e ainda não foi rastreada
    if existe and not rastreio_json:
        # Se a disciplina do loop estiver na lista geral então
        # pode proceder ao rastreio
        print(f"   >> Condições OK para RASTREAR: [{curso_rastreio}] {disciplina_rastreio}")
        return True

    else:
        if existe and rastreio_json:
            print(f"    >> RASTREIO FEITO: {disciplina_rastreio} - {modulo_rastreio}_{ano_rastreio} - {existe} - {rastreio_json} na lista geral, PRÓXIMO ")
        return False

        

def percorrer_atividades(self, **kwargs):
    """
    atividades: é uma lista de dicts de cada Atividade individual
    
    """

    disciplina_rastreio = kwargs.get('disciplina_rastreio')
    cd_shortname_rastreio = kwargs.get('cd_shortname_rastreio')
    atividades = kwargs.get('atividades')
    disciplina_rastreio = kwargs.get('disciplina_rastreio')    

    try:

        print(f"\n    > Início do rastreio das atividades: {disciplina_rastreio}")

        # Mapeia as atividades ativas que aluno possui da disciplina 
        url_mapa_atividades = f"https://studeoapi.unicesumar.edu.br/objeto-ensino-api-controller/api/questionario/disciplina/{cd_shortname_rastreio}/MAPA"
        req_mapa = requests.get(url=url_mapa_atividades, headers=self.headers)
        mapa_atividades = req_mapa.json()
        rol_de_atividades = [limpar_egrad(item) for item in mapa_atividades]
        print("mapppaa", mapa_atividades)
        print("rolll", rol_de_atividades)
        # t(10)

        for atividade in atividades:

            # Verifica se a atividade consta no rol do aluno
            # descricao_atividade = deepcopy(atividade) # Faz cópia para não alterar a atividade
            # limpar_egrad(descricao_atividade)
            print(f"\n     >>> {atividade['descricao']}")
            if atividade['descricao'] in rol_de_atividades:
                print("     >>>> Encontrou a atividade na lista do aluno")
            else:
                print(f"     >>>> A atividade não está presente na lista, segue para a próxima")
                continue

            try:

                if not verificar_data_inicio(
                    atividade['dataInicial'],
                    data_base_str=self.data_base
                ):
                    print(f"     >>> Atividade ainda não disponibilizada no STUDEO {atividade['descricao']}")
                    # False caso a atividade ainda não tenha iniciado
                    continue

                # Obter o JSON de cada atividade individual
                url_atividade = (
                    f"https://studeoapi.unicesumar.edu.br/objeto-ensino-api-controller/api/questao/shortname/"
                    f"{cd_shortname_rastreio}/questionario/{atividade['idQuestionario']}"
                )

                # print(f"url ativv {url_atividade}")
                
                tentativas = 3
                questoes = None
                while tentativas:
                    try:
                        req_relacao_questoes = requests.get(url=url_atividade, headers=self.headers)
                        questoes = req_relacao_questoes.json()
                        if 'errors' in questoes:
                            if "não está matriculado" in questoes['errors'][0]['message']:
                                raise RastreioError
                        
                        req_relacao_questoes.raise_for_status()
                        
                        # Se JSON vier vazio, já pula para a próxima atividade do for
                        if not questoes:
                            msg = f"   >>> JSON vazio para a disciplina: {atividade['descricao']}"
                            log_grava(msg=f"AVISO 9232 \n\n {msg}")
                            break

                        # Se chegou aqui, está tudo ok: sai do while pra processar normalmente
                        break

                    except requests.exceptions.JSONDecodeError:
                        tentativas -= 1
                        if not tentativas:
                            msg = f"   >>> Não foi possível extrair dados da disciplina: {atividade['descricao']}"
                            log_grava(msg=f"ERRO 9231 {req_relacao_questoes.status_code if 'req_relacao_questoes' in locals() else 'SEM_STATUS'} \n\n {msg}")
                            break

                    except requests.exceptions.RequestException as e:
                        tentativas -= 1
                        msg = f"     ❌ Falha de conexão {tentativas} ao tentar acessar: {atividade['descricao']}"
                        print(msg)
                        if not tentativas:
                            log_grava(msg=f"ERRO 9233 \n\n {msg} - Detalhe: {e}\n")
                            if self.config['rastrear_scg'] or self.config['rastrear_ect']:
                                raise RastreioError
                        # t(300)

                    except Exception as e:
                        msg = f"   >>> Erro inesperado para {atividade['descricao']}: {e}"
                        log_grava(msg=f"ERRO 9234 \n\n {msg}")
                        break
                
                # Só prossegue caso tenha certeza que existe um valor válido para questões
                if not questoes:
                    continue

                # O aluno de varredura atual não tem o mesmo questionário que estava salvo no Banco de dados
                if 'errors' in questoes:
                    msg = questoes['errors'][0]['message']
                    if "não está matriculado com a disciplina" in msg:
                        print(f"    >>> Aluno não está matriculado na disciplina atual {disciplina_rastreio}")
                        log_grava(msg=msg)
                        raise RastreioError

                # Garantir que as chaves de atualizar existam, se existirem mantenham o valor
                for chave in ['atualizar_atividade', 'atualizar_livros', 'atualizar_templates']:
                    atividade.setdefault(chave, False)

                for questao in questoes:
                    
                    # Enunciado sem todos os unescapes
                    enunciado=retirar_todos_unescapes(questao['descricaoHtml'])

                    # Verifica se é QUESTIONÁRIO OU DISSERTATIVA
                    atividade['QUESTIONARIO'] = True if questao['alternativaList'] else False

                    # Hash do Enunciado Formatado
                    hash_atividade =  gerar_hash_atividade(enunciado=enunciado,alternativas_dict=None)

                    # Garante que a chave 'QUESTOES' existe
                    atividade.setdefault('QUESTOES', {})

                    # Garante que o subnível do hash existe
                    atividade['QUESTOES'].setdefault(hash_atividade, {})

                    # Agora pode atribuir sem erro: remandar fazer o unescape
                    atividade['QUESTOES'][hash_atividade]['descricaoHtml'] = enunciado

                    # Lista de dict das alternativas contendo Id_Alternativa e descricao
                    alternativas = questao['alternativaList']

                    atividade['QUESTOES'][hash_atividade]['alternativaList'] = html.unescape(alternativas) if alternativas else None

                    if alternativas:
                        
                        gabarito = questao['gabarito'] 

                        # Tratamento para gabarito None
                        # not atividade['QUESTOES'][hash_atividade].get('gabarito') foi colocado 
                        # transitoriamente para guardar os gabaritos e não apagar caso tenha pego antes
                        if not gabarito and not atividade['QUESTOES'][hash_atividade].get('gabarito'):

                            descricao_gabarito = None  # ou 'Gabarito não definido'

                            atividade['QUESTOES'][hash_atividade]['gabarito'] = None

                            atividade['QUESTOES'][hash_atividade]['gabarito_id'] = None

                        else:

                            if gabarito:

                                descricao_gabarito = next(
                                    (alt['descricao'] for alt in alternativas if alt['idAlternativa'] == gabarito['idAlternativa']),
                                    None
                                )

                                atividade['QUESTOES'][hash_atividade]['gabarito'] = descricao_gabarito

                                atividade['QUESTOES'][hash_atividade]['gabarito_id'] = gabarito['idAlternativa']

                        
                        # Gerar hash final da atividade
                        lista_alternativas = questao['alternativaList']

                        if lista_alternativas:
                            alternativas_site = {"alternativas": {str(i):alternativa['descricao'] for i, alternativa in enumerate(lista_alternativas)}}
                        else:
                            alternativas_site=None
                        hash_geral = gerar_hash_atividade(enunciado=enunciado, alternativas_dict=alternativas_site['alternativas'])

                        atividade['QUESTOES'][hash_atividade]['anulada'] = questao['anulada']

                        # Faz a troca do endereço para o hash geral
                        if hash_geral != hash_atividade:

                            atividade['QUESTOES'][hash_geral] = dict(atividade['QUESTOES'][hash_atividade])

                            del(atividade['QUESTOES'][hash_atividade])

                        hash_atividade = hash_geral
                    
                    else:
                        # Informar valores Nulos pois são discurisvas
                        atividade['QUESTOES'][hash_atividade]['gabarito']  = None
                        atividade['QUESTOES'][hash_atividade]['gabarito_id']  = None
                        atividade['QUESTOES'][hash_atividade]['anulada']  = None
                        
            except RastreioError:
                raise RastreioError

            except Exception as err:
                log_grava(err=err)
                
        
        print("    > Finalizou de percorrer todas as atividades")
        
        return
    
    except RastreioError:
        raise RastreioError
    
    except Exception as err:
        log_grava(err=err)
        raise RastreioError
