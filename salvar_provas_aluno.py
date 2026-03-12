import sys
import os
import requests

# Inicia sessão HTTP
session = requests.Session()

from system.requests_unicesumar import (
    login,
    gerar_enconding,
    imprimir_prova,
    listar_provas_disponíveis,
)

import requests

def main():
    disciplina = input("  >> Informe a disciplina: ")
    ra = input("  >> Informe RA do aluno: ")
    senha = input("  >> SENHA: ")

    try:
        headers = login(ra=ra, senha=senha)
        token = headers["Authorization"]

        # listar_provas_disponíveis(headers=headers)

        url_encerradas = (
            "https://studeoapi.unicesumar.edu.br/agendamento-api-controller/api/avaliacao-encerrada/busca-lista-encerrada-web/?page=0"
        )

        headers["Host"] = "studeoapi.unicesumar.edu.br"

        response = session.get(url_encerradas, headers=headers)
        response.raise_for_status()

        dados = response.json()
        provas = dados["itens"]

        avaliacoes_realizadas = [
            item for item in provas if item.get("dsStatus") == "Avaliação Realizada"
        ]

        for av in avaliacoes_realizadas:
            disciplina_portal = av["nmDisciplina"]
            id_questao = av["idQuestionarioAluno"]
            # print(disciplina_portal)

            if disciplina_portal == disciplina:
                print(f"    >> Encontrou {disciplina}")

                encoding = gerar_enconding(
                    ra=ra, id_questao=id_questao, token=token
                )
                imprimir_prova(
                    encoding=encoding, disciplina=disciplina_portal, id=id_questao
                )
    except Exception as err:
        print(f"Erro para RA {ra}: {err}")


if __name__ == "__main__":
    main()
