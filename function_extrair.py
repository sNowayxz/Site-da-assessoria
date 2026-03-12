import os
import traceback
from datetime import datetime
from json.decoder import JSONDecodeError

from bs4 import BeautifulSoup as BS
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from class_papiron.class_error import (
    AlunoNotScrappedError,
    DisciplinaError,
    DisciplinaNotNew,
    DisciplinaScrappedError,
    ScrappedError,
    SenhaError,
    StatusScrappedError,
)
from dados_gerais import LISTA_EXCLUSAO_DISCIPLINAS, LISTA_STATUS_DISCIPLINAS
from function import (
    bd_registrar_atividade,
    disciplina_localiza,
    entra_atividade_script,
    entra_disciplina,
    entra_disciplina_painel,
    escape_html,
    espera_atividades,
    formata_data_disciplina,
    formata_data_fim_atividade,
    listar_atividades,
    listar_atividades_script,
    salva_material_disciplina,
    verifica_aviso,
    verifica_proxima_questao,
)
from system.system import t
from function_bd import abre_json, atualiza_bd, atualiza_bd_scrapped, leitura_dados_rastreamento, salvar_com_releitura, save_json
from system.chrome import (
    atualizar_soup,
    chrome_encerra,
    iniciar_sesssao_chrome,
    login,
    ult_div,
)
from system.logger import log_grava
from function_modulo import extrair_disciplinas_por_modulo
from functions.atividade import alocar_chaves, definir_data_atividades, definir_propriedades_atividade, extrair_dados_basicos, extrair_enunciado, gabarito_atividade, inserir_alternativas_dict, listar_alternativas, salva_tela, salvar_dados_dissertativa, salvar_dados_questionario, salvar_drive_atividade
from functions.rastreio import esperar_carregamento_enunciado
from class_papiron.class_dados_aluno import AlunoScrapped, Disciplina


