import json
import os

from function_bd import save_json
from functions.curso import dict_curso
from function_system import verifica_json


def dict_curso_sigla() -> dict:
    # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla.json"
    cursos = dict_curso(opcao=6)
    # if os.path.isfile(path_file_curso):
    #     with open(path_file_curso, encoding='utf-8') as json_file:
    #         cursos = json.load(json_file)
    return cursos

def dict_curso_nome() -> dict:
    # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_nome.json"
    cursos = dict_curso(opcao=4)
    # if os.path.isfile(path_file_curso):
    #     with open(path_file_curso, encoding='utf-8') as json_file:
    #         cursos = json.load(json_file)
    return cursos

def dict_curso_sigla_nome() -> dict:
    # path_file_curso = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla_nome.json"
    cursos = dict_curso(opcao=5)
    # if os.path.isfile(path_file_curso):
    #     with open(path_file_curso, encoding='utf-8') as json_file:
    #         cursos = json.load(json_file)
    return cursos

def dict_inicial_curso_nome():
    return {"": "", 
        "INDEFINIDO": "Não foi possível entrar no PORTAL",
        "GRADUAÇÃO EM ADMINISTRAÇÃO": "ADMINISTRAÇÃO", 
        "SUPERIOR DE TECNOLOGIA EM AGRONEGÓCIO": "AGRONEGÓCIO", 
        "SUPERIOR DE TECNOLOGIA EM LOGÍSTICA": "LOGÍSTICA", 
        "SUPERIOR DE TECNOLOGIA EM PROCESSOS GERENCIAIS": "PROCESSOS GERENCIAIS", 
        "BACHARELADO EM BIOMEDICINA": "BIOMEDICINA", 
        "BACHARELADO EM FARMACIA": "FARMÁCIA", 
        "BACHARELADO EM NUTRIÇÃO": "NUTRIÇÃO", 
        "BACHARELADO EM ENFERMAGEM": "ENFERMAGEM", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO HOSPITALAR": "GESTÃO HOSPITALAR", 
        "SUPERIOR DE TECNOLOGIA EM PODOLOGIA": "PODOLOGIA", 
        "BACHARELADO EM CIÊNCIAS CONTÁBEIS": "CIÊNCIAS CONTÁBEIS", 
        "BACHARELADO EM CIÊNCIAS ECONÔMICAS": "CIÊNCIAS ECONÔMICAS", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO AMBIENTAL": "GESTÃO AMBIENTAL", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO COMERCIAL": "GESTÃO COMERCIAL", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO PÚBLICA": "GESTÃO PÚBLICA", 
        "SUPERIOR DE TECNOLOGIA EM GASTRONOMIA": "GASTRONOMIA",
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DA QUALIDADE": "GESTÃO DA QUALIDADE", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO FINANCEIRA": "GESTÃO FINANCEIRA", 
        "BACHARELADO EM EDUCAÇÃO FÍSICA": "EDUCAÇÃO FÍSICA", 
        "LICENCIATURA EM EDUCAÇÃO FÍSICA": "EDUCAÇÃO FÍSICA", 
        "BACHARELADO EM MATEMÁTICA": "MATEMÁTICA", 
        "LICENCIATURA EM MATEMÁTICA": "MATEMÁTICA", 
        "LICENCIATURA EM LETRAS PORTUGUÊS-INGLÊS": "LETRAS INGLÊS", 
        "LICENCIATURA EM HISTÓRIA": "HISTÓRIA", 
        "LICENCIATURA EM GEOGRAFIA": "GEOGRAFIA", 
        "GRADUAÇÃO EM PEDAGOGIA": "PEDAGOGIA", 
        "BACHARELADO EM PSICOPEDAGOGIA": "PSICOPEDAGOGIA", 
        "SUPERIOR DE TECNOLOGIA EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS": "ADS - ANÁLISE E DESENVOLVIMENTO DE SISTEMAS", 
        "SUPERIOR EM GESTÃO DA TECNOLOGIA DA INFORMAÇÃO": "TECNOLOGIA DA INFORMAÇÃO", 
        "SUPERIOR DE TECNOLOGIA EM MARKETING": "MARKETING", 
        "BACHARELADO EM JORNALISMO": "JORNALISMO", 
        "GRADUAÇÃO EM ENGENHARIA CIVIL": "ENGENHARIA CIVIL", 
        "GRADUAÇÃO EM ENGENHARIA ELÉTRICA": "ENGENHARIA ELÉTRICA", 
        "GRADUAÇÃO EM ENGENHARIA MECÂNICA": "ENGENHARIA MECÂNICA", 
        "BACHARELADO EM ENGENHARIA DE PRODUÇÃO": "ENGENHARIA DA PRODUÇÃO", 
        "BACHARELADO EM ENGENHARIA SOFTWARE": "ENGENHARIA DO SOFTAWARE", 
        "BACHARELADO EM SERVIÇO SOCIAL": "SERVIÇO SOCIAIS", 
        "SUPERIOR DE TECNOLOGIA EM SEGURANÇA NO TRABALHO": "SEGURANÇA DO TRABALHO", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DE SEGURANÇA PRIVADA": "SEGURANÇA PRIVADA", 
        "SUPERIOR DE TECNOLOGIA EM SEGURANÇA ALIMENTAR": "SEGURANÇA ALIMENTAR", 
        "SUPERIOR DE TECNOLOGIA EM INVESTIGAÇÃO FORENSE E PERÍCIA CRIMINAL": "INVESTIGAÇÃO CRIMINAL", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DE RECURSOS HUMANOS": "RECURSOS HUMANOS", 
        "SUPERIOR DE TECNOLOGIA EM CIÊNCIA DA FELICIDADE": "CIÊNCIA DA FELICIDADE", 
        "SUPERIOR DE TECNOLOGIA EM SECRETARIADO": "SECRETARIADO",
        "LICENCIATURA EM CIÊNCIAS BIOLÓGICAS":"CIÊNCIAS BIOLÓGICAS",
        "SUPERIOR DE TECNOLOGIA EM EMPREENDEDORISMO":"EMPREENDEDORISMO",
        "BACHARELADO EM TEOLOGIA":"TEOLOGIA",
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DA PRODUÇÃO INDUSTRIAL":"GESTÃO DA PRODUÇÃO INDUSTRIAL",
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DA SAÚDE PÚBLICA":"GESTÃO DA SAÚDE PÚBLICA",
        "SUPERIOR DE TECNOLOGIA EM CIÊNCIAS DE DADOS E ANÁLISE DE COMPORTAMENTO":"CIÊNCIAS DE DADOS",
        "SUPERIOR DE TECNOLOGIA EM DESIGN DE INTERIORES":"DESIGN DE INTERIORES",
        "SUPERIOR DE TECNOLOGIA EM CRIMINOLOGIA":"CRIMINOLOGIA",
        "LICENCIATURA EM FÍSICA":"FÍSICA",
        "SUPERIOR DE TECNOLOGIA EM TERAPIAS INTEGRATIVAS E COMPLEMENTARES":"TERAPIAS INTEGRATIVAS",
        "BACHARELADO EM PUBLICIDADE E PROPAGANDA":"PUBLICIDADE E PROPAGANDA",
        "BACHARELADO EM TERAPIA OCUPACIONAL":"TERAPIA OCUPACIONAL",
        "SUPERIOR DE TECNOLOGIA EM AUTOMAÇÃO INDUSTRIAL":"AUTOMAÇÃO INDUSTRIAL",
        "PÓS-GRADUAÇÃO LATO SENSU EM ATENDIMENTO EDUCACIONAL ESPECIALIZADO - EDUCAÇÃO ESPECIAL E INCLUSIVA":"PÓS ATENDIMENTO EDUCACIONAL ESPECIAL",
        "PÓS-GRADUAÇÃO LATO SENSU EM ARTE, CULTURA E EDUCAÇÃO":"PÓS ARTE E CULTURA",
        "PÓS-GRADUAÇÃO LATO SENSU EM ADMINISTRAÇÃO FINANCEIRA":"PÓS ADMINISTRAÇÃO FINANCEIRA",
    }

