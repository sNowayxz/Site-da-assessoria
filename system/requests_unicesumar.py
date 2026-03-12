import requests
from system.pastas import localizar_desktop

def login(ra,senha):

    # Endpoint de login
    url = "https://studeoapi.unicesumar.edu.br/auth-api-controller/auth/token/create"

    # Payload do formulário
    payload = {
        "username": ra,
        "password": senha
    }

    # Headers
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://studeo.unicesumar.edu.br",
        "Referer": "https://studeo.unicesumar.edu.br/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }

    # Se quiser manter a sessão (cookies, etc.)
    session = requests.Session()

    # Requisição de login
    response = session.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        dados = response.json()
        token = dados.get("token")
        # print(f"TOKEN DE AUTENTICAÇÃO: {token}")
        headers["Authorization"] = f"{token}"
        print(f"   >>> Efetuou login com sucesso: {response.status_code}")
        return headers
    else:
        print(f"   >>> [FALHA]: Erro no login/senha: {response.status_code}")
        print(response.text)
        raise ValueError
    
def gerar_enconding(ra,id_questao,token):
    import base64

    # Dados do método
    ra = ra
    idquest = id_questao
    token = token

    # Monta a string no formato correto
    dados = f"{ra}|{idquest}|{token}"

    # Codifica em base64
    encoding = base64.b64encode(dados.encode()).decode()

    return encoding

def imprimir_prova(encoding, disciplina, id):
    import requests
    import os
    import urllib.parse

    url_copia_prova = 'https://intranet.unicesumar.edu.br/sistemas/bancoDeQuestoes/webservice/impressao/avaliacao-digital-copia.php'
    data = {"encoding": encoding}
    response = requests.post(url_copia_prova, data=data)
    html = response.text
    disciplina = disciplina.replace(":","").replace("/","").replace("\\","")

    # Remove scripts e imagens indesejadas
    retirar_trecho = """<script>
        function mensagem(){
            alert('É proibida a cópia e a reprodução deste conteúdo.');
            return false;
        }
        
        function bloquearCopia(Event){
            var Event = Event ? Event : window.event;
            var tecla = (Event.keyCode) ? Event.keyCode : Event.which;
            if(tecla == 17){
                mensagem();
            }
        }
    </script>"""

    retirar_trecho2 = """<script>
    document.onkeypress = bloquearCopia;
    document.onkeydown = bloquearCopia;
    document.oncontextmenu = mensagem;
</script>"""

    retirar_trecho3 = ".img-bloq"
    retirar_trecho4 = "<img src=\"spacer.gif\" title=\"É proibida a cópia e a reprodução deste conteúdo.\" class=\"img-bloq\" />"
    retirar_trecho5 = "<img src=\"unicesumar-logo.png\" style=\"width:150px;\">"

    html = (
        html.replace(retirar_trecho, "")
        .replace(retirar_trecho2, "")
        .replace(retirar_trecho3, ".xxx")
        .replace(retirar_trecho4, "")
        .replace(retirar_trecho5, "")
    )

    html_total = f"""<html><head><meta charset="utf-8"></head><body>
                {html}
                </body></html>
            """

    # Caminho da pasta Papiron no Desktop
    desktop = localizar_desktop()
    pasta_destino = os.path.join(desktop, "Papiron","Provas")

    # Cria a pasta se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Caminho final do arquivo
    caminho_html = os.path.join(pasta_destino, f"{disciplina}_{id}.html")

    with open(caminho_html, "w", encoding="utf-8") as f:
        f.write(html_total)

    print(f"     >>> Prova salva em: {caminho_html}")


def listar_provas_disponíveis(headers):

    
    # Se quiser manter a sessão (cookies, etc.)
    session = requests.Session()

    url_encerradas = "https://studeoapi.unicesumar.edu.br/agendamento-api-controller/api/avaliacao-encerrada/busca-lista-encerrada/"

    headers["Host"] = "studeoapi.unicesumar.edu.br"

    response = session.get(url_encerradas, headers=headers)

    # print(f"Status: {response.status_code}")
    # print(f"Resposta: {response.text}")

    dados = (response.json())[0]


def compilador_arquivos(disciplina, deletar):
    import glob
    import os

    # Caminho do Desktop do usuário
    disciplina = disciplina.replace(":","").replace("/","").replace("\\","")
    desktop = localizar_desktop()
    pasta_destino = os.path.join(desktop, "Papiron","Provas")

    # Cria a pasta se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Padrão dos arquivos a serem juntados (considera que eles estão na pasta de trabalho atual)
    padrao = os.path.join(pasta_destino, f"{disciplina}_*.html")

    # Nome do arquivo compilado
    arquivo_compilado = os.path.join(pasta_destino, f"{disciplina}_00001.html")

    # Lista todos arquivos que batem com o padrão
    arquivos = glob.glob(padrao)

    with open(arquivo_compilado, "w", encoding="utf-8") as saida:
        for arquivo in arquivos:
            with open(arquivo, "r", encoding="utf-8") as entrada:
                conteudo = entrada.read()
                saida.write(conteudo)
            try:
                if deletar:
                    os.remove(arquivo)
            except PermissionError:
                pass

    print(f"Arquivos compilados em XXX {arquivo_compilado}")
