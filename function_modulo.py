def extrair_disciplinas_por_modulo(disciplinas, modulo_alvo):
    disciplinas_encontradas = []
    # Itera sobre as categorias de disciplinas (matriculada, cursada, etc.)
    for categoria, detalhes in disciplinas.items():
        # Itera sobre as disciplinas individuais dentro de cada categoria
        for nome_disciplina, detalhes_disciplina in detalhes.items():
            if detalhes_disciplina.get('MODULO') == modulo_alvo:
                disciplinas_encontradas.append(nome_disciplina)
    return disciplinas_encontradas