import os
import re
import shutil
import unicodedata

import pdfkit
import requests
from class_papiron.utils_atividade.utils import (
    ajustar_nome_arquivo,
    contar_gabaritos,
    limpar_nome,
    verificar_data_inicio,
)
from class_papiron.utils_atividade.utils_json import abrir_arquivo_path_drive_json
from system.converter_HTML_to_PDF import render_questionario_to_html
from system.logger import log_grava
from system.pastas import localizar_desktop


def salvar_atividade(self,**kwargs):
    ano_rastreio=kwargs['ano_rastreio']
    modulo_rastreio=kwargs['modulo_rastreio']    
    disciplina_salvamento=kwargs['disciplina_salvamento']
    atividade_tipo=kwargs['atividade_tipo']
    questionario=kwargs['questionario']
    dados_drive_disciplina=kwargs['dados_drive_disciplina']

    # Recupera os hashes das disciplinas
    dados_drive_geral = abrir_arquivo_path_drive_json(
        self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio
    )

    # recupera o hash geral por tipo de atividade
    hash_atividades = dados_drive_disciplina.get('questionario') if questionario else dados_drive_disciplina.get('discursiva')
    
    tipo = "questionario" if questionario else "discursiva" 
    if not hash_atividades:
        print(f"     >>> Não há atividades do tipo {tipo} para salvar material")

    # Diretório completo onde ficará o arquivo (NÃO inclui extensão)
    # Nivelamento não precisar estar aqui, para ser separado em pastas
    
    if (
        "PREPARE-SE" in disciplina_salvamento
        or "PROJETO DE ENSINO" in disciplina_salvamento
        or self.config['rastrear_ect'] or self.config['rastrear_scg']
    ):
        caminho_atividade_drive = dados_drive_geral[hash_atividades]['drive']

    else:
        caminho_atividade_drive = (
            f"{dados_drive_geral[hash_atividades]['drive']} - {limpar_nome(disciplina_salvamento)}"
        )
    
    # print(f"[{disciplina_salvamento}] caminho_atividade_drive = {caminho_atividade_drive}")

    caminho_atividade_dir = os.path.join(
        caminho_atividade_drive,
        limpar_nome(atividade_tipo['descricao'])
    )    

    # caminho_atividade_questionario = caminho_atividade_drive

    if questionario:   
        total = len(atividade_tipo['QUESTOES']) 
        respondidas = contar_gabaritos(self,atividade_tipo)
        caminho_atividade_dir = f'{caminho_atividade_dir} - {respondidas} de {total}'

        # if total!=respondidas:
        #     print("    Não temos o GABARITO COMPLETO, então não salva o PDF.")
        #     return 
        
    # else:
    #     caminho_atividade_discursiva = caminho_atividade_drive
        
    # reduzir de tamanho em alguns casos
    caminho_atividade_dir = ajustar_nome_arquivo(caminho_atividade_dir)

    # Caminho completo para o arquivo .html e .pdf
    arquivo_html = unicodedata.normalize("NFC",caminho_atividade_dir + ".html")
    arquivo_pdf = unicodedata.normalize("NFC",caminho_atividade_dir + ".pdf")

    # print(" >>>> ARQUIVO HTML", arquivo_html)
    print("    >>> ARQUIVO PDF", arquivo_pdf)

    # print("reprs:", repr(arquivo_html))
    # print("existss:", os.path.exists(arquivo_html))

    # Antes de salvar: criar todas as pastas necessárias
    pasta = os.path.dirname(arquivo_html)
    os.makedirs(pasta, exist_ok=True)  # Cria todas as pastas, se não existirem

    
    # Verifica se a atividade está SALVA e ATUALIZADA no drive
    if atividade_tipo['atualizar_atividade'] and os.path.isfile(arquivo_pdf):
        print(f"    >>> Atividade {atividade_tipo['descricao']} já está salva e atualizada no drive")
        return
    
    print(f"    >>> DRIVE: {caminho_atividade_drive}")

    # Salva HTML
    try:
        html = render_questionario_to_html(data=atividade_tipo)
        with open(arquivo_html, 'w', encoding='utf-8') as f:
            f.write(html)

    except AttributeError as err:
        log_grava(err=err)
        import winsound
        winsound.Beep(3000,2000)

    # Caminho do wkhtmltopdf (ajuste se estiver diferente)
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

    # Gera PDF
    print("    >>>>> Salvando o PDF:", arquivo_pdf)

    try:
        # Opções recomendadas
        options = {
            'encoding': "UTF-8",
            'disable-smart-shrinking': '',
        }

        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        pdfkit.from_file(arquivo_html, arquivo_pdf,  configuration=config, options=options)

        print(f"        Arquivo salvo em: {arquivo_pdf}")
    
    except OSError as err:

        print("    >>>>  Erro ao gerar PDF, tentar salvar de outra forma")

        try:

            from xhtml2pdf import pisa

            with open(f"VP_{arquivo_pdf}", 'wb') as f:
                pisa.CreatePDF(html, dest=f)
            
            print(f"        Arquivo salvo em: {arquivo_pdf}")

        except Exception as err:
            log_grava(err=err)

    if os.path.isfile(arquivo_html):
        os.remove(arquivo_html)

    # Registrar que a atividade foi salva
    atividade_tipo['atualizar_atividade'] = True

