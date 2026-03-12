import json
import os
import random
import traceback
import time
import logging
import threading

from json import JSONDecodeError

from class_papiron.class_error import DisciplinaNotNew, DisciplinaScrappedError, StatusAlunoError, StatusScrappedError
from dados_gerais import LISTA_EXCLUSAO_DISCIPLINAS, LISTA_GERAL_DISCIPLINAS, LISTA_STATUS_DISCIPLINAS
from functions.curso import dict_curso
from function_error import imprimir_erro
from system.logger import log_grava
from function_modulo import extrair_disciplinas_por_modulo
from system.pastas import verifica_pastas



# Lock global da thread, assim evita que mais de uma Thread acesse o arquivo
json_lock = threading.Lock()

def leitura_de_contas(path_file):
    
    with open(path_file, 'r', encoding='utf-8') as arquivo:
        contas = arquivo.readlines()
    
    dict_de_contas = {}
    try:
        for conta in contas:
            if "\tOK\t" in conta:
                user = conta.split("\tOK\t").__getitem__(0)
                dict_de_contas[user] = {}
                password = conta.split("\tOK\t").__getitem__(1).replace("\n","")
                dict_de_contas[user]['RA'] = user
                dict_de_contas[user]['password'] = password
                try:
                    nome = conta.split("\tOK\t").__getitem__(2).replace("\n","")
                    dict_de_contas[user]['nome'] = nome
                except IndexError:
                    dict_de_contas[user]['nome'] = "Não possui nome do ARQUIVO"
            else:
                user = conta.split("\t").__getitem__(0)
                dict_de_contas[user] = {}
                password = conta.split("\t").__getitem__(1).replace("\n","")
                dict_de_contas[user]['RA'] = user
                dict_de_contas[user]['password'] = password
                try:
                    nome = conta.split("\t").__getitem__(2).replace("\n","")
                    dict_de_contas[user]['nome'] = nome
                except IndexError:
                    dict_de_contas[user]['nome'] = "Não possui nome do ARQUIVO"


            print(f"    Inserido para leitura!: {dict_de_contas[user]['RA']} - {dict_de_contas[user]['password']} - {dict_de_contas[user]['nome']}  ")
    except IndexError:
        print(f"   Há erro na linha: {conta}")
        raise IndexError
    
    return dict_de_contas

def merge_dicts(a, b):
    for date, data in b.items():
        if date in a:
            # Se a data já existe em 'a', mescla os valores das chaves
            a[date].update(data)
        else:
            # Se a data não existe em 'a', simplesmente adiciona o novo dado
            a[date] = data

    return a

# def abre_json(path_file:str) -> dict:

#     # Cria diretório se não existir
#     os.makedirs(os.path.dirname(path_file), exist_ok=True)

#     if os.path.isfile(path=path_file):
#         try:
#             with open(path_file, encoding='utf-8') as json_file:
#                 data = json.load(json_file)
#             return data
        
#         except UnicodeDecodeError:

#             try:
#                 # Quando o arquivo foi salvo em UTF-8 com BOM.
#                 with open(path_file, 'r', encoding='utf-8-sig') as json_file:
#                     data = json.load(json_file)

#             except UnicodeDecodeError:
#                 # Arquivos vindos de Windows, Word, Excel antigos.
#                 with open(path_file, 'r', encoding='latin1') as json_file:
#                     data = json.load(json_file)

#     else:
#         data = {}
#         with open(path_file, 'w', encoding='utf-8') as json_file:
#             json.dump(data, json_file ,ensure_ascii=False)
#         return data

