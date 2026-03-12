from system.chrome import t


def dict_curso(opcao, **kwargs):
    """
    Opções:

    1 - Siglas

    2 - Nome Cursos Completos

    3 - Apelidos

    4 - Nome Completo : Apelido (curso_nome.json)

    5 - Sigla : Apelido (curso_sigla_nome.json)

    6 - Nome Completo : Sigla (curso_sigla.json)
    
    
    
    """
    # Obtém a dict dos cursos cadastrados no Papiron
    data_cursos = dict_cursos_papiron()

    if opcao == 1:

        # Usando compreensão de lista para coletar todas as siglas
        data = [detalhes['sigla'] for chave, detalhes in data_cursos.items() if detalhes['sigla']]

    elif opcao == 2:

        # Usando compreensão de lista para coletar todas as siglas
        data = [detalhes['nome'] for chave, detalhes in data_cursos.items() if detalhes['nome']]

    elif opcao == 3:

        # Usando compreensão de lista para coletar todas as siglas
        data = [detalhes['apelido'] for chave, detalhes in data_cursos.items() if detalhes['apelido']]

    elif opcao == 4:
        data = {}
        for curso in data_cursos:
            data[data_cursos[curso]['nome']]=data_cursos[curso]['apelido']
    
    elif opcao == 5:
        data = {}
        for curso in data_cursos:
            data[data_cursos[curso]['sigla']]=data_cursos[curso]['apelido']

    elif opcao == 6:
        data = {}
        for curso in data_cursos:
            data[data_cursos[curso]['nome']]=data_cursos[curso]['sigla']

    else:
        data = data_cursos

    
    return data

def dict_cursos_papiron():

    import requests as rq

    url_base ="https://www.papiron.com.br"

    url_cursos = url_base+"/atividades/listar/listar_cursos_bd"

    cont = 4

    while cont:
        try:
            r = rq.get(url_cursos, allow_redirects=False)
            data_cursos = r.json()
            break
        except Exception as err:
            t(15*(4-cont))
            cont-=1
            if not cont:
                raise ConnectionError
            
    return data_cursos