def download_material(self,**kwargs):

    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    dados_drive_disciplina=kwargs['dados_drive_disciplina']
    disciplina_rastreio=kwargs['disciplina_rastreio']
    cd_shortname_rastreio=kwargs['cd_shortname_rastreio']

    # Verifica se existe atividade de questionário, se não
    # houver vai salvar na pasta das discursivas
    hash_atividade = dados_drive_disciplina.get('questionario')
    if not hash_atividade:
        hash_atividade = dados_drive_disciplina.get('discursiva')
        if not hash_atividade:
            return None
   
    # Caminho base do livro na pasta Livros Digitais
    caminho_livro_base = os.path.join(
        localizar_desktop(),
        "Papiron",
        "Livros Digitais",
        limpar_nome(disciplina_rastreio)
    )

    dados_drive_geral = abrir_arquivo_path_drive_json(
        self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio = modulo_rastreio
    )   
    
    destino_dir = os.path.join(
            f"{dados_drive_geral[hash_atividade]['drive']} - {limpar_nome(disciplina_rastreio)}"
        )
    # print("caminho questionario:",destino_dir)
    # destino_dir =  self.dados_drive_disciplina['questionario']
    os.makedirs(destino_dir, exist_ok=True)

    # Tenta copiar localmente (apenas o primeiro MATERIAL.pdf)
    caminho_livro_pdf = f'{caminho_livro_base}.pdf'
    # destino_material_pdf = os.path.join(destino_dir, "MATERIAL.pdf")

    # Se não achou localmente, baixa todos os PDFs disponíveis
    url_lista_livro = f'https://studeoapi.unicesumar.edu.br/objeto-ensino-api-controller/api/material-estudo/{cd_shortname_rastreio}'
    req = requests.get(url=url_lista_livro, headers=self.headers)
    lista = req.json()

    hashes_pdf = [item["nomeArquivoHash"] for item in lista if item["tipo"] == "pdf"]
    
    if not hashes_pdf:
        print("\n   >> Nenhum PDF encontrado para download!")
        return

    headers_download_pdf = self.headers.copy()
    # headers['host'] = 'conteudoava.unicesumar.edu.br'
    # headers['referer'] = 'https://studeo.unicesumar.edu.br/'

    print(f"   >>> Lista de Hashes de Livros {hashes_pdf}")

    for idx, hash_pdf in enumerate(hashes_pdf, start=1):
        
        # Define nome dos arquivos para salvar
        if len(hashes_pdf) == 1:
            nome_pdf = "MATERIAL.pdf"
            caminho_livro_pdf = f"{caminho_livro_base}.pdf"
        else:
            nome_pdf = f"MATERIAL_{idx}.pdf"
            caminho_livro_pdf = f"{caminho_livro_base}_{idx}.pdf"

        
        print(f"\n   >> LIVRO LOCAL [{os.path.isfile(caminho_livro_pdf)}]:", caminho_livro_pdf)
        caminho_pdf_destino = os.path.join(destino_dir, nome_pdf)

        # Se já tiver um livro com mesmo nome do destino final
        if os.path.isfile(caminho_pdf_destino):
            print(f"   >>> Já tem o livro no drive")
            continue
        else:
            print(f"   >>> Necessário enviar livro para DRIVE")
        
        # Verifica se existe o livro na pasta de Livros
        if os.path.isfile(caminho_livro_pdf):

            # Tenta copiar localmente para o destino final, caso não esteja lá
            if not os.path.isfile(caminho_pdf_destino):
                shutil.copyfile(src=caminho_livro_pdf, dst=caminho_pdf_destino)
                print(f"   >>>> Livro local encontrado e copiado para: {caminho_pdf_destino}")
            else:
                print(f"   >>>> Livro já está no destino final: {caminho_pdf_destino}")
            return
        else:
            print(f"   >>>> Livro local NÃO encontrado em: {caminho_livro_pdf}")

        
        cont_download = 3

        while cont_download:
            try:
                # print(f"   Hash do livro pdf {hash_pdf}")
                url_pdf_api = f"https://studeoapi.unicesumar.edu.br/central-anexo-api-controller/api-conteudo/download/apostila/{hash_pdf}?redirect=false"
                # print(f"   >> URL_PDF_API = {url_pdf_api}")
                resp = requests.get(url=url_pdf_api, headers=self.headers)
                # print(f"   >> resp url api = {resp.status_code}")
                
                
                url_download_livro = resp.text.strip('"')  # Remove aspas se vier
                # print(f"   >> url donwload- {url_download_livro}")
                print(f"\n   >>>>> Livro {idx} sendo Baixado")
                req_download_livro = requests.get(url=url_download_livro, headers={"User-Agent": headers_download_pdf["User-Agent"],"Accept-Ranges":"bytes"})
                break
            
            except requests.exceptions.InvalidSchema as err:
                cont_download-=1
                log_grava(msg=f"Falha ao tentar baixar o livro {nome_pdf}",err=err)
                if not cont_download:
                    return
            except Exception as err:
                cont_download-=1
                log_grava(err=err)
                if not cont_download:
                    return

        # Salva na pasta Livros Digitais
        with open(caminho_livro_pdf, "wb") as f:
            f.write(req_download_livro.content)
        print(f"   >>>>>> PDF salvo em Livros Digitais: {caminho_livro_pdf}")

        # Salva na pasta da atividade
        with open(caminho_pdf_destino, "wb") as f:
            f.write(req_download_livro.content)
        print(f"   >>>>>> PDF salvo na atividade: {caminho_pdf_destino}")