def dict_inicial_curso_sigla():
    return {
        "GRADUAÇÃO EM ADMINISTRAÇÃO": "ADM",
        "SUPERIOR DE TECNOLOGIA EM AGRONEGÓCIO": "AGRO", 
        "BACHARELADO EM EDUCAÇÃO FÍSICA": "BEDU", "LICENCIATURA EM EDUCAÇÃO FÍSICA": "BEDU", 
        "BACHARELADO EM BIOMEDICINA": "BIOMED", 
        "BACHARELADO EM FARMACIA": "FARM", 
        "BACHARELADO EM NUTRIÇÃO": "NUT", 
        "BACHARELADO EM ENFERMAGEM": "ENF", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO HOSPITALAR": "GH", 
        "BACHARELADO EM CIÊNCIAS CONTÁBEIS": "CCONT", 
        "BACHARELADO EM CIÊNCIAS ECONÔMICAS": "ECO", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO AMBIENTAL": "GAMB", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO PÚBLICA": "GPUB", 
        "SUPERIOR DE TECNOLOGIA EM GASTRONOMIA": "GAST", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DA QUALIDADE": "GQ", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO FINANCEIRA": "GFIN", 
        "BACHARELADO EM MATEMÁTICA": "MAT", "LICENCIATURA EM MATEMÁTICA": "MAT", 
        "GRADUAÇÃO EM PEDAGOGIA": "PED", 
        "BACHARELADO EM PSICOPEDAGOGIA": "PSICOPED", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DE SEGURANÇA PRIVADA": "SPRIV", 
        "SUPERIOR EM GESTÃO DA TECNOLOGIA DA INFORMAÇÃO": "TI", 
        "LICENCIATURA EM HISTÓRIA": "HIST", 
        "LICENCIATURA EM GEOGRAFIA": "GEOG", 
        "SUPERIOR DE TECNOLOGIA EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS": "ADS", 
        "SUPERIOR DE TECNOLOGIA EM PROCESSOS GERENCIAIS": "GPROC", 
        "SUPERIOR DE TECNOLOGIA EM LOGÍSTICA": "LOG", 
        "BACHARELADO EM SERVIÇO SOCIAL": "SSOC", 
        "SUPERIOR DE TECNOLOGIA EM SEGURANÇA NO TRABALHO": "SEG", 
        "SUPERIOR DE TECNOLOGIA EM INVESTIGAÇÃO FORENSE E PERÍCIA CRIMINAL": "IFPC", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO COMERCIAL": "GCOM", "GRADUAÇÃO EM ENGENHARIA ELÉTRICA": "EELE", 
        "GRADUAÇÃO EM ENGENHARIA MECÂNICA": "EMEC", "GRADUAÇÃO EM ENGENHARIA CIVIL": "ECIV", 
        "BACHARELADO EM ENGENHARIA SOFTWARE": "ESOFT", 
        "BACHARELADO EM ENGENHARIA DE PRODUÇÃO": "EPROD", 
        "SUPERIOR DE TECNOLOGIA EM PODOLOGIA": "POD", 
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DE RECURSOS HUMANOS": "RH", 
        "LICENCIATURA EM LETRAS PORTUGUÊS-INGLÊS": "LET", 
        "SUPERIOR DE TECNOLOGIA EM CIÊNCIA DA FELICIDADE": "CFEL", 
        "SUPERIOR DE TECNOLOGIA EM SEGURANÇA ALIMENTAR": "SALIM", 
        "SUPERIOR DE TECNOLOGIA EM SECRETARIADO": "SECR", 
        "SUPERIOR DE TECNOLOGIA EM MARKETING": "MKT", 
        "BACHARELADO EM JORNALISMO": "JOR", 
        "LICENCIATURA EM CIÊNCIAS BIOLÓGICAS":"CBIO",
        "SUPERIOR DE TECNOLOGIA EM EMPREENDEDORISMO":"EMP",
        "BACHARELADO EM TEOLOGIA":"TEOL",
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DA PRODUÇÃO INDUSTRIAL":"GPIN",
        "SUPERIOR DE TECNOLOGIA EM GESTÃO DA SAÚDE PÚBLICA":"GSP",
        "SUPERIOR DE TECNOLOGIA EM CIÊNCIAS DE DADOS E ANÁLISE DE COMPORTAMENTO":"CDAS",
        "SUPERIOR DE TECNOLOGIA EM DESIGN DE INTERIORES":"DI",
        "SUPERIOR DE TECNOLOGIA EM CRIMINOLOGIA":"CRIM",
        "LICENCIATURA EM FÍSICA":"FIS",
        "SUPERIOR DE TECNOLOGIA EM TERAPIAS INTEGRATIVAS E COMPLEMENTARES":"TIOC",
        "BACHARELADO EM PUBLICIDADE E PROPAGANDA":"PP",
        "BACHARELADO EM TERAPIA OCUPACIONAL":"TEOC",
        "SUPERIOR DE TECNOLOGIA EM AUTOMAÇÃO INDUSTRIAL":"AUTIN",
        "PÓS-GRADUAÇÃO LATO SENSU EM ADMINISTRAÇÃO FINANCEIRA":"PADMF",
        "PÓS-GRADUAÇÃO LATO SENSU EM ATENDIMENTO EDUCACIONAL ESPECIALIZADO - EDUCAÇÃO ESPECIAL E INCLUSIVA":"PEDESP",
        "PÓS-GRADUAÇÃO LATO SENSU EM ARTE, CULTURA E EDUCAÇÃO":"PACE",
        }