# def save_json(data, path_file):
    path_temp = path_file[:-5] + "TEMP.json"  # substitui ".json" por "TEMP.json"
    cont = 5

    while cont:
        try:
            
            # Salva no arquivo temporário
            with open(path_temp, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
                json_file.flush()
                os.fsync(json_file.fileno())  # garante escrita no disco

            try: 
                # Tenta ler de volta para verificar consistência
                with open(path_temp, encoding='utf-8') as json_file:
                    _ = json.load(json_file)
            except UnicodeDecodeError:
                # Tente com ISO-8859-1
                with open(path_temp, ncoding='iso-8859-1') as json_file:
                    _ = json.load(json_file)

            # Substitui o arquivo original
            with open(path_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())

            # Remove TEMP com lock ativo
            try:
                os.remove(path_temp)
            except FileNotFoundError:
                logging.warning("Arquivo TEMP já havia sido deletado.")
            except PermissionError:
                logging.warning("Arquivo TEMP em uso, não foi possível deletar.")
            break  # Sucesso: sai do loop

        except FileNotFoundError as err:
            time.sleep(random.uniform(0.1, 1))
            cont -= 1

        except JSONDecodeError as err:
            cont -= 1
            logging.error(f"       Erro ao validar o conteúdo do arquivo JSON TEMP: {path_file}")

        except TypeError:
            logging.critical("Tipo inválido detectado. Arquivo JSON corrompido.")
            break

        except Exception as err:
            log_grava(err=err)
            logging.exception(f"Erro inesperado ao salvar JSON: {err}")
            break

    else:
        logging.error("Falha após múltiplas tentativas de salvar JSON.")

from filelock import FileLock

def abre_json(path_file: str) -> dict:
    os.makedirs(os.path.dirname(path_file), exist_ok=True)
    lock = FileLock(path_file + ".lock")
    with lock:
        if os.path.isfile(path=path_file):
            try:
                with open(path_file, encoding='utf-8') as json_file:
                    data = json.load(json_file)
                return data
            except UnicodeDecodeError:
                try:
                    with open(path_file, 'r', encoding='utf-8-sig') as json_file:
                        data = json.load(json_file)
                except UnicodeDecodeError:
                    with open(path_file, 'r', encoding='latin1') as json_file:
                        data = json.load(json_file)
        else:
            data = {}
            with open(path_file, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False)
            return data

def save_json(data, path_file):
    from filelock import FileLock
    path_temp = path_file[:-5] + "TEMP.json"
    lock = FileLock(path_file + ".lock")
    cont = 5

    with lock:
        while cont:
            try:
                with open(path_temp, 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
                    json_file.flush()
                    os.fsync(json_file.fileno())
                try:
                    with open(path_temp, encoding='utf-8') as json_file:
                        _ = json.load(json_file)
                except UnicodeDecodeError:
                    with open(path_temp, encoding='iso-8859-1') as json_file:
                        _ = json.load(json_file)
                with open(path_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                try:
                    os.remove(path_temp)
                except FileNotFoundError:
                    logging.warning("Arquivo TEMP já havia sido deletado.")
                except PermissionError:
                    logging.warning("Arquivo TEMP em uso, não foi possível deletar.")
                break
            except FileNotFoundError as err:
                time.sleep(random.uniform(0.1, 1))
                cont -= 1
            except JSONDecodeError as err:
                cont -= 1
                logging.error(f"       Erro ao validar o conteúdo do arquivo JSON TEMP: {path_file}")
            except TypeError:
                logging.critical("Tipo inválido detectado. Arquivo JSON corrompido.")
                break
            except Exception as err:
                log_grava(err=err)
                logging.exception(f"Erro inesperado ao salvar JSON: {err}")
                break
        else:
            logging.error("Falha após múltiplas tentativas de salvar JSON.")

def atualiza_bd(data_add, path_file):
    cont = 4
    n = random.randint(1, 10)
    path_temp = path_file[:-4] + "TEMP.json"
    while cont > 0:
        time.sleep(n/10)
        try:
            data = abre_json(path_file=path_file)
            data_update = merge_dicts(data, data_add)
            save_json(data=data_update, path_file=path_file)
            logging.info("Banco de dados atualizado com sucesso.")
            break
        except json.JSONDecodeError as err:
            logging.error(os.path.isfile(path_temp), "Falha ao decodificar JSON: %s", err)
            if os.path.isfile(path_temp):
                try:
                    os.remove(path_temp)
                    logging.info("Arquivo TEMP deletado com sucesso.")
                except FileNotFoundError:
                    logging.warning("Arquivo TEMP não encontrado ao tentar deletar.")
            else:
                try:
                    os.remove(path_file)
                    logging.info("Arquivo Original deletado com sucesso. Pois não existe TEMP para recuperar")
                except FileNotFoundError:
                    logging.warning("Arquivo TEMP não encontrado ao tentar deletar.")


            cont -= 1
            time.sleep(n)
        except Exception as e:
            logging.error("Erro desconhecido: %s", e)
            break

    if cont == 0:
        logging.error("Falha persistente ao atualizar banco de dados após várias tentativas.")

def atualiza_bd_scrapped(**kwargs):
    from datetime import datetime

    # Argumentos recebidos (com valores padrões se não informados)
    modulo = kwargs.get("modulo")
    info = kwargs.get("info", "")
    ra = kwargs.get("ra")
    curso_sigla = kwargs.get("curso_sigla")
    disciplina = kwargs.get("disciplina")

    # Define data atual no formato AAAAMMDD
    dia = datetime.now().strftime('%Y%m%d')

    # Caminho do arquivo JSON, definido por condição
    base_path = os.getcwd() + '\\BD'
    path_file = f"{base_path}\\atividades\\dias_scrapped.json" if disciplina else f"{base_path}\\alunos\\dias_scrapped.json"
    # path_temp = path_file[:-4] + "TEMP.json"

    tentativas = 4  # Número de tentativas de leitura/gravação do arquivo

    while tentativas > 0:
        try:

            with json_lock:  # <-- PROTEÇÃO CONTRA ACESSOS CONCORRENTES

                data = abre_json(path_file=path_file)

                if disciplina:
                    data\
                        .setdefault(dia, {})\
                        .setdefault(modulo, {})\
                        .setdefault(curso_sigla, {})[disciplina] = info
                elif ra:
                    data\
                        .setdefault(dia, {})\
                        .setdefault(modulo, {})[ra] = info

                save_json(data=data, path_file=path_file)

            logging.info("Banco de dados atualizado com sucesso.")
            break

        # except json.JSONDecodeError as err:
        #     logging.error("Falha ao decodificar JSON: %s", err)
        #     if os.path.isfile(path_temp):
        #         os.remove(path_temp)
        #         logging.info("Arquivo TEMP deletado com sucesso.")
        #     elif os.path.isfile(path_file):
        #         os.remove(path_file)
        #         logging.info("Arquivo original deletado, sem TEMP disponível.")
        #     else:
        #         logging.warning("Nenhum arquivo encontrado para deletar.")
        #     tentativas -= 1
        #     time.sleep(random.uniform(0.5, 2))  # espera mais longa antes de retentar

        except Exception as e:
            logging.error("Erro desconhecido: %s", e)
            log_grava(err=e)
            break  # Erro desconhecido: Sai imediatamente do loop

    else:
        print("dfjlçllllllllll")
        logging.error("Falha após várias tentativas de atualização.")

def salvar_com_releitura(path_file, novos_dados, disciplina):

    with json_lock:

        data_atual = abre_json(path_file)
        
        # Atualize somente a parte necessária
        data_atual = dict(novos_dados)
        
        save_json(data_atual, path_file)

def atualiza_bd_scrapped_40(**kwargs):
    from datetime import datetime

    # Informações de entrada
    modulo = kwargs.get("modulo",None)
    info = kwargs.get("info","")
    ra = kwargs.get("ra",None)
    curso_sigla = kwargs.get("curso_sigla",None)
    disciplina = kwargs.get("disciplina",None)

    # Data hoje no formato AAAAMMDD
    dia =  datetime.now().__format__('%Y%m%d')

    # Arquivos para ler do Banco de Dados
    path_file = os.getcwd()+'\\BD\\atividades\\dias_scrapped.json' if disciplina else os.getcwd()+'\\BD\\alunos\\dias_scrapped.json'

    cont = 4
    n = random.randint(1, 10)
    path_temp = path_file[:-4] + "TEMP.json"
    while cont > 0:
        time.sleep(n/10)
        try:
            data = abre_json(path_file=path_file)
            if disciplina:
                novo={
                    dia:{
                        modulo:{
                            curso_sigla:{disciplina:info}
                            }
                    }
                }
                # Garantindo que as chaves intermediárias existam:
                data.setdefault(dia, {}).setdefault(modulo, {}).setdefault(curso_sigla, {}).update(novo[dia][modulo][curso_sigla])


            elif ra:
                novo = {
                        dia: {
                            modulo: {
                                ra: info
                            }
                        }
                    }

                data.setdefault(dia, {}).setdefault(modulo, {}).update(novo[dia][modulo])

            save_json(data=data, path_file=path_file)
            logging.info("Banco de dados atualizado com sucesso.")
            break

        except json.JSONDecodeError as err:
            logging.error(os.path.isfile(path_temp), "Falha ao decodificar JSON: %s", err)
            if os.path.isfile(path_temp):
                try:
                    os.remove(path_temp)
                    logging.info("Arquivo TEMP deletado com sucesso.")
                except FileNotFoundError:
                    logging.warning("Arquivo TEMP não encontrado ao tentar deletar.")
            else:
                try:
                    os.remove(path_file)
                    logging.info("Arquivo Original deletado com sucesso. Pois não existe TEMP para recuperar")
                except FileNotFoundError:
                    logging.warning("Arquivo TEMP não encontrado ao tentar deletar.")
            cont-= 1
            time.sleep(n)
        except Exception as e:
            logging.error("Erro desconhecido: %s", e)
            break

    if cont == 0:
        logging.error("Falha persistente ao atualizar banco de dados após várias tentativas.")

def atualiza_bd_40(data_add, path_file):
    import random
    import time
    from json.decoder import JSONDecodeError

    temp = True
    cont = 4
    n = random.randint(1,5)
    while temp:
        print("aaaaa")
        try:
            path_temp = path_file[:-4]+"TEMP.json"
            data = abre_json(path_file=path_file)
            data_update = merge_dicts(data,data_add)

            print(f"      => Verifica se há arquivo TEMP:", os.path.isfile(path=path_temp))

            if not os.path.isfile(path=path_temp):
                save_json(data=data_update,path_file=path_file)
                break
        
        except JSONDecodeError as err:
            msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            print(msg,"\n\nFalha em abrir o JSON:", path_file[:-4]+"TEMP.json\n")

        if not cont:
            try:
                print(f"        - Deletando arquivo TEMP")
                os.remove(path=path_temp)
                print(f"        - Arquivo TEMP deletado com sucesso")
            except FileExistsError:
                pass
            # Renova a contagem, por um extremo do arquivo ter sido deletado
            # enquanto tentava apagá-lo.
            print("XXXXXX")
            n=4

        else: 
            print("55555555555")
            time.sleep(n)
            cont-=1

def integridade_bd(sigla,modulo):
    from json.decoder import JSONDecodeError

    try:
        path_file = os.getcwd()+'\\BD\\atividades\\'+modulo.replace('/','')+'\\bd_papiron_'+sigla+'.json'
        with open(path_file, encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        # Verifica se tem um arquivo TEMP indevido:
        path_file_temp = os.getcwd()+'\\BD\\atividades\\'+modulo.replace('/','')+'\\bd_papiron_'+sigla+'.TEMP.json'
        # retirei para não apagar os TEMPs tem que certeza que vão manter o principal
        # if os.path.isfile(path=path_file_temp):
        #     os.remove(path=path_file_temp)

        return data , path_file
    
    except FileNotFoundError:
        data = {sigla:{}}
        # print(f">> NÃO ARQUIVO LOCALIZOU: {path_file}")
        return data , path_file

    except json.JSONDecodeError:
        print(f"Erro na abertura do arquivo JSON  {path_file} , tentativa de recuperação!")
        path_file_temp = os.getcwd()+'\\BD\\atividades\\'+modulo.replace('/','')+'\\bd_papiron_'+sigla+'TEMP.json'
        data = verifica_temp(path_file = path_file, path_file_temp = path_file_temp, sigla = sigla,)
        return data , path_file

    except TypeError as err:
        # Ocorre quando passa pelo valor None que contém a lista de cursos
        return None, None
    
    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))+"XXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxxx\n\n>>>>>> FALHA NO CURSO:  "+sigla+"\n\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        print(msg)
        return None

def verifica_temp(path_file, path_file_temp, **kwargs) -> dict:
    import time
    from datetime import datetime
    from json.decoder import JSONDecodeError

    dict_item = kwargs.get("sigla", datetime.now().__format__('%Y%m%d'))

    print("Verificando arquivo TEMP", os.path.isfile(path=path_file_temp))

    if os.path.isfile(path=path_file_temp):
        # Verifica se existe o TEMP, caso exista
        # verifica se este não está corrompido
        try:
            print("    >>Abrindo arquivo TEMP")
            data = abre_json(path_file=path_file_temp)
            os.remove(path_file)
            os.rename(path_file_temp,path_file)
            print("    >>Renomeou arquivo TEMP")
            time.sleep(15)
            return data

        except JSONDecodeError:
            # caso os dois arquivos estejam corrompidos
            print("Devem ser apagados os dois arquivos, pois ambos estão corrompidos")
            os.remove(path_file)
            os.remove(path_file_temp)
            data = {dict_item:{}}
            return data

    else:
        # Como não há condições de restaurar, pois erro no arquivo principal
        # e não existe o TEMP. Apaga o arquivo principal corrompido
        os.remove(path_file)
        data = {dict_item:{}}
        return data

def leitura_dados_rastreamento(self, aluno, ra, curso, modulo, **kwargs):
    import os
    from datetime import datetime

    cb_geral = kwargs.get("cb_geral",None)

    dt_hoje = datetime.now().__format__('%Y%m%d')

    # Arquivos para ler do Banco de Dados
    path_file_aluno = os.path.abspath(os.getcwd())+'\\BD\\alunos\\dados_aluno_ra.json'
    try: 
        data_aluno = abre_json(path_file=path_file_aluno)
        
    except FileNotFoundError:
        raise FileNotFoundError

    # Obtém dados do Aluno, este arquivo tem que estar pronto antes de iniciar
    aluno_nome = data_aluno[ra]['NOME']
    aluno_ra = data_aluno[ra]['RA']
    aluno_curso = data_aluno[ra]['CURSO']
    aluno.dados(nome = aluno_nome, curso = aluno_curso, ra = aluno_ra)
    
    # Verifica a consistência do Curso
    if aluno_curso == "NÃO RASTREADO":
        raise StatusAlunoError 
    curso_sigla = curso[aluno_curso]

    # Verificação da existência e leitura dos arquivos BD
    # Registra informações dos CURSOS com relação aos scrappeds diários
    path_file_dia = os.getcwd()+'\\BD\\atividades\\dias_scrapped.json'
    if not os.path.isfile(path_file_dia):
        data_dia = {dt_hoje:{modulo:{}}}
        with open(path_file_dia, 'w', encoding='utf-8') as f:
            json.dump(data_dia, f ,ensure_ascii=False)
    else:
        with open(path_file_dia, encoding='utf-8') as json_file:
            data_dia = json.load(json_file)

            # Garante que todas as chaves intermediárias existam
            data_dia\
                .setdefault(dt_hoje, {})\
                .setdefault(modulo, {})\
                .setdefault(curso_sigla, {})
 
    # Verificação da existência e leitura dos arquivos BD
    # Registra informações dos ALUNOS com relação aos scrappeds diários
    path_file_dia_aluno = os.path.join(os.getcwd(), 'BD', 'alunos', 'dias_scrapped.json')

    # Carrega dados existentes ou inicializa nova estrutura se não existir
    if os.path.isfile(path_file_dia_aluno):
        with open(path_file_dia_aluno, encoding='utf-8') as json_file:
            data_dia_aluno = json.load(json_file)
    else:
        data_dia_aluno = {}

    # Garante a existência das chaves intermediárias
    data_dia_aluno\
        .setdefault(dt_hoje, {})\
        .setdefault(modulo, {})
    
    if aluno.ra in data_dia_aluno[dt_hoje][modulo]:
        raise StatusScrappedError

    # Verificação da existência e leitura dos arquivos BD
    # referente aos dados das atividades salvas
    path_dir = os.path.abspath(os.getcwd())+"\\BD\\atividades\\"+modulo.replace('/','')
    if not os.path.isdir(path_dir):
        verifica_pastas(dir_pasta=path_dir)

    path_file = path_dir+"\\bd_papiron_"+curso_sigla+'.json'
    if not os.path.isfile(path_file):
        data = {curso_sigla:{}}
        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(data, f ,ensure_ascii=False)

    else:
        with open(path_file, encoding='utf-8') as json_file:
            data = json.load(json_file)

    try:
        lista_geral = LISTA_GERAL_DISCIPLINAS
        verifica = False
        lista_disciplinas_rastrear = extrair_disciplinas_por_modulo(disciplinas=data_aluno[aluno.ra]['DISCIPLINAS'], modulo_alvo=modulo)
        
        if lista_disciplinas_rastrear:
            print(F"   \n Disciplinas a rastrear listadas [{modulo}] [{aluno_nome}] :")
            for d in lista_disciplinas_rastrear:
                print(f"      - {d}")
        else:
            raise DisciplinaNotNew

        print(f"\n        > Verifica se as disciplinas precisam ser rastreadas:")
        for disciplina in lista_disciplinas_rastrear:
            # print(f"         - {disciplina}")
            # disciplina_complementar = False

            # Caso esteja desmarcada a opção SCG, irá pular essa atividade
            # Caso esteja marcada, deve verificar somente as SCG
            # if "SEMANA DE CONHECIMENTOS GERAIS" in disciplina:
            #     if not self.config['cb_scg']:
            #         # print(f"        >> [{self.config['cb_scg']}] - Pular rastreio da SCG: {disciplina}")
            #         continue
            # else:
            #     if self.config['cb_scg']:
            #         # print(f"        >> [{self.config['cb_scg']}] - Pular rastreio de disciplina NÃO SCG: {disciplina}")
            #         continue

            # Se for rastrear o SCG, todo mundo do módulo aberto tem (ou quase todo mundo)
            if self.config['cb_scg']:
                # if aluno['SITUAÇÃO'] == "CURSANDO":
                #     return [aluno, data, data_aluno, data_dia, data_dia_aluno, path_file]
                # else:
                #     return [None, data, data_aluno, data_dia, data_dia_aluno, path_file]
                
                return [aluno, data, data_aluno, data_dia, data_dia_aluno, path_file] \
                        if data_aluno[ra]['SITUAÇÃO'] == "CURSANDO" \
                        else [None, data, data_aluno, data_dia, data_dia_aluno, path_file]

            if not any(palavra in disciplina for palavra in LISTA_EXCLUSAO_DISCIPLINAS):

                if any(palavra in disciplina for palavra in lista_geral):
                    # disciplina_complementar = True
                    if not cb_geral:
                        # print(f"        >> [{cb_geral}] - Atividade complementar não é para ser rastreada: {disciplina}")
                        continue
                    else:
                        # print(f"        >> [{cb_geral}] - Irá rastrar Atividade complementar: {disciplina}")
                        pass

                else:
                    # print(f"        >> [{cb_geral}] Atividade Curricular: {disciplina}") 
                    pass

                
                # Se a sigla não está no BD, isso significa que não houve rastreio no dt_hoje para a disciplina
                if curso_sigla in data_dia[dt_hoje]:
                    verifica_modulo = False
                    # Verifica:
                    # - se a disciplina não foi rastreada em portal de outro aluno.
                    # - Se a disciplina pertence ao módulo de rastreio.
                    # - o módulo das disciplinas de Nivelamento não são padrões, por isso não olhamos para o módulo delas

                    print(f"       {disciplina} - {modulo}\n        > Rastreada hoje?: {disciplina not in data_dia[dt_hoje][modulo][curso_sigla]}")
                    if disciplina not in data_dia[dt_hoje][modulo][curso_sigla]:
                        
                        # Percorre dentro das informações pessoais, pois pode variar o Status da disciplina para cada aluno
                        for opcao in LISTA_STATUS_DISCIPLINAS:
                            if opcao in data_aluno[ra]["DISCIPLINAS"]:
                                if disciplina in data_aluno[ra]["DISCIPLINAS"][opcao]:
                                    if data_aluno[ra]["DISCIPLINAS"][opcao][disciplina]["MODULO"] == modulo:
                                        verifica_modulo = True
                                        break
                            
                    if verifica_modulo:
                        print(f"        >> Encontrada nova disciplina a ser rastreada hoje em {curso_sigla}: {disciplina} - {modulo}")
                        verifica = True
                        break
                    else:
                        print(f"          >>  {curso_sigla}: {disciplina} - Rastreio OK\n")
                else:
                    # Não há registros que tenha feito nada de rastreio para o Curso
                    # Então pode rastrear tudo
                    verifica = True
                    break
            else:
                print(f"        >> Disciplina da lista de Exclusão: {disciplina}")


        if not verifica:
            raise DisciplinaNotNew
        
    except DisciplinaNotNew:
        print(f"   >> {aluno_ra} - {aluno_nome} - {modulo} - Não foi encontrada disciplina nova a ser rastreada neste módulo\n\n")
        raise DisciplinaNotNew

    except Exception as err:
        imprimir_erro(err)
        log_grava(msg="Erro a verificar:\n", err=err)
        raise
    
    return [aluno, data, data_aluno, data_dia, data_dia_aluno, path_file]

def clear_bd():
    """
    Elimina as entradas com senhas possivelmente erradas.
    """
    path_file = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
    data = abre_json(path_file)
    data_temp = dict(data)
    print("Aqui")
    for ra in data:
        if data[ra]["SENHA_OK"] == "SENHA FALHOU":
            del(data_temp[ra])
    
    save_json(data_temp, path_file)

def lista_sigla_cursos():

    siglas = dict_curso(opcao=1)

    return siglas