def download_templates(self,**kwargs):
    
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    disciplina_rastreio=kwargs['disciplina_rastreio']
    dados_drive_disciplina=kwargs['dados_drive_disciplina']
    cd_shortname_rastreio=kwargs['cd_shortname_rastreio']

    # Verifica se existe atividade de questionário, se não
    # houver vai salvar na pasta das discursivas
    hash_atividade=dados_drive_disciplina.get('discursiva')
    if not hash_atividade:
        return None

    print("  >> Iniciando a rastrear Templates")

    url_templates = f'https://studeoapi.unicesumar.edu.br/ambiente-api-controller/api/arquivo/disciplina/{cd_shortname_rastreio}'

    headers = self.headers.copy()
    headers['host'] = 'studeoapi.unicesumar.edu.br'
    headers['referer'] = 'https://studeo.unicesumar.edu.br/'
    headers['origin']= 'https://studeo.unicesumar.edu.br'

    req = requests.get(url=url_templates, headers=headers)
    lista_extras = req.json()
    lista_templates = listar_templates(lista_extras)
    print(f"TEMPLATES>>> {lista_templates}")
    if not lista_templates:
        print(f" >> Não foram localizados templates a serem baixados")
        return

    # Caminho onde serão armazenados os templates
    dados_drive_geral = abrir_arquivo_path_drive_json(
        self,
        ano_rastreio=ano_rastreio,
        modulo_rastreio=modulo_rastreio
    )
    destino_dir =  destino_dir = os.path.join(
            f"{dados_drive_geral[hash_atividade]['drive']} - {limpar_nome(disciplina_rastreio)}"
        )
    print("caminho template:",destino_dir)
    os.makedirs(destino_dir, exist_ok=True)

    for item in lista_templates:
        url_material_api = f"https://studeoapi.unicesumar.edu.br/central-anexo-api-controller/api-conteudo/download/arquivo-geral/{item['nome_arquivo']}?redirect=false"
        resp = requests.get(url_material_api, headers=headers)
        
        url_download_material = resp.text.strip('"')  # Remove aspas se vier

        nome_arquivo = limpar_nome(f"|{item['descricao']}.{item['extensao']}")

        # Verifica se tem o arquivo na pasta da atividade
        caminho_destino_template = os.path.join(destino_dir, limpar_nome(f"{nome_arquivo}"))
        if os.path.isfile(caminho_destino_template):
            continue
        else:
            print(f"\n\n    >>> Não foi encontrado na pasta de destino: {os.path.isfile(caminho_destino_template)} - {caminho_destino_template}")
        

        print(f"\n\n    >>> Baixando Template [{os.path.isfile(caminho_destino_template)}]: {caminho_destino_template}")
        req_download_material = requests.get(url=url_download_material, headers={"User-Agent": headers["User-Agent"]})
        
        try:
            with open(caminho_destino_template, "wb") as f:
                f.write(req_download_material.content)
            print(f"    >>>> Finalizou de baixar template")
        
        except Exception as err:
            log_grava(err=err)

        # Verifica se pelo menos um template foi feito download
        if os.path.isfile(caminho_destino_template):
            
            dados_drive_disciplina['atualizar_discursiva'] = True
            # print(f"Arquivo salvo na atividade: {caminho_pdf_destino}")

