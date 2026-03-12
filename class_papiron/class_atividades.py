try:
    import json
    import os
    import re
    import traceback
    from datetime import date, datetime
    from pathlib import Path

    import requests
    from function_bd import abre_json, save_json
    from function_extrair import scrapped_atividades
    from functions.curso import dict_curso
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtGui import *
    from PyQt6.QtWidgets import *
    from system.chrome import login_papiron
    from system.logger import log_grava
    from system.requests_unicesumar import login
    from system.system import t

    from class_papiron.class_error import (
        DisciplinaNotIniciadaError,
        DisciplinaScrappedError,
        RastreioError,
    )

    from class_papiron.utils_atividade.utils import (
        ajustar_nome_arquivo,
        hora_atual_texto,
        limpar_dict,
        limpar_idurl_errado,
        limpar_nome,
        totalizador_rastreio,
        totalizador_rastreio_aluno,
        totalizador_rastreio_ect,
        trimestre,
        verificar_lista_disciplinas,
    )

    from class_papiron.utils_atividade.utils_json import (
        atualizar_dict_atividades,
        caminho_completo,
        carregar_rastreio,
        gravar_rastreio,
        gravar_rastreio_aluno,
        gravar_rastreio_ect,
        verificar_rastreio,
        verificar_rastreio_aluno,
        verificar_rastreio_ect,
    )

except Exception as err:
    print(err)
    log_grava(err=err)
    raise Exception

LISTA=[ 
    "ESTUDO CONTEMPORÂNEO E TRANSVERSAL",
    "FORMAÇÃO SOCIOCULTURAL E ÉTICA",
    "PREPARE-SE",
    "PROJETO DE ENSINO",
    "NIVELAMENTO"
]