def scrapped_atividades(self, driver, config:dict, usuario:str, senha:str, curso:dict, modulo:str):
    """
    Prepara para realizar o scrapped dos Portais
    """
    from class_papiron.class_dados_aluno import Aluno

    dt_hoje = datetime.now().__format__('%Y%m%d')
    # Dado de inicial
    driver = None
    
    # Arquivos para ler do Banco de Dados
    # path_file_dia = os.getcwd()+'\\BD\\atividades\\dias_scrapped.json'
    # path_file_dia_aluno = os.getcwd()+'\\BD\\alunos\\dias_scrapped.json'
    
    try:
        # Dados do aluno
        aluno = AlunoScrapped()
        cont = 10

        while cont:
            try:
                [aluno, data_real, data_aluno, data_dia, data_dia_aluno, path_file_curso] = leitura_dados_rastreamento(self, aluno,usuario, curso, modulo,cb_geral=self.config['cb_geral'])
                break
            except JSONDecodeError:
                cont-=1
                t(cont/(11-cont))
                if not cont:
                    raise JSONDecodeError
            # Obtém dados do Aluno

        if not aluno:
            raise AlunoNotScrappedError
        # else:
        #     #Prepara os dados que serão inseridos no BD
        #     nome_aluno = aluno.nome

        # Realiza uma nova sessão
        driver = driver if driver else iniciar_sesssao_chrome(n_thread = self.config['THREAD'])

        # Realiza o login na conta de um novo aluno.
        driver = login(
            driver=driver,
            username=usuario,
            password=senha
        )

        if not driver:
            self.finished.emit()
            raise NoSuchWindowException
        
        # Verificações iniciais de login
        verifica_aviso(driver)

        disciplinas = []
        # Obtém lista dos nomes das disciplinas a rastrear pertencentes ao módulo
        lista_disciplinas_rastrear = extrair_disciplinas_por_modulo(disciplinas=data_aluno[aluno.ra]['DISCIPLINAS'], modulo_alvo=modulo)
        
        lista_exclusao = LISTA_EXCLUSAO_DISCIPLINAS
        for disciplina in lista_disciplinas_rastrear:

            if self.config['cb_scg']:
                # Se estiver marcado o SCG força a inclusão no módulo atual
                disciplinas = [Disciplina("SEMANA DE CONHECIMENTOS GERAIS", modulo, "N/A", None, "NIVELAMENTO")]
                break

            elif not any(palavra in disciplina for palavra in lista_exclusao):
                for disciplina_status in LISTA_STATUS_DISCIPLINAS:
                    try:
                        dt_inicio = data_aluno[aluno.ra]['DISCIPLINAS'][disciplina_status][disciplina]['DT_INICIO']
                        modulo_disciplina = data_aluno[aluno.ra]['DISCIPLINAS'][disciplina_status][disciplina]['MODULO']
                        disciplinas.append(Disciplina(disciplina, modulo_disciplina, dt_inicio, None, disciplina_status)) 
                        print(f"       Disciplina incluída para Rastreamento: {disciplina} - {modulo_disciplina}")
                    except KeyError as err:
                        log_grava(err=err)
            else:
                print(f"       Disciplina na lista de exclusão: {disciplina}")


        print("\n\n   Registrou Aluno:\n     - ", aluno)
        print("\n\n  - Iniciando a extração das atividades atuais")

        # Verifica se existe no arquivo de scrapped diário o curso atual, senão insere
        if not curso[aluno.curso] in data_dia[dt_hoje][modulo]:
            data_dia[dt_hoje][modulo][curso[aluno.curso]]={}
            # save_json(data_dia,path_file_dia)
        

        for disciplina in disciplinas:
            print(f"      - {disciplina.disciplina} - {disciplina.status} - {disciplina.modulo}")

        # Inicia a extração das Atividades, dentro de cada Disciplina
        # Quando for incluir vários módulos, antes deste for deverá conter um "for" 
        # percorrendo a lista de módulos abertos
        for i, disciplina in enumerate(disciplinas):

            print(f"\n\nIniciando {disciplina.disciplina} - {disciplina.status} - {disciplina.modulo}")
            
            #retoma as variáveis iniciais
            data = data_real.copy()
            path_file = path_file_curso            
            aluno.curso = aluno.curso_real
            
            status = disciplina.status

            # Verifica se a disciplina é a mesma do módulo interessado
            # if disciplina.modulo != self.modulo:
            if disciplina.modulo != modulo:
                continue

            # Para incluir o não o ECT na lista geral de disciplinas
            # quando for avaliação, ele deve ficar de fora para rastrear
            # os diferentes cursos, no geral elas são iguais
            if not {self.config['cb_ect']}:

                lista_geral = [
                    "ESTUDO CONTEMPORÂNEO E TRANSVERSAL",
                    "FORMAÇÃO SOCIOCULTURAL E ÉTICA",
                    "SEMANA DE CONHECIMENTOS GERAIS", 
                    "PROJETO DE ENSINO",
                    "NIVELAMENTO DE",
                    "PREPARE-SE",
                    # "GO - "
                ]

            else:
                lista_geral = [
                "SEMANA DE CONHECIMENTOS GERAIS", 
                "PROJETO DE ENSINO",
                "NIVELAMENTO DE",
                "PREPARE-SE",
                # "GO - "
                ]

            # Verifica se a disciplina é das gerais a diversos cursos diferentes
            if any(disciplina_geral in disciplina.disciplina.upper() for disciplina_geral in lista_geral) :

                aluno.curso = "GERAL"
                path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\"+modulo.replace('/','')+'\\bd_papiron_GERAL.json'
                if not os.path.isfile(path_file):
                    data = {"GERAL":{}}
                    save_json(data=data, path_file=path_file)
                else:
                    data = abre_json(path_file=path_file)

                # Verifica se já teve alguma disciplina GERAL rastreada
                if not "GERAL" in data_dia[dt_hoje]:
                    data_dia[dt_hoje]["GERAL"] = {}

                # Como para cada aluno, cada formulário muda, então engloba em 
                # um único dict
                if "SEMANA DE CONHECIMENTOS GERAIS" in disciplina.disciplina.upper():
                    disciplina.disciplina = "SEMANA DE CONHECIMENTOS GERAIS"
                    # Não aparece o módulo para o SCG, por isso forçamos aqui
                    # a princípio, se chegou aqui, já foi incluído o módulo do SCG
                    # disciplina.modulo = self.modulo
                    disciplina.modulo = modulo
                    if not self.config['cb_scg']:
                        print("      > Não rastreou SCG pois está desabilitada o rastreamento.")
                        continue
                
                elif "PROJETO DE ENSINO" in disciplina.disciplina.upper() \
                    or "NIVELAMENTO DE" in disciplina.disciplina.upper()  \
                    or ("GO - " in disciplina.disciplina.upper() and "PROJETO DE VIDA" not in disciplina.disciplina.upper()):
                    
                    # disciplina.modulo = self.modulo
                    disciplina.modulo = modulo
                    modulo_ano = ""
                    if "51" in disciplina.disciplina:
                        modulo_ano = "51"
                    elif "52" in disciplina.disciplina:
                        modulo_ano = "52"
                    elif "53" in disciplina.disciplina:
                        modulo_ano = "53"
                    elif "54" in disciplina.disciplina:
                        modulo_ano = "54"

                    tipo = "Projeto" if "PROJETO DE ENSINO" in disciplina.disciplina.upper() else "Nivelamento" if "NIVELAMENTO" in disciplina.disciplina.upper() else "Atividade GO"
                
                    # if modulo_ano not in self.modulo:
                    if modulo_ano not in modulo:
                        print(f"   >>> {tipo} de outro módulo! - ", disciplina.disciplina )
                        continue


            # Se a disciplina não foi RASTREADA no dia atual, executa!
            # curso atual no caso de realizar as Disciplinas comuns a muitos cursos
            # Como o "ESTUDO CONTEMPORÂNEO E TRANSVERSAL" ou "FSCE"
            # Primeiro verifica se existe o curso no BD do dia de rastreamento:
            try:

                if not curso[aluno.curso] in data_dia[dt_hoje][modulo]:
                    data_dia[dt_hoje][modulo][curso[aluno.curso]] = {}
            except KeyError as err:
                # Como ele pega da WEB por ser que isso esteja em desuso
                print("   ATENÇÃO: Instalação nova? \n     Verificar arquivos de cursos, falta incluir GERAL")
                log_grava(
                    err=err,
                    msg= curso[aluno.curso]+" - "+disciplina.modulo+" - "+disciplina.disciplina
                )
                raise Exception

            if not curso[aluno.curso_real] in data_dia[dt_hoje][modulo]:
                data_dia[dt_hoje][modulo][curso[aluno.curso_real]] = {}
            
            # Depois verifica se a disciplina foi rastreada no dia atual
            if (not disciplina.disciplina in data_dia[dt_hoje][modulo][curso[aluno.curso]] and 
                not disciplina.disciplina in data_dia[dt_hoje][modulo][curso[aluno.curso_real]]):

                try:
                    print(f"       VERIFICA SCG: {config['cb_scg']} - {disciplina.disciplina}", "SEMANA DE CONHECIMENTOS GERAIS" in disciplina.disciplina)
                    if config['cb_scg']:
                        # Se tiver ligado o SCG na GUI, vai ler somente as atividades de SCG
                        if "SEMANA DE CONHECIMENTOS GERAIS" in disciplina.disciplina:
                            # Realiza o scrapped das atividades e material didático
                            # if status != "NIVELAMENTO":
                                # verifica se há SCG registrado se não houver, registra
                                print(disciplina.disciplina not in data[curso[aluno.curso]])
                                if disciplina.disciplina not in data[curso[aluno.curso]]:
                                    data[curso[aluno.curso]][disciplina.disciplina]={}
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo] = {}
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['DT_INICIO']=disciplina.dt_inicio
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO']="NÃO INICIADA"
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'] = {}

                                path_file_scg = os.path.abspath(os.getcwd())+"\\BD\\atividades\\"+modulo.replace('/','')+'\\bd_papiron_SCG.json'
                                # data = abre_json(path_file=path_file_scg)
                                extrai_atividade_SCG(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
                                # salvar_com_releitura(path_file_scg, data, disciplina.disciplina)
                                salvar_com_releitura(path_file, data, disciplina.disciplina)
                                # save_json(data,path_file_scg)

                    else:
                        # Caso a disciplina ainda não esteja no BD
                        if disciplina.disciplina not in data[curso[aluno.curso]]:
                            # Criar disciplina no arquivo de BD do curso
                            if disciplina.modulo == modulo:
                                data[curso[aluno.curso]][disciplina.disciplina] = {}
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]={}
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['DT_INICIO']=disciplina.dt_inicio
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO']="NÃO INICIADA"
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'] = {}
                                
                                # Realiza o scrapped das atividades e material didático 
                                extrair_atividade( self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
                                
                            
                        elif data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO']=="FECHADA":
                            pass
                        
                        elif data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO']=="ABERTA":
                            extrair_atividade(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
                            
                        elif data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO']=="NÃO INICIADA":
                            # Realiza o scrapped das atividades e material didático
                            extrair_atividade(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
                        else:
                            print(" Passando pelo ELSE")
                            pass
                        
                        atualiza_bd_scrapped(
                            modulo = modulo,
                            info = "",
                            curso_sigla = curso[aluno.curso],
                            disciplina = disciplina.disciplina
                        )


                    
                except KeyError as err:
                    """
                    Está redundante com o trecho acima no IF
                    """
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))

                    if disciplina.disciplina == "SEMANA DE CONHECIMENTOS GERAIS":
                        print("SCG - ", disciplina.disciplina , msg)
                    else:
                        print("Disciplina de outro módulo! - ", disciplina.disciplina )
                    
                save_json(data,path_file)
            else:
                print(f"   >>> Disciplina {disciplina} já feito scrapped hoje para este curso!")

        # Atualiza o BD informando que rastreio foi concluído
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "RASTREADO",
            ra = aluno.ra
        )

        print(f"\n     >>>>>> Finalizado o rastreio do [{modulo}] do Aluno: {aluno.nome} - {aluno.curso}  <<<<<<<<<<\n\n")
          
    except  AlunoNotScrappedError as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "ERRO NO ALUNO",
            ra = aluno.ra
        )

        log_grava(
            err=err,
            msg=modulo+" - "+aluno.ra
        )

    except StatusScrappedError as err:
        print(f" >> {aluno.nome} - Já realizou o rastreio para este Aluno [{modulo}]\n")
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "RASTREIO ANTERIOR",
            ra = aluno.ra
        )

    except DisciplinaScrappedError as err:
        print("        >> Não há novas disciplinas a serem rastreadas")
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "SEM NOVAS DISCIPLINAS",
            ra = aluno.ra
        )

    except SenhaError as err:
        msg = str(err)
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "FALHA DE LOGIN",
            ra = aluno.ra
        )
        
        driver = chrome_encerra(driver)
        return None

    except KeyError as err:
        log_grava(err=err)
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "KeyError",
            ra = aluno.ra
        )
    
    except NoSuchWindowException as err:

        # Grava no LOG o erro
        msg = "Falha ao abrir o Chrome"
        log_grava(
            err=err,
            msg=msg
        )

        atualiza_bd_scrapped(
            modulo = modulo,
            info = "NoSuchWindowException",
            ra = aluno.ra
        )

        driver = chrome_encerra(driver)
        return None
    
    except JSONDecodeError as err:
        log_grava(err=err)
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "JSONDecodeError",
            ra = aluno.ra
        )
    
    except DisciplinaNotNew as err:
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "Sem Disciplinas no módulo",
            ra = aluno.ra
        )
    
    except Exception as err:
        log_grava(err=err)
        atualiza_bd_scrapped(
            modulo = modulo,
            info = "Exception: ler Log",
            ra = aluno.ra
        )
    
    # driver = chrome_encerra(driver)
    return driver if driver else None

