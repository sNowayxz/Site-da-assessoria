import importlib
import os

STYLE = """"""

# Caminho relativo, considerando o local do script atual
dir_atual = os.path.dirname(os.path.abspath(__file__))
dir_componentes = os.path.join(dir_atual, 'componentes')

# Listando todos os arquivos no diretório especificado
files = os.listdir(dir_componentes)

# Extraindo o nome dos arquivos sem a extensão
nomes_componentes = [os.path.splitext(file)[0] for file in files if file.endswith('.py')]

# Imprimindo os nomes dos componentes
for nome in nomes_componentes:
    nome_file_componente = f"gui.componentes.{nome}"
    modulo = importlib.import_module(nome_file_componente)
    # print(f"Módulo {nome_file_componente} carregado com sucesso.")
    STYLE += modulo.STYLE