def baixar_material_disciplina(self,**kwargs):
    print("Entrou aqui 00.3.1")
    atividades=kwargs['atividades']
    disciplina_rastreio=kwargs['disciplina_rastreio']
    ano_rastreio = kwargs['ano_rastreio']
    modulo_rastreio = kwargs['modulo_rastreio']
    dados_drive_disciplina=kwargs['dados_drive_disciplina']
    cd_shortname_rastreio=kwargs['cd_shortname_rastreio']

    try:
        print("\n\n      Executar downloads:")

        for atividade in atividades:

            if not verificar_data_inicio(atividade['dataInicial'],data_base_str=self.data_base):
            # False caso a atividade ainda não tenha iniciado
                continue
            
            try:
                print("\n\n   >>> Baixar livros:", self.config['cb_download_livros'], not atividade.get('atualizar_livros'))
                if self.config['cb_download_livros']:
                    if not atividade.get('atualizar_livros'):
                    # Finalizou o rastreio das atividades, agora vai baixar o material (Livros e Templates)
                        download_material(
                            self,
                            disciplina_rastreio=disciplina_rastreio,
                            ano_rastreio=ano_rastreio,
                            modulo_rastreio=modulo_rastreio,
                            dados_drive_disciplina=dados_drive_disciplina,
                            cd_shortname_rastreio=cd_shortname_rastreio
                        )
                        atividade['atualizar_livros'] = True

                elif atividade.get('atualizar_livros'):
                    print("      Livros já foram baixados")

                else:
                    print("      >> A opção de baixar LIVROS está desabilitada.")

            except KeyError as err:
                log_grava(err=err,msg=f"Erro [6107]")
                # Ocorreu falha na busca pelas questões da atividade
                # então não foram geradas as chaves para a atividade 
                continue
            
            except Exception as err:
                log_grava(err=err,msg=f"Erro [5107]")
                continue

            try:
                print("\n\n  >>>Baixar Templates:", self.config['cb_material_atualizar'], atividade.get('atualizar_templates'))
                if self.config['cb_material_atualizar']:
                    if not atividade.get('atualizar_templates'):
                        download_templates(
                            self,
                            ano_rastreio=ano_rastreio,
                            modulo_rastreio=modulo_rastreio,
                            disciplina_rastreio=disciplina_rastreio,
                            dados_drive_disciplina=dados_drive_disciplina,
                            cd_shortname_rastreio=cd_shortname_rastreio
                        )

                        print(f"    >>> Finalizou de Baixar templates de {disciplina_rastreio}")
                        atividade['atualizar_templates'] = True
                
                elif atividade.get('atualizar_templates'):
                    print("      Templates já atuaizados")
                else:
                    print("      >> A opção de atualizar MATERIAL está desabilitada.\n\n")

            except KeyError as err:
                # Ocorreu falha na busca pelas questões da atividade
                # então não foram geradas as chaves para a atividade
                log_grava(err=err,msg=f"Erro [6109]")
                continue

            break


    except Exception as err:
        log_grava(err=err)


def listar_templates(itens):

    # Palavras que DEVEM aparecer na descrição (case insensitive)
    palavras_incluir = [
        "MAPA", "TEMPLATE", "FORMULÁRIO", "FORMULARIO",
        "MODELO", "PADRÃO","PADRAO",
        "AE1","AE01", "ATIVIDADE 1","ATIVIDADE 1",
        "AE2","AE02", "ATIVIDADE 2","ATIVIDADE 2",
        "AE3","AE03", "ATIVIDADE 3","ATIVIDADE 3",
        "RELATÓRIO","RELATORIO","ERRATA",
        "PORTFOLIO","PORTFOLIO","ROTEIRO"
    ]
    # Palavras que NÃO PODEM aparecer na descrição (case insensitive)
    palavras_excluir = [
        "COMO ENVIAR", "REVISÃO DE QUESTÕES", "CRACHÁ"
    ]

    # Função de filtro
    def filtrar_item(item):
        desc = item["descricao"].upper()

        if not any(p in desc for p in palavras_incluir):
            return False
        if any(p in desc for p in palavras_excluir):
            return False
        return True

    # Extração dos dados
    resultados = []
    for item in itens:
        if filtrar_item(item):
            hash_arquivo = item["nomeArquivoHash"]
            descricao = item['descricao']
            # Prioriza a extensão do campo tipo, se houver, senão pega do titulo
            extensao = item.get("tipo")
            try:
                if not extensao:
                    extensao = re.search(r'\.([a-z0-9]+)$', item["titulo"], re.I)
                    extensao = extensao.group(1) if extensao else ""
                resultados.append({'nome_arquivo':f'{hash_arquivo}.{extensao}','descricao':descricao,'extensao':extensao})
            except TypeError as err:
                # log_grava(err=err)
                print("\n    >>>> VIDEOOO: ", item,"\n\n")
                # print("bbbbb",itens)
    return resultados