def extrair_atividade(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso):
    
    print(f"   Iniciar a extração: {disciplina.disciplina} - {disciplina.status} ")

    if  disciplina.disciplina == "SEMANA DE CONHECIMENTOS GERAIS":
        print("   >> SEMANA DE CONHECIMENTOS GERAIS >>  " , disciplina.disciplina)
        # extrai_atividade_SCG(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
        extrai_atividade_curricular(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)

        return None
    
    elif  "PROJETO DE ENSINO" in disciplina.disciplina.upper()  or\
        "NIVELAMENTO DE" in disciplina.disciplina.upper()       or\
        "GO - " in disciplina.disciplina.upper()                or\
        "PREPARE-SE" in disciplina.disciplina.upper():
        
        if  "PROJETO DE ENSINO" in disciplina.disciplina.upper():
            print("   >> PROJETO DE ENSINO")
        elif "NIVELAMENTO DE" in disciplina.disciplina.upper():
            print("   >> NIVELAMENTO")
        elif "GO - " in disciplina.disciplina.upper():
            print("   >> Atividade GO")
        elif "PREPARE-SE" in disciplina.disciplina.upper():
            print("   >> Atividade PREPARA-SE")

        if not self.config['cb_geral']:
            print("A opção de rastrear ATIVIDADES GERAIS está desabilitada.")
            return None

        extrai_atividade_curricular(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
        # extrai_atividade_projeto(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)

    else:
        print("   >> CURRICULAR")
        extrai_atividade_curricular(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso)
       
def extrai_atividade_curricular(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso):

    cont_n = 2
    while cont_n:
        try:

            print("   >> Iniciando a coleta em",disciplina,status)

            cont_acessa=3
            while cont_acessa:
                try:
                    # Entra no painel do tipo da disciplina
                    disc_lista = disciplina_localiza(driver, disciplina)
                    if not disc_lista:
                        print("   > Não localizou, mas vai tentar clicar")
                    t(5)

                    # Entra pela lista de disciplinas gerais
                    print("   > Entra na disciplina pelo painel de Disciplinas")
                    entra_disciplina_painel(driver,disciplina)

                    # Formata a data de início e fim de Modulo
                    dt_inicio = formata_data_disciplina(data, data_aluno, aluno, curso, disciplina)
                    if not dt_inicio:
                        raise AlunoNotScrappedError
                    
                    # Aguarda a página de ATIVIDADES carregar
                    espera_atividades(driver=driver,disciplina=disciplina)
                    print("   > Entrou no painel da disciplina")

                    break
                
                except Exception as err:
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    print("Falhou em acessar o painel de Atividades ,"+str(cont_acessa) + "\n\n"+msg)
                    cont_acessa -= 1
                    if not cont_acessa:
                        print("Falhou em acessar o painel de Atividades COMPLETAMENTE:", disciplina.disciplina)
                        raise DisciplinaError

            # Irá fazer se Data Atual for maior que a data de Início da DISCICPLINA
            if  datetime.now()>dt_inicio:

                # Verifica se quer baixar: Templates, Livros, etc
                if config['cb_material_atualizar']:
                    print("      >> Procurando por materiais a serem extraídos")
                    salva_material_disciplina(driver, aluno.curso, disciplina.disciplina, disciplina.modulo, config)
                else:
                    print("      >> A Opção de baixar material está desabilitada.")

                # Extrai a lista de Atividades da disciplina
                espera_atividades(driver = driver , disciplina = disciplina)
                lista_de_atividades = listar_atividades(self, driver , disciplina)
                if not lista_de_atividades:
                    # Não foi possível acessar a lista do painel de atividades
                    raise DisciplinaError
                
                for j, lista_ativ in enumerate(lista_de_atividades):

                    # Formata a atividade para ficar legível
                    atividade = escape_html(lista_de_atividades[j].text)

                    # Verifica se deve percorrer a atividade
                    deve_percorrer = False

                    if not self.config['cb_ect']:
                        deve_percorrer = True

                    elif ("ESTUDO CONTEMPORÂNEO E TRANSVERSAL" in disciplina.disciplina or 
                        "FORMAÇÃO SOCIOCULTURAL E ÉTICA" in disciplina.disciplina) and atividade == "AV":
                        deve_percorrer = True
                        # atividade = atividade+"_"+curso[aluno.curso]

                    # Executa ou continua
                    if deve_percorrer:

                        # Aguarda novamente a página de ATIVIDADES carregar, para o looping
                        espera_atividades(driver = driver , disciplina = disciplina)

                        # Atualiza os elementos webdriver
                        ativ_script = listar_atividades_script(driver = driver)

                        # Caso tenha mais de uma atividade com o mesmo nome!
                        if list(atividade == verifica_atividade for verifica_atividade in lista_de_atividades).count(True)>1: 
                            atividade = atividade+" "+str(j+1)
                            print("       >>> Renumera atividade:", atividade)

                        dt_fim = formata_data_fim_atividade(data, aluno , disciplina , curso , atividade)

                        registro_bd = bd_registrar_atividade(data, aluno , curso , disciplina , atividade , dt_fim )
                        if registro_bd == "continue":
                            # Se a atividade já foi registrada no BD, segue-se para a seguinte
                            continue

                        # Acessa a atividade do looping
                        print(f'\n                   - Acessando a Atividade({j+1}/{len(lista_de_atividades)}):',atividade, disciplina.disciplina)
                
                        if not entra_atividade_script(driver, ativ_script[j]):
                            # Caso dê erro ao identificar a Atividade, volta para a página
                            # anterior de todas as atividades e continua na próxima atividade.
                            continue

                        percorre_atividade(
                            self,
                            driver,
                            data,
                            aluno=aluno,
                            curso=curso,
                            disciplina=disciplina,
                            atividade=atividade
                            )
                    else:
                        continue 

            else:
                # Então ainda não se iniciou o peródio avaliativo da ATIVIDADE
                print("                   - Acessando a Atividade: ",disciplina.disciplina)
                print("                      >> Não iniciou o período avaliativo da Atividade")

            break

        except DisciplinaError:
            cont_n -= 1
        
        except ScrappedError:
            cont_n -= 1

        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            log_grava(msg=msg)
            print(msg+str(cont_n))
            cont_n -= 1

def extrai_atividade_projeto(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso):
    print("     INICIOU PROJETOS")
    cont_n = 2

    # if "PREPARE-SE" in disciplina.disciplina.upper():
    #     print("    >> Disciplina prepare-se, pulou")
    #     return None
    
    if not self.config['cb_geral']:
        print("A opção de rastrear ATIVIDADES COMPLEMENTARES está desabilitada.")
        return None

    while cont_n:
        try:
            print(f"      >>> Iniciando a coleta em {disciplina} - {status} - {self.modulo}")
            # print(f"      >>> Iniciando a coleta em {disciplina} - {status} - {modulo}")
            # progresso_lista(self,"   Iniciando a coleta em: "+disciplina.disciplina)

            cont_acessa  = 3
            while cont_acessa:
                try:
                    # Entra no painel do tipo da disciplina
                    # painel_disciplinas(driver,status)
                    disc_lista = disciplina_localiza(driver, disciplina)
                    if not disc_lista:
                        raise DisciplinaError

                    # Entra no painel da disciplina
                    entra_disciplina_painel(driver,disciplina)

                    # Aguarda a página de ATIVIDADES carregar
                    espera_atividades(driver = driver , disciplina = disciplina)

                    break
                
                except Exception as err:
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    print("Falhou em acessar o painel de Atividades ,"+str(cont_acessa) + "\n\n"+msg)
                    cont_acessa -= 1
                    if not cont_acessa:
                        print("Falhou em acessar o painel de Atividades COMPLETAMENTE:", disciplina.disciplina)
                        raise DisciplinaError

            # Extrai a lista de Atividades da disciplina
            espera_atividades(driver = driver , disciplina = disciplina)
            lista_de_atividades = listar_atividades(self, driver , disciplina)
            if not lista_de_atividades:
                # Não foi possível acessar a lista do painel de atividades
                raise DisciplinaError
            
            for j, lista_ativ in enumerate(lista_de_atividades):
                atividade = escape_html(lista_de_atividades[j].text)

                # Aguarda novamente a página de ATIVIDADES carregar, para o looping
                espera_atividades(driver = driver , disciplina = disciplina)

                # Atualiza os elementos webdriver
                ativ_script = listar_atividades_script(driver = driver)

                print(list(lista_ativ == verifica_atividade for verifica_atividade in lista_de_atividades) , list(lista_ativ == verifica_atividade for verifica_atividade in lista_de_atividades).count(True))
                renumera = False
                if list(lista_ativ == verifica_atividade for verifica_atividade in lista_de_atividades).count(True)>1: 
                    atividade = atividade+" "+str(j+1)
                    print("       >>> Renumera atividade:", atividade)
                    renumera = True

                
                dt_fim = formata_data_fim_atividade(data, aluno , disciplina , curso , atividade)

                registro_bd = bd_registrar_atividade(data, aluno , curso , disciplina , atividade , dt_fim = dt_fim )
                


                # ARRUMAR AQUI TIREI PROVISÓRIO
                if registro_bd == "continue":
                    # Se a atividade já foi registrada no BD, segue-se para a seguinte
                    # pass
                    continue
                    
                

                # Acessa a atividade do looping
                print(f'\n                   - Acessando a Atividade({j+1}/{len(lista_de_atividades)}):',atividade, disciplina.disciplina)
        
                print("          == Prepara para entrar na Atividade ==")
                if not entra_atividade_script(driver, ativ_script[j]):
                        # Caso dê erro ao identificar a Atividade, volta para a página
                        # anterior de todas as atividades e continua na próxima atividade.
                        continue
                
                print(f"          == Entrou na Atividade == {atividade}")
                
                percorre_atividade(
                    self,
                    driver,
                    data, 
                    aluno=aluno,
                    curso=curso,
                    disciplina=disciplina,
                    atividade=atividade,
                    renumera=renumera              
                )                        

            break

        except DisciplinaError as err:
            log_grava(err=err)
            cont_n -= 1
        
        except ScrappedError as err:
            log_grava(err=err)
            cont_n -= 1

        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            log_grava(msg=msg)
            print(msg+str(cont_n))
            cont_n -= 1

def extrai_atividade_SCG(self, config, data, data_dia, data_aluno, aluno, disciplina, driver, status, curso):

    cont_n = 2
    while cont_n:
        try:
            print("      >>> Iniciando a coleta de SCG em",disciplina.disciplina,status)
            # progresso_lista(self,"   Iniciando a coleta em: "+disciplina.disciplina)

            cont_acessa=3
            while cont_acessa:
                try:
                    # Entra no painel do tipo da disciplina
                    disc_lista = disciplina_localiza(driver,disciplina)
                    if not disc_lista:
                        raise DisciplinaError
                    
                    # Entra no painel da disciplina
                    entra_disciplina(driver,disciplina)
                    
                    # Aguarda a página de ATIVIDADES carregar
                    espera_atividades(driver=driver,disciplina=disciplina)

                    break
                
                except Exception as err:
                    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    print("Falhou em acessar o painel de Atividades ,"+str(cont_acessa) + "\n\n"+msg)
                    cont_acessa -= 1
                    if not cont_acessa:
                        print("Falhou em acessar o painel de Atividades COMPLETAMENTE:", disciplina.disciplina)
                        raise DisciplinaError

            # Irá fazer se Data Atual for maior que a data de Início da DISCICPLINA
            # if  datetime.now()>dt_inicio:

            # Extrai a lista de Atividades da disciplina
            espera_atividades(driver=driver,disciplina=disciplina)
            lista_de_atividades = listar_atividades(self,driver,disciplina)
            if not lista_de_atividades:
                # Não foi possível acessar a lista do painel de atividades
                raise DisciplinaError
                

            for j, lista_ativ in enumerate(lista_de_atividades):
                atividade = escape_html(lista_de_atividades[j].text)

                # Aguarda novamente a página de ATIVIDADES carregar, para o looping
                espera_atividades(driver = driver , disciplina = disciplina)

                # Atualiza os elementos webdriver
                ativ_script = listar_atividades_script(driver = driver)

                if list(atividade == verifica_atividade for verifica_atividade in lista_de_atividades).count(True)>1: 
                    atividade = atividade+" "+str(j+1)
                    print("       >>> Renumera atividade:", atividade)

                if not entra_atividade_script(driver, ativ_script[j]):
                        # Caso dê erro ao identificar a Atividade, volta para a página
                        # anterior de todas as atividades e continua na próxima atividade.
                        continue

                dt_fim = formata_data_fim_atividade(data, aluno , disciplina , curso , atividade)

                registro_bd = bd_registrar_atividade(data, aluno , curso , disciplina , atividade , dt_fim = dt_fim )


                # percorre_atividade_SCG(
                #     driver,
                #     data, 
                #     aluno=aluno,
                #     curso=curso,
                #     disciplina=disciplina,
                #     atividade=atividade                  
                # )               

                percorre_atividade(
                            self,
                            driver,
                            data,
                            aluno=aluno,
                            curso=curso,
                            disciplina=disciplina,
                            atividade=atividade
                            )         

            break

        except DisciplinaError as err:
            log_grava(err=err)
            cont_n -= 1
        
        except ScrappedError as err:
            log_grava(err=err)
            cont_n -= 1

        except Exception as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            log_grava(msg=msg)
            print(msg+str(cont_n))
            cont_n -= 1

def percorre_atividade(self, driver, data,**kwargs):

    try:
        # Obtém o valor das variáveis
        aluno = kwargs.get("aluno", None)
        curso = kwargs.get("curso", None)
        disciplina = kwargs.get("disciplina", None)
        atividade = kwargs.get("atividade", None)
        renumera = kwargs.get("renumera", None)

        # Seta a dict
        chave_modulo= data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO']
        chave_data = data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]

        print(f"    >> Começou a percorrer as questões da atividade: {atividade} - {curso[aluno.curso]} - {[disciplina.disciplina]}")

        # Aguarda o cabeçalho ficar pronto
        css_questao = "#cabecalhoQuestao > div.panel-body.p-t-20.b-t.b-grey"
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_questao)))
        
        proxima_questao = "continua"
        k=0
        cont_geral=2
        while proxima_questao:
            # Percorre os enunciados da ATIVIDADE
            try:
                # Extrai informações do enunciado!
                enunciado, titulo, hash_questao, lista_alternativas_div, alternativas, questionario = extrair_dados_basicos(driver)

                
                # path_file_scg = os.path.abspath(os.getcwd())+"\\BD\\atividades\\"+disciplina.modulo.replace('/','')+'\\bd_papiron_SCG1.json'
                # save_json(data,path_file_scg)
                
                # Corrige certos problemas de demora de carregamento de enunciado
                esperar_carregamento_enunciado(driver,enunciado)

                soup = atualizar_soup(driver) 
      
                if enunciado.text:
                    
                    # Fomata as datas
                    hoje, dt_inicio_atividade, dt_fim_atividade, dt_gabarito = definir_data_atividades(self, driver, questionario)

                    # Verifica se a atividade está no prazo Ativo
                    atividade_ativa = True if dt_inicio_atividade <= hoje <= dt_fim_atividade else False
                    atividade_liberada = True

                    # Insere no BD chave dos dados
                    alocar_chaves(chave_data, hash_questao, questionario,dt_inicio_atividade,dt_fim_atividade)
                    
                    if questionario:
                
                        # Confere se a questão foi anulada                
                        verifica_questao_anulada = soup.find("span",{"class":"label label-danger all-caps pull-right m-r-20"})

                        if verifica_questao_anulada:
                            alternativa_correta = "QUESTÃO ANULADA!"
                            gabarito_site = None
                        else:
                            alternativa_correta, gabarito_site = gabarito_atividade(
                                aluno,
                                curso,
                                disciplina,
                                soup,
                                enunciado,
                                atividade,
                                hash_questao,
                                lista_alternativas_div
                            )               
                    
                    if  dt_fim_atividade>=hoje:
                        data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['DT_FIM'] = soup.find("span",{"ng-bind":"vm.questionario.dataFinal | serverDate:'dd/MM/yyyy HH:mm'"}).text[:10]

                    # Verifica o ESTILO de Atividade
                    if questionario:  

                        salvar_dados_questionario(chave_data, hash_questao, enunciado, titulo, alternativas, alternativa_correta, gabarito_site)            

                        definir_propriedades_atividade(
                            soup,
                            chave_data,
                            chave_modulo,
                            hash_questao,
                            verifica_questao_anulada,
                            alternativa_correta,
                            dt_gabarito,
                            hoje
                        )

                        proxima_questao = verifica_proxima_questao(driver,soup)
                        print("               >> Atividade de questionário gravada <<\n")

                        if not proxima_questao and alternativa_correta:
                            # Se houver alternativa correta, significa que a ATIVIDADE de querstionário foi avaliada e finalizada
                            chave_data['STATUS_ATIVIDADE'] = "FECHADA"

                    else:
                        # Atividade Dissertativa
                        salvar_dados_dissertativa(chave_data, hash_questao, enunciado, titulo)

                        # Casos nunca vistos de atividade dissertativa ter mais de uma questão
                        proxima_questao=verifica_proxima_questao(driver,soup)

                    if k==0 and atividade_ativa:
                        # No primeiro looping salva a atividade completa no drive
                        salvar_drive_atividade(
                            driver,
                            aluno,
                            curso,
                            disciplina,
                            atividade,
                            titulo,
                            questionario,
                        )
                            
                else:
                    # Se não tiver enunciado, significa que a questão não foi liberada, pode sair do WHILE e ir para a próxima atividade
                    print("           >> Atividade não liberada <<")
                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO'] = "NÃO INICIADA"
                    proxima_questao = None
                    atividade_liberada = False

            except Exception as err:
                msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+" - "+aluno.curso+" - "+disciplina.disciplina+" - "+atividade
                print(msg)
                log_grava(msg=msg)
                if cont_geral:
                    cont_geral=-1
                    driver.refresh()
                    verifica_aviso(driver=driver)
                else:
                    break

            # último comando While
            k+=1 # Finalizou, passa para o Gabarito da próxima questão
        

            path_file_scg = os.path.abspath(os.getcwd())+"\\BD\\atividades\\"+disciplina.modulo.replace('/','')+'\\bd_papiron_SCG2.json'
            save_json(data,path_file_scg)

        
        # Fora do while, salva o que tem para salvar
        if atividade_liberada:
            salva_tela(
                driver,
                aluno.curso,
                disciplina.disciplina,
                atividade,
                questionario,
                disciplina.modulo,
                titulo=titulo,
                renumera=renumera, 
                atividade_ativa=atividade_ativa,
                data=data,
                )

                
    except TimeoutException:
        print("            >> Passa a próxima Atividade, por falha")
    
    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(msg)
        log_grava(msg=msg)

    # Volta para a página de todas as ATIVIDADES
    # print("clicou para voltar uma página")
    driver.back()
    t(3)