def dict_inicial_curso_sigla_nome():
    return {
        "ADM": "ADMINISTRAÇÃO",
        "AGRO": "AGRONEGÓCIO", 
        "BEDU": "EDUCAÇÃO FÍSICA", 
        "BIOMED": "BIOMEDICINA", 
        "FARM": "FARMÁCIA", 
        "NUT": "NUTRIÇÃO", 
        "ENF": "ENFERMAGEM", 
        "GH":"GESTÃO HOSPITALAR", 
        "CCONT":"CIÊNCIAS CONTÁBEIS", 
        "ECO":"CIÊNCIAS ECONÔMICAS", 
        "GAMB":"GESTÃO AMBIENTAL", 
        "GPUB":"GESTÃO PÚBLICA", 
        "GAST": "GASTRONOMIA", 
        "GQ": "GESTÃO DA QUALIDADE", 
        "GFIN": "GESTÃO FINANCEIRA", 
        "MAT": "MATEMÁTICA", 
        "PED": "PEDAGOGIA", 
        "PSICOPED": "PSICOPEDAGOGIA", 
        "SPRIV": "SEGURANÇA PRIVADA", 
        "TI": "TECNOLOGIA DA INFORMAÇÃO", 
        "MKT": "MARKETING", 
        "JOR": "JORNALISMO", 
        "EMEC": "ENGENHARIA MECÂNICA", 
        "EELE": "ENGENHARIA ELÉTRICA", 
        "ECIV": "ENGENHARIA CIVIL", 
        "EPROD": "ENGENHARIA DA PRODUÇÃO", 
        "ESOFT": "ENGENHARIA SOFTWARE", 
        "HIST": "HISTÓRIA", "GEOG": "GEOGRAFIA", 
        "ADS": "ADS - ANÁLISE E DESENVOLVIMENTO DE SISTEMAS", 
        "GPROC": "PROCESSOS GERENCIAIS", 
        "LOG": "LOGÍSTICA", 
        "SSOC": "SERVIÇO SOCIAIS", 
        "SEG": "SEGURANÇA DO TRABALHO", 
        "IFPC": "INVESTIGAÇÃO CRIMINAL", 
        "GCOM": "GESTÃO COMERCIAL", 
        "POD": "PODOLOGIA", 
        "RH": "RECURSOS HUMANOS", 
        "LET": "LETRAS INGLÊS", 
        "SALIM": "SEGURANÇA ALIMENTAR", 
        "CFEL": "CIÊNCIA DA FELICIDADE", 
        "SECR": "SECRETARIADO", 
        "CBIO":"CIÊNCIAS BIOLÓGICAS",
        "EMP":"EMPREENDEDORISMO",
        "TEOL":"TEOLOGIA",
        "GPIN":"GESTÃO DA PRODUÇÃO INDUSTRIAL",
        "GSP":"GESTÃO DA SAÚDE PÚBLICA",
        "CDAS":"CIÊNCIAS DE DADOS",
        "DI":"DESIGN DE INTERIORES",
        "CRIM":"CRIMINOLOGIA",
        "PADMF":"PÓS ADMINISTRAÇÃO FINANCEIRA",
        "FIS":"FÍSICA",
        "PEDESP":"PÓS ATENDIMENTO EDUCACIONAL ESPECIAL",
        "PACE":"PÓS ARTE E CULTURA",
        "TIOC":"TERAPIAS INTEGRATIVAS",
        "PP":"PUBLICIDADE E PROPAGANDA",
        "TEOC":"TERAPIA OCUPACIONAL",
        "AUTIN":"AUTOMAÇÃO INDUSTRIAL",
    }