class Rotinas_RastrearAtividades(QObject):
    """
    Classe para rastreas as atividades do módulo selecionado

    ### Args:

        - self.ui, recupera informações da GUI
        - modulo, informa qual módulo será scrapped
        - self.config, informa as configurações extraídas da GUI
        - self.lista_curso, fornece a lista de curso que deverão ser executados dentro do Thread atual

    """
    finished = pyqtSignal()
    timerSignal = pyqtSignal()
    updateProgress = pyqtSignal(int,str)
    updateProgress_thread = pyqtSignal(str)
    sinal_postar = pyqtSignal(list,str)

    

    def __init__(
        self, 
        ui,
        config_thread,
    ) :

        super().__init__()
        self.active = True
        self.ui = ui
        self.config = config_thread
        self.thr = config_thread['THREAD']
        self.lista_curso_disciplinas = config_thread.get('CURSOS_DISCIPLINAS')
        self.lista_curso = config_thread.get('LISTA CURSOS')
        self.ras = config_thread.get('ALUNOS_RA')
        self.disciplina_especial = config_thread.get('disciplina_especial')
        self.config['rastrear_ect'] =  config_thread.get('rastrear_ect',False)
        self.config['rastrear_scg'] =  config_thread.get('rastrear_scg',False)
        self.config['disciplina_unica'] = config_thread.get('disciplina_unica',None)
        self.rastrear_scg =  config_thread.get('rastrear_scg',False)
        self.data_base = self.config["data_base"]
                
    def run_rastrear_atividades_scg(self):

        from class_papiron.utils_atividade.utils_rastrear import rastrear_atividades_ra
        from class_papiron.utils_atividade.utils_salvar import (
            gerenciar_nome_drive_complementar,
            salvar_dados_rastreio_local,
            salvar_dados_rastreio_remoto
        )

        self.trimestre_scg = trimestre()
        
        # Não baixar nenhum material
        self.config['cb_download_livros'] = False
        self.config['cb_material_atualizar'] = False

        self.data_hoje = datetime.now().strftime('%d%m%Y')
        self.cursos_papiron = dict_curso(opcao=6)
        # print(f">> travar dia em {self.data_base}")

        self.username = self.config['username']
        self.password = self.config['password'] 
        url_base ="https://www.papiron.com.br" 

        self.headers_papiron = login_papiron(self.username,self.password,url_base)

        # Informa dados iniciais
        sigla_curso_rastreio = "GERAL"
        curso_rastreio = "SCG"
        ano_rastreio = str(datetime.now().year)
        mod_curso_rastreio = "5"
        modulo_rastreio = str(trimestre())
        disciplina_rastreio = "SEMANA DE CONHECIMENTOS GERAIS"

        dados_drive_disciplina = gerenciar_nome_drive_complementar(
            self=self,
            disciplina_rastreio=disciplina_rastreio,
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            estilo = "SCG"
        )

        atividades = None
        for i, ra in enumerate(self.ras):

            # Para imprimir 1
            # if i!=0:
            #     continue
                        
            try:
                if verificar_rastreio_aluno(self, ra=ra):
                    print(f"  >> Consta que o aluno já foi rastreado hoje: {ra}")
                    continue

                print(f"  >> Nova portal a ser rastreado: {ra}")
                print(f"  >>> Entrando no login {ra} e senha {self.ras[ra]['senha']}")
                
                try:
                    # Entra no login do aluno "ra" e coleta as informações
                    # da disciplina do looping
                    self.headers = login(ra=ra,senha=self.ras[ra]['senha'])
                    cd_shortname_rastreio = self.ras[ra]['cd_shortname']
                    
                    atividades = rastrear_atividades_ra(
                        self,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        curso_rastreio=curso_rastreio,
                        sigla_curso_rastreio=sigla_curso_rastreio,
                        disciplina_rastreio=disciplina_rastreio,
                        cd_shortname_rastreio=cd_shortname_rastreio        
                    )

                    gravar_rastreio_aluno(self,ra=ra)
                
                    print(f"\n\n ---------------- FIM RASTREIO: {ra} - {cd_shortname_rastreio} ------------------- ")

                except ValueError as err:
                    log_grava(msg=f"Falha ao entrar no login: {ra} senha: {self.ras[ra]}")
            
            except requests.exceptions.RequestException as e:
                msg = f"Erro de conexão ou requisição: {e}"
                log_grava(msg=msg)
                print(msg)
                t(300)

            except RastreioError:
                print("   >>>> Erro durante a execução do rastreio\n\n")
            
            except Exception as err:
                log_grava(err=err)
            
            # Depois de finalizar o FOR de disciplinas do curso, incrementa 
            self.updateProgress.emit(totalizador_rastreio_aluno(self), f"Finalizou o rastreio para o RA {ra}")

        # Caso já tenha feito todo rastreio, recupera o json salvo
        if not atividades:
            path = Path(caminho_completo(
                ano_rastreio=ano_rastreio,
                modulo_rastreio=modulo_rastreio,
                curso_rastreio=curso_rastreio,
                disciplina_rastreio=disciplina_rastreio,
            ))
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    atividades=json.load(f)
            else:
                atividades=[]
            
        # Salvar dados no Drive do Computador
        salvar_dados_rastreio_local(
            self,
            dados_drive_disciplina=dados_drive_disciplina,                       
            ano_rastreio=ano_rastreio,
            modulo_rastreio=modulo_rastreio,
            curso_rastreio=curso_rastreio,
            sigla_curso_rastreio=sigla_curso_rastreio,
            disciplina_salvamento=disciplina_rastreio,
            atividades=atividades,
            )

        # Salvar dados Remotamente
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
                   
    def run_rastrear_atividades_ect(self):

        from class_papiron.utils_atividade.utils_rastrear import rastrear_atividades_ra
        from class_papiron.utils_atividade.utils_salvar import (
            recuperando_dados_salvos_disciplina_legenda,
            salvar_dados_rastreio_ect
        )

        # Não baixar nenhum material
        self.config['cb_download_livros'] = False
        self.config['cb_material_atualizar'] = False

        # Dados gerais do rastreio
        self.data_hoje = datetime.now().strftime('%d%m%Y')
        self.cursos_papiron = dict_curso(opcao=6)

        # Logar na Papiron
        self.username = self.config['username']
        self.password = self.config['password'] 
        url_base ="https://www.papiron.com.br" 
        self.headers_papiron = login_papiron(self.username,self.password,url_base)

        dict_atividades_ect = {}

        for ano in self.ras:
            
            # Informa dados iniciais
            modulos = self.ras[ano]
            ano_rastreio = ano
            print(f"\n    >> RASTREAR ANO: [{ano}]")

            for modulo in modulos:                    
                self.ras = modulos[modulo]
                modulo_rastreio = modulo
                mod_curso_rastreio = "5"

                print(f"    >>> MÓDULO: [{modulo}]")

                for i, ra in enumerate(self.ras):

                    try:

                        # if ra != "23161337-5":
                        #     continue

                        if verificar_rastreio_ect(self,ra,ano,modulo):
                            print(f"    >>>> Consta que o aluno já foi rastreado hoje: {ra}")
                            continue

                        print(f"    >>>> Nova portal a ser rastreado: {ra}")
                        print(f"    >>>>> Entrando no login {ra} e senha {self.ras[ra]['senha']}")
                        
                        try:
                            # Entra no login do aluno "ra" e coleta as informações
                            # da disciplina do looping
                            self.headers = login(ra=ra,senha=self.ras[ra]['senha'])
                            cd_shortname_rastreio = self.ras[ra]['cd_shortname']
                            url_ect = f"https://studeoapi.unicesumar.edu.br/ambiente-api-controller/api/usuario-log-acesso-disciplina/{cd_shortname_rastreio}"
                            req_ect = requests.post(url=url_ect,headers=self.headers)

                            if req_ect.status_code != 200:
                                continue

                            dados_ect = req_ect.json()
                            # print("dadas", dados_ect)
                            disciplina_bruta = limpar_nome(dados_ect['idDisciplina']['nmDisciplina'])
                            disciplina_rastreio = ajustar_nome_arquivo(disciplina_bruta)


                            # if "TRANSFORMAÇÃO DIGITAL" not in disciplina_rastreio:  #"" "AUTONOMIA INTELECTUAL"
                            #     continue

                            # Informa dados iniciais
                            sigla_curso_rastreio = "GERAL"
                            curso_rastreio = "GERAL"
                            modulo_rastreio = modulo
                            mod_curso_rastreio = "5"

                            # Recupera dados já salvos
                            
                            # Confirmou entrada no login, então agora irá verificar
                            # as atividades que o aluno tem
                            atividades_novas = rastrear_atividades_ra(
                                self,
                                disciplina_rastreio=disciplina_rastreio,
                                ano_rastreio=ano_rastreio,
                                modulo_rastreio=modulo_rastreio,
                                cd_shortname_rastreio = cd_shortname_rastreio,
                                curso_rastreio=curso_rastreio,
                                sigla_curso_rastreio = sigla_curso_rastreio
                            )

                            atividades=recuperando_dados_salvos_disciplina_legenda(
                                ano_rastreio=ano_rastreio,
                                modulo_rastreio=modulo_rastreio,
                                curso_rastreio=curso_rastreio,
                                disciplina_rastreio=disciplina_rastreio,
                                atividades_req=atividades_novas
                            )

                            gravar_rastreio_ect(self, ano, modulo, ra)
                        
                            print(f"\n\n ---------------- FIM RASTREIO: {ra} - {cd_shortname_rastreio} ------------------- ")

                        except ValueError as err:
                            log_grava(msg=f"Falha ao entrar no login: {ra} senha: {self.ras[ra]['senha']}")
                        
                        # Adiciona ao todo
                        dict_atividades_ect[disciplina_rastreio] = atividades
                    
                    except requests.exceptions.RequestException as e:
                        msg = f"Erro de conexão ou requisição: {e}"
                        log_grava(msg=msg)
                        print(msg)
                        t(300)

                    except RastreioError:
                        print("   >>>> Erro durante a execução do rastreio\n\n")
                    
                    except Exception as err:
                        log_grava(err=err)
                    
                    # Depois de finalizar o FOR de disciplinas do curso, incrementa 
                    self.updateProgress.emit(totalizador_rastreio_ect(self), f"[{totalizador_rastreio_ect(self)}] - Finalizou o rastreio para o RA {ra}")

                if dict_atividades_ect:
                    salvar_dados_rastreio_ect(
                        self,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        curso_rastreio=curso_rastreio,
                        mod_curso_rastreio=mod_curso_rastreio,
                        sigla_curso_rastreio=sigla_curso_rastreio,
                        dict_atividades_ect =dict_atividades_ect,
                    )

            self.updateProgress.emit(totalizador_rastreio_ect(self), f"Finalizou o rastreio para os ETCs")
     
    def run_rastrear_atividades_req(self):
        import urllib.parse
    
        
        self.data_hoje = datetime.now().strftime('%d%m%Y')
        self.cursos_papiron = dict_curso(opcao=6)
        print(f">> travar dia em {self.data_base}")

        self.username = self.config['username']
        self.password = self.config['password'] 
        url_base ="https://www.papiron.com.br" 

        self.headers_papiron = login_papiron(self.username,self.password,url_base)

        for ano in self.lista_curso_disciplinas:
            modulos = self.lista_curso_disciplinas[ano]
            for modulo in modulos:                    
                cursos = modulos[modulo]
                n_cursos = 0
                n_cursos_total = len(cursos)
                for j,  curso in enumerate(cursos):
                    n_cursos +=1
                    disciplinas = cursos[curso]
                    print(f"\n\nX - X - X - X - X - X - X  {curso} - Total de {j+1} de {len(cursos)}  X - X - X - X - X - X - X \n")

                    for i, disciplina in enumerate(disciplinas):
                        
                        if self.config['disciplina_unica']:
                            texto = self.config['disciplina_unica']
                            lista = re.split(r'[;]\s*', texto.upper())

                            # print(f"    [{curso}] {disciplina}")
                            if disciplina not in lista:
                                self.updateProgress.emit(totalizador_rastreio(self), None)
                                continue

                        # Disciplinas Gerais fora da LISTA pulam
                        if modulo == "9":
                            if not any(disc in disciplina for disc in LISTA):
                                
                                print(f'\n\n     >> Disciplina do Looping: {disciplina}') 
                                print(f'     >>>> Excluída do Rastreio') 
                                continue

                        print(f"\n\n> Total de {j+1} de {len(cursos)} ------- Total de {i+1} de {len(disciplinas)} xxxxxxxxxxxxxxxxxxx {disciplina} xxxxxxxxxxxxxxxxxxxxxxx")

                        self.disciplina_rastreio = ajustar_nome_arquivo(disciplina)
                        
                        self.curso_rastreio = "GERAL" if any(disc in disciplina for disc in LISTA) else curso
                        
                        try:
                            if verificar_rastreio(self,self.curso_rastreio,limpar_nome(self.disciplina_rastreio),ano,modulo):
                                print(f"  >> Consta que a disciplina foi rastreada em outro aluno: {self.disciplina_rastreio} {ano}_{modulo} - {self.curso_rastreio}")
                                self.updateProgress.emit(totalizador_rastreio(self), None)
                                continue
                            else:
                                print(f"  >> Nova disciplina a ser rastreada: {self.disciplina_rastreio} {ano}_{modulo} - {self.curso_rastreio}")

                            # procurar alunos que são ou foram matriculados na disciplina do curso do looping
                            # tem que procurar pelos nomes reais de curso e disciplina
                            curso_encode = urllib.parse.quote(curso)
                            disciplina_encode = urllib.parse.quote(disciplina)
                            url = f"https://www.papiron.com.br/ferramentas/informar_alunos_json/{curso_encode}/{disciplina_encode}/{ano}/{modulo}"
                            req = requests.get(url=url)
                            self.ras = req.json()

                            print(f"   > Localizou {len(self.ras) } RA´s que possuem a disciplina {disciplina} - {url}")

                            for ra in dict(self.ras):

                                print(f"   >> Entrando no login {ra} e senha {self.ras[ra]['senha']}")
                                
                                try:
                                    # Entra no login do aluno "ra" e coleta as informações
                                    # da disciplina do looping
                                    self.headers = login(ra=ra,senha=self.ras[ra]['senha'])
                                    print("logou aqui")
                                    # Confirmou entrada no login, então agora irá verificar
                                    # as atividades que o aluno tem
                                    self.verificar_atividades_ra(
                                        ra=ra,
                                        curso=curso
                                    )
                                    
                                    print(f"\n\n      >>>> FIM RASTREIO RA: {ra} ------------------- ")
                                    
                                    if ajustar_nome_arquivo(self.disciplina_rastreio) == ajustar_nome_arquivo(disciplina):
                                        print(f"---------------- FIM RASTREIO da disciplina alvo:  {disciplina} ------------------- ")
                                        break
                                    else:
                                        print(f"\n       >>> Continua no looping para encontrar a disciplina alvo do looping")
                                        print(f"        >>>> Disc Looping : {ajustar_nome_arquivo(disciplina)}")

                                except ValueError as err:
                                    log_grava(msg=f"Falha ao entrar no login: {ra} senha: {self.ras[ra]}")
                        
                        except requests.exceptions.RequestException as e:
                            msg = f"Erro de conexão ou requisição: {e}"
                            log_grava(msg=msg)
                            print(msg)
                            t(300)
                        
                        except Exception as err:
                            log_grava(err=err)
                        
                        self.updateProgress.emit(totalizador_rastreio(self), None)
                    
                    # Depois de finalizar o FOR de disciplinas do curso, incrementa
                    hora_atual = hora_atual_texto()
                    self.updateProgress.emit(totalizador_rastreio(self), f"[{hora_atual}] Finalizou para {curso} [{ano}_{modulo}]  {n_cursos}/{n_cursos_total}")
                
                self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X")
                self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X")
                self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X")
                self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X      MÓDULO:{ano}_{modulo}      X-X-X-X-X-X-X-X-X-X-X-X-X-X")
            self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X")
            self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X")
            self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X-X")
            self.updateProgress.emit(totalizador_rastreio(self), f"X-X-X-X-X-X-X-X-X-X-X-X     ANO: {ano}      X-X-X-X-X-X-X-X-X-X-X-X")

    def verificar_atividades_ra(self,**kwargs):
        """
        Depois de confirmado que os dados de login estão corretos
        irá buscar no papiron as disciplinas do aluno e irá mandar 
        percorrer as que pertecerem ao conjunto de disciplinas gerais
        a serem rastreadas

        """

        try:
            import importlib
            # print(" >> Iniciando importação dinâmica...")

            # 1. Carrega utils_downloads
            mod_downloads = importlib.import_module("class_papiron.utils_atividade.utils_downloads")
            baixar_material_disciplina = mod_downloads.baixar_material_disciplina
            # print(" >> utils_downloads carregado.")

            # 2. Carrega utils_rastrear
            mod_rastrear = importlib.import_module("class_papiron.utils_atividade.utils_rastrear")
            buscar_disciplina_de_rastreio = mod_rastrear.buscar_disciplina_de_rastreio
            dados_iniciais_rastreio = mod_rastrear.dados_iniciais_rastreio
            rastrear_atividades_ra = mod_rastrear.rastrear_atividades_ra
            # print(" >> utils_rastrear carregado.")

            # 3. Carrega utils_salvar
            mod_salvar = importlib.import_module("class_papiron.utils_atividade.utils_salvar")
            gerenciar_nome_drive = mod_salvar.gerenciar_nome_drive
            salvar_dados_rastreio_geral = mod_salvar.salvar_dados_rastreio_geral
            # print(" >> utils_salvar carregado.")

        except Exception as e:
            import traceback
            print("\n\n" + "="*60)
            print(">>> ERRO NO IMPORTLIB <<<")
            print(f"Erro: {e}")
            print(traceback.format_exc())
            print("="*60 + "\n\n")
            raise e

        print("Imports finalizados. Prosseguindo...")


        ra=kwargs['ra'] 
        curso=kwargs['curso']
    
        cont = 3
        while cont:
            try:
                # Verificar todas as disciplinas do aluno RA que estão no rastreio
                url_aluno_disciplinas = f"https://www.papiron.com.br/ferramentas/informar_disciplinas_aluno_json/{ra}"
                req_aluno_disciplinas = requests.get(url=url_aluno_disciplinas)
                disciplinas_ra = req_aluno_disciplinas.json()

                print(f"   >>>> Foram localizadas {len(disciplinas_ra)} disciplinas - {ra}, iniciar rastreio")
                break
            
            except requests.exceptions.RequestException as e:
                cont -=1
                msg = f"Erro de conexão ou requisição: {e}"
                log_grava(msg=msg)
                print(msg)
                t(300)
                if not cont:
                    raise RastreioError
                        
        
        for disciplina_ra in disciplinas_ra:

            try:
                verificar_lista_disciplinas(self,disciplina_ra=disciplina_ra)

            except DisciplinaScrappedError:
                continue
            
            except Exception as err:
                log_grava(err=err)
                continue
            
            # Gera e formata informações para realizar o rastreio 
            [ano_rastreio,modulo_rastreio,mod_curso_rastreio,disciplina_rastreio,cd_shortname_rastreio,
            curso_verificar_rastreio,disciplina_verificar_rastreio,curso_rastreio,
            sigla_curso_rastreio] = dados_iniciais_rastreio(self,ra=ra,curso=curso,disciplina_ra=disciplina_ra)

            if buscar_disciplina_de_rastreio(
                self=self,
                ano_rastreio=ano_rastreio,
                modulo_rastreio=modulo_rastreio,
                curso=curso,
                curso_rastreio=curso_rastreio,
                disciplina_rastreio=disciplina_rastreio,
                lista_curso_disciplinas=self.lista_curso_disciplinas,
                disciplina_verificar_rastreio=disciplina_verificar_rastreio,
                curso_verificar_rastreio=curso_verificar_rastreio
            ):

                try:
                    # Realiza o rastreio das atividades dentro do RA do aluno
                    atividades = rastrear_atividades_ra(
                        self,
                        ra=ra,
                        # dados_drive_disciplina = dados_drive_disciplina,
                        disciplina_rastreio=disciplina_rastreio,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        cd_shortname_rastreio = cd_shortname_rastreio,
                        curso_rastreio=curso_rastreio,
                        sigla_curso_rastreio = sigla_curso_rastreio,
                    )

                    dados_drive_disciplina=gerenciar_nome_drive(
                        self,
                        disciplina_rastreio=disciplina_rastreio,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        curso_rastreio=curso_rastreio,
                        sigla_curso_rastreio=sigla_curso_rastreio,
                        atividades=atividades,
                    )

                    salvar_dados_rastreio_geral(self,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        mod_curso_rastreio=mod_curso_rastreio,
                        curso_rastreio=curso_rastreio,
                        sigla_curso_rastreio=sigla_curso_rastreio,
                        atividades=atividades,
                        disciplina_rastreio=disciplina_rastreio,
                        dados_drive_disciplina=dados_drive_disciplina
                    )

                    # Finalizado o rastreio, realiza o download de templates e livros
                    baixar_material_disciplina(
                        self,
                        atividades=atividades,
                        disciplina_rastreio=disciplina_rastreio,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        dados_drive_disciplina=dados_drive_disciplina,
                        cd_shortname_rastreio=cd_shortname_rastreio
                    )

                    # Final
                    print(f"      X-X-X-X Finalizou Rastreio da disciplina, grava registro JSON {curso_rastreio} - {disciplina_rastreio} X-X-X-X")
                    gravar_rastreio(
                        self,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        curso_rastreio=curso_rastreio,
                        disciplina_rastreio=disciplina_rastreio
                    )
                    print(f"\n\n ---------------- FIM: {disciplina_rastreio}  ------------------- \n\n")
    
                
                except DisciplinaNotIniciadaError:
                    # Disciplina com nenhuma atividade liberada no portal do aluno
                    gravar_rastreio(
                        self,
                        ano_rastreio=ano_rastreio,
                        modulo_rastreio=modulo_rastreio,
                        curso_rastreio=curso_rastreio,
                        disciplina_rastreio=disciplina_rastreio
                    )
                    continue

                except RastreioError as err:
                    msg=f"Passará o rastreio para o aluno seguinte"
                    log_grava(err=err)
                    continue

                except Exception as err:
                    log_grava(err=err)
                    continue