def percorre_atividade_SCG(driver, data,**kwargs):

    aluno = kwargs.get("aluno", None)
    curso = kwargs.get("curso", None)
    disciplina = kwargs.get("disciplina", None)
    atividade = kwargs.get("atividade", None)

    lista_enunciados_html, lista_alternativas_html = [],[]

    try:
        css_questao = "#cabecalhoQuestao > div.panel-body.p-t-20.b-t.b-grey"
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_questao)))
        
        k=0
        # Enquanto houver questões para obter dados
        proxima_questao = "continua"
        while proxima_questao:

            # Percorre os enunciados da ATIVIDADE 
            # Realiza o Scrapped do ENUNCIADO

            ult_div(driver)
            soup = atualizar_soup(driver)
            
            # Extrai informações do enunciado!
            css_enunciado = "#cabecalhoQuestao > div.panel-body.p-t-20.b-t.b-grey > div.enunciado.ng-binding"                
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR,css_enunciado)))
            soup = atualizar_soup(driver)
            enunciado =  soup.find('div',{"class":"enunciado ng-binding"})
            
            # Corrige certos problemas de demora de carregamento de 
            # enunciado
            delta_t = 0.1
            T = 6
            # Se deixar apenas T, ele pode entrar em loopíng infinito
            # pois pode nunca chegar a zero!
            while T>0 and not enunciado.text:
                soup = atualizar_soup(driver)
                enunciado =  soup.find('div',{"class":"enunciado ng-binding"})
                t(delta_t)
                T -= delta_t

            # Poderia colocar dentro do próximo bloco, mas
            # posso utilizar a informação da questão mais adiante
            questao_n = escape_html(soup.find('div',{"class":"panel-title cursor ng-binding","ng-bind":"'Questão ' + vm.questaoAtual.ordem"}).text)
        
            if enunciado.text:

                #Extrai o título
                titulo_soup = soup.find('div',{"ng-bind":"vm.questionario.descricao"})
                titulo = titulo_soup.text

                # Listas as alternativas se a questão for do tipo QUESTIONÁRIO
                lista_alternativas = soup.find_all('label',{"ng-repeat":"alternativa in vm.questaoAtual.alternativaList track by alternativa.idAlternativa"})

                # Extrai o gabarito, se houver
                lista_gabarito = soup.find_all('tr',{"style":"background-color: rgb(202, 220, 251);"})
            
                # print("\n                       Iniciou a leitura do enunciado")
                print(f"                         - Extraindo a  {questao_n} - {curso[aluno.curso]} - {[disciplina.disciplina]}")
                
                # Cria um dict para acolher os dados da questão
                # Se tiver alternativas, trata-se questionário, senão atividade dissertativa
                # Se tem enunciado questão aberta
                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE'] = "ABERTA"

                # Fomata a data obtida na atividade
                dt_inicio_atividade =   datetime.strptime(soup.find("span",{"ng-bind":"vm.questionario.dataInicial | serverDate:'dd/MM/yyyy HH:mm'"}).text[:10],'%d/%m/%Y')
                dt_fim_atividade    =   datetime.strptime(soup.find("span",{"ng-bind":"vm.questionario.dataFinal | serverDate:'dd/MM/yyyy HH:mm'"}).text[:10],'%d/%m/%Y')
                
                # Insere as informações de prazo limite no BD
                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['DT_INICIO'] = dt_inicio_atividade.strftime('%Y-%m-%d')
                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['DT_FIM'] = dt_fim_atividade .strftime('%Y-%m-%d')
                
                verifica_questoes = data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]
                num_questoes = len(verifica_questoes) - 4
                print(f"                      >>>  Número de questões atuais: {num_questoes}")
                encontrou_questao = False
                for verifica_questao in verifica_questoes:
                    if "QUESTÃO" in verifica_questao.upper():
                        # print(f"       COMPARA QUESTÃO: {verifica_questao.upper()}")
                        # Primeiro verifica se encontra algum ENUNCIADO igual                                                                                                                                                                              
                        if  escape_html(enunciado) == verifica_questoes[verifica_questao]['ENUNCIADO']:
                            print(f"\n\n       ACHOU QUESTÃO PARA COMPARAR: {verifica_questao.upper()}")
                            # Obtém todas as alternativas do Enunciado idêntico
                            verifica_questao_alternativas = verifica_questoes[verifica_questao]['ALTERNATIVAS']
                            print(f"       ALTERNATIVAS do Banco : {verifica_questao_alternativas}")
                            # Registra a primeira alternativa do rastreamento
                            primeira_alternativa = escape_html(lista_alternativas[0].text)
                            print(f"       ALTERNATIVAS Paradigma: {verifica_questao_alternativas}")

                            for verifica_questao_alternativa in verifica_questao_alternativas:
                                if verifica_questao_alternativas[verifica_questao_alternativa] == primeira_alternativa:
                                    questao_n = verifica_questao
                                    encontrou_questao = True
                                    print("     >> Achou", questao_n)
                                    break
                            if encontrou_questao:
                                break
                if not encontrou_questao:
                    num_questoes = len(verifica_questoes) - 3
                    questao_n = "Questão "+str(num_questoes)
                    print("\n                   >> Não achou", questao_n)
                

                # Verifica se a questão já não está gravada (para não apagar os dados já coletados anteriormente)
                if questao_n not in data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]:

                    # Aloca o espaço para receber as Questões da Atividade
                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]={}

                    # Insere a key [ID_URL]
                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['ID_URL'] = None
                
                if  dt_fim_atividade >=datetime.now():
                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['DT_FIM'] = soup.find("span",{"ng-bind":"vm.questionario.dataFinal | serverDate:'dd/MM/yyyy HH:mm'"}).text[:10]

                # setando questionario igual a True, pq SCG sempre vai ser
                    questionario=True
                
                # Verifica o ESTILO de Atividade
                if questionario:
                    # Se tem alternativas é do ESTILO questionário
                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['ESTILO']="QUESTIONARIO"
                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['ALTERNATIVAS'] = {}
                    
                    # Realiza o Scrapped das Alternativas
                    for m, alternativa in enumerate(lista_alternativas):
                        data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['ALTERNATIVAS'][m] = escape_html(alternativa.text)
                        status_atividade = soup.find("span",{"ng-show":"vm.questionario.notaAluno == null || vm.questionario.notaAluno == undefined"}).text
                        finalizada_atividade = soup.find("p",{"class":"ng-binding","ng-bind":"vm.questionario.situacao.descricao"}).text
                        verifica_questao_anulada = soup.find("span",{"class":"label label-danger all-caps pull-right m-r-20"})

                        if finalizada_atividade == "ENCERRADO":  ## if no lugar certo???
                            if verifica_questao_anulada: # se tem alguma informação, significa QUESTÃO ANULADA
                                alternativa_correta = "QUESTÃO ANULADA!"
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['STATUS_QUESTAO'] = "FECHADA"
                                
                            elif status_atividade == 'Não avaliado, aguarde a correção.':
                                # Verifica se é possível obter o gabarito, mesmo sem correção
                                try:
                                    # O item abaixo irá retornar erro se não tiver respostas, pois não haverá index registrado para o Elemento
                                    alternativa_correta = escape_html(lista_gabarito[k].text)
                                    
                                except IndexError:
                                    # Ainda nem com nota nem gabarito liberados
                                    alternativa_correta = None
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO'] = "ABERTA" 
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['STATUS_QUESTAO'] = "ABERTA"
                            else:
                                # Gabarito e notas liberados
                                alternativa_correta = escape_html(lista_gabarito[k].text)
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['STATUS_QUESTAO'] = "FECHADA"
                                
                                verifica_questoes = data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]
                                encerrou_atividade = False
                                for verifica_questao in verifica_questoes:
                                    if "QUESTÃO" in verifica_questao.upper():
                                        if data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][verifica_questao]['STATUS_QUESTAO'] != "FECHADA":
                                            encerrou_atividade = True
                                            break
                                
                                if encerrou_atividade and num_questoes>70:
                                    data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE']=="FECHADA"

                        else:
                            # Atividade ainda não encerrada
                            alternativa_correta = None
                            data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['STATUS_QUESTAO'] = "ABERTA"
                        
                        # Grava dados no banco de dados
                        data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['ENUNCIADO']=escape_html(enunciado)
                        data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['TITULO'] = titulo
                        data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][questao_n]['GABARITO']=alternativa_correta
                        
                    proxima_questao = verifica_proxima_questao(driver,soup)
                    print("                          >> Atividade de questionário gravada")

                    if not proxima_questao:

                        # Refaz arquivo HTML e PDF
                        lista_enunciados_html , lista_enunciados_html , lista_gabaritos_html = [] , [] , []

                        verifica_questoes = data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]
                        for verifica_questao in verifica_questoes:
                            if "QUESTÃO" in verifica_questao.upper():
                                lista_enunciados_html.append(data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][verifica_questao]['ENUNCIADO'])
                                
                                lista_alternativas = []
                                alternativas = data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][verifica_questao]['ALTERNATIVAS']
                                for alternativa in alternativas:
                                    lista_alternativas.append(data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][verifica_questao]['ALTERNATIVAS'][alternativa])
                                lista_alternativas_html.append(lista_alternativas)
                                
                                lista_gabaritos_html.append(data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade][verifica_questao]['GABARITO'])

                        # salva_tela(driver, 
                        #     aluno.curso,
                        #     disciplina.disciplina,
                        #     atividade,
                        #     questionario,
                        #     disciplina.modulo,
                        #     lista_enunciados_html,
                        #     lista_alternativas_html,
                        #     gabarito=lista_gabaritos_html
                        # )

                        salva_tela(
                            driver,
                            aluno.curso,
                            disciplina.disciplina,
                            atividade,
                            questionario,
                            disciplina.modulo,
                            lista_enunciados_html,
                            lista_alternativas_html,
                            # gabarito=lista_gabaritos,
                            titulo=titulo,
                            # renumera=renumera, 
                            # atividade_ativa=atividade_ativa,
                            data=data,
                        )




                        lista_enunciados_html = []
                        lista_alternativas_html = []
                        lista_gabaritos_html = []
                        # Se houver alternativa correta, significa que a ATIVIDADE de querstionário foi avaliada e finalizada
                        if  alternativa_correta:
                            if num_questoes>20:
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['ATIVIDADE'][atividade]['STATUS_ATIVIDADE'] = "FECHADA"
                                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO'] = "FECHADA" 
                        
            else:
                # Se não tiver enunciado, significa que a questão não foi liberada, pode sair do WHILE e ir para a próxima atividade
                print("                          >> Atividade não liberada")
                data[curso[aluno.curso]][disciplina.disciplina][disciplina.modulo]['STATUS_MODULO'] = "NÃO INICIADA"
                proxima_questao = None
            
            k+=1 # Finalizou, passa para o Gabarito da próxima questão

    except TimeoutException as err:
        print("                       Passa a próxima Atividade, por falha")
        log_grava(
            err=err,
            msg= curso[aluno.curso]+" - "+disciplina.modulo+" - "+disciplina.disciplina+" - "+atividade
        )

    # Volta para a página de todas as ATIVIDADES
    driver.back()
    t(3)