def verifica_inicial_dicts():
    path_file_curso_sigla = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla.json"
    path_file_curso_nome = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_nome.json"
    path_file_curso_sigla_nome = os.path.abspath(os.getcwd())+"\\BD\\cursos\\curso_sigla_nome.json"

    data_curso_sigla_inicial = dict_inicial_curso_sigla()
    data_curso_nome_inicial = dict_inicial_curso_nome()
    data_curso_sigla_nome_inicial = dict_inicial_curso_sigla_nome()

    data_curso_sigla = verifica_json(path_file_curso_sigla)
    data_curso_nome = verifica_json(path_file_curso_nome)
    data_curso_sigla_nome = verifica_json(path_file_curso_sigla_nome)

    for dado in data_curso_sigla_inicial:
        if dado not in data_curso_sigla:
            data_curso_sigla[dado] = data_curso_sigla_inicial[dado]
    save_json(data_curso_sigla, path_file_curso_sigla)

    for dado in data_curso_nome_inicial:
        if dado not in data_curso_nome:
            data_curso_nome[dado] = data_curso_nome_inicial[dado]
    save_json(data_curso_nome, path_file_curso_nome)

    for dado in data_curso_sigla_nome_inicial:
        if dado not in data_curso_sigla_nome:
            data_curso_sigla_nome[dado] = data_curso_sigla_nome_inicial[dado]
    save_json(data_curso_sigla_nome, path_file_curso_sigla_nome)

    
