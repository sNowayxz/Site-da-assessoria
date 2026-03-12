from xhtml2pdf import pisa

import io
import os
import re
import traceback
from datetime import datetime

from system.logger import log_grava



# ----------------------------
# Helpers de encoding/arquivo
# ----------------------------
def _read_text_file_smart(path: str) -> tuple[str, str]:
    """
    Lê um arquivo de texto tentando:
    1) UTF-8 (com BOM) via 'utf-8-sig'
    2) UTF-8 normal
    3) Latin-1 (não falha em bytes estranhos)
    Retorna: (conteudo, encoding_usado)
    """
    # 1) UTF-8 com BOM (muito comum em arquivos salvos no Windows)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read(), "utf-8-sig"
    except UnicodeDecodeError:
        pass

    # 2) UTF-8 normal
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), "utf-8"
    except UnicodeDecodeError:
        pass

    # 3) latin-1: garante leitura (mesmo que alguns caracteres fiquem “estranhos”)
    with open(path, "r", encoding="latin-1") as f:
        return f.read(), "latin-1"


def _safe_shorten_filename(path: str, ext: str, max_len: int = 240) -> str:
    """
    Encurta o caminho (principalmente nome do arquivo) para evitar erro de caminho longo no Windows.
    Mantém a extensão.
    """
    path = os.path.abspath(path)
    base_dir = os.path.dirname(path)
    filename = os.path.splitext(os.path.basename(path))[0]

    short_name = filename[: max(1, max_len - len(ext) - 1)]
    return os.path.join(base_dir, f"{short_name}{ext}")


# ----------------------------
# HTML -> PDF
# ----------------------------
def html_to_pdf(html_path: str, pdf_path: str) -> bool:
    """
    Converte arquivo HTML em PDF.
    Retorna True/False.
    """
    content = None
    encoding = None

    try:
        content, encoding = _read_text_file_smart(html_path)

    except FileNotFoundError:
        # tenta renomear (sua lógica original)
        try_html = _safe_shorten_filename(html_path, ".html", max_len=240)
        try_pdf = _safe_shorten_filename(pdf_path, ".pdf", max_len=240)

        print(f"\n>>> Tentando renomear\n  {try_html}\n  {try_pdf}")
        log_grava(msg=f"Tentando renomear HTML/PDF por FileNotFoundError: {try_html} / {try_pdf}")

        content, encoding = _read_text_file_smart(try_html)
        html_path, pdf_path = try_html, try_pdf

    except UnicodeDecodeError as err:
        # em tese não deve acontecer por causa do latin-1, mas mantemos por segurança
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print("Erro de decodificação detectado. Detalhes:\n", msg)
        log_grava(err=err, msg="Erro de decodificação detectado")

        # fallback forte
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        encoding = "utf-8"

    except Exception as err:
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print("Erro inesperado lendo HTML:\n", msg)
        log_grava(err=err, msg="Erro inesperado lendo HTML")
        return False

    if not content:
        print("Erro: O conteúdo HTML está vazio ou não pôde ser lido.")
        log_grava(msg=f"HTML vazio ou não lido: {html_path}")
        return False

    # Gera PDF
    try:
        # garante fechamento do arquivo PDF
        with open(pdf_path, "w+b") as result_file:
            # OBS: pisaDocument aceita string em src
            # encoding ajuda quando há caracteres fora do ascii
            pisa_status = pisa.pisaDocument(
                src=content,
                dest=result_file,
                encoding=encoding or "utf-8",
            )

        if pisa_status.err:
            log_grava(msg=f"pisaDocument retornou err={pisa_status.err} para {html_path}")
            print(f"Atenção: pisaDocument terminou com err={pisa_status.err}")

        return not bool(pisa_status.err)

    except Exception as e:
        # fallback sem encoding explícito
        try:
            with open(pdf_path, "w+b") as result_file:
                pisa_status = pisa.pisaDocument(src=content, dest=result_file)
            if pisa_status.err:
                log_grava(msg=f"Fallback pisaDocument err={pisa_status.err} para {html_path}")
            return not bool(pisa_status.err)
        except Exception as err2:
            msg = "".join(traceback.format_exception(type(err2), err2, err2.__traceback__))
            print("Erro ao converter HTML para PDF:\n", msg)
            log_grava(err=err2, msg="Erro ao converter HTML para PDF")
            return False


# Mantive sua função "meu" mas agora chamando a versão robusta
def html_to_pdf_meu(html_path: str, pdf_path: str) -> bool:
    return html_to_pdf(html_path, pdf_path)


def gera_html(curso, disciplina, atividade, modulo, cabecalho, body):
    html_inic = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8" />'
        "<title>PAPIRON</title></head><body>"
    )
    html_fim = "</body></html>"
    html = html_inic + str(cabecalho) + str(body) + html_fim

    path_file_html = os.path.abspath(os.getcwd()) + r"\BD\atividades\html.html"
    safe_modulo = str(modulo).replace("/", "")
    path_file_pdf = (
        os.path.abspath(os.getcwd())
        + "\\BD\\atividades\\"
        + f"{curso} - {disciplina} - {atividade} - {safe_modulo}.pdf"
    )

    os.makedirs(os.path.dirname(path_file_html), exist_ok=True)

    with io.open(path_file_html, "w", encoding="utf-8") as arquivo:
        arquivo.write(html)

    return html_to_pdf(path_file_html, path_file_pdf)


# ----------------------------
# Render do questionário
# ----------------------------
def ms_to_str(ms):
    if not ms:
        return ""
    return datetime.fromtimestamp(int(ms) // 1000).strftime("%d/%m/%Y %H:%M")


def render_questionario_to_html(data):
    html = f"""
    <html lang="pt-br">
    <head>
      <meta charset="utf-8">
      <title>{data["descricao"]}</title>
      <style>
        body {{
          background: #fff;
          color: #222;
          font-family: Arial, Helvetica, sans-serif;
          font-size: 12pt;
        }}
        .cabecalho {{
          display: flex;
          align-items: flex-start;
          gap: 1em;
          margin-bottom: 0.5em;
        }}
        .logo-unicesumar {{
          height: 45px;
          margin-right: 1.2em;
        }}
        .papiron-endereco {{
          font-size: 0.93em;
          color: #1463c1;
          font-weight: bold;
          margin-top: 0.2em;
        }}
        .titulo-pagina {{
          font-size: 1.32em;
          font-weight: bold;
          margin-bottom: 0.3em;
          padding-bottom: 0.23em;
          border-bottom: 4px solid #1463c1;
          color: #232d37;
        }}
        .info-top {{
          border: 1px solid #bbb;
          padding: 1em;
          margin-bottom: 1.2em;
          background: #fafbfc;
        }}
        .info-top b {{ color: #232d37; }}
        .info-top span {{
          margin-right: 2em;
          display: inline-block;
          min-width: 130px;
        }}
        .questao {{
          margin-bottom: 1.7em;
          page-break-inside: avoid;
        }}
        .questao.anulada {{
          background: #ffeaea !important;
          border: 2.5px solid #ee2222;
          border-radius: 8px;
          padding-top: 0.8em;
          padding-bottom: 0.8em;
        }}
        .questao-numero {{
          font-size: 1em;
          font-weight: bold;
          color: #222;
          margin-bottom: 0;
          padding-bottom: 0.15em;
          border-bottom: 3px solid #1463c1;
          width: fit-content;
        }}
        .enunciado {{
          border: 1px solid #bbb;
          border-radius: 4px;
          margin-bottom: 0.85em;
          margin-top: 0.6em;
          padding: 1em 1.2em 0.8em 1.2em;
          font-size: 1.02em;
          text-align: justify;
          background: #fff;
        }}
        .alternativas-bloco {{
          border: 1px solid #bbb;
          border-radius: 4px;
          background: #fff;
          margin-bottom: 0.2em;
          padding: 0.3em 1.2em 0.8em 1.2em;
        }}
        .alternativas-titulo {{
          font-weight: bold;
          color: #222;
          margin-top: 0.5em;
          margin-bottom: 0.5em;
          padding-bottom: 0.15em;
          border-bottom: 3px solid #1463c1;
          width: fit-content;
          font-size: 1.05em;
        }}
        .alternativas-lista {{
          display: block;
          margin: 0.2em 0 0 0;
          padding: 0;
        }}
        .alternativa-linha {{
          display: table-row;
          margin-bottom: 0.9em;
          height: 2.2em;
        }}
        .alternativa-texto {{
          color:black;
          display: table-cell;
          vertical-align: middle;
          padding-left: 0.7em;
          padding-bottom: 0.5em;
          padding-top: 0.5em;
          border-radius: 12px;
        }}
        .alternativa-gabarito {{
          background: #fff940 !important;
          font-weight: bold;
          color: #664d00;
          border-radius: 5px;
        }}
      </style>
    </head>
    <body>
      <div class="questionario">
        <div class="cabecalho">
          <img class="logo-unicesumar" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAhQAAABfCAMAAACHpK5R...">
          <div>
            <div style="font-size:1.25em; color:#444;">
              <b>UniCesumar</b> - Ensino a Distância -
              <span class="papiron-endereco"> https://www.papiron.com.br </span>
            </div><br>
          </div>
        </div>
        <div class="titulo-pagina">{data["descricao"]}</div>
        <div class="info-top">
          <span><b>Período:</b> {ms_to_str(data.get("dataInicial"))} a {ms_to_str(data.get("dataFinal"))}</span>
          <span><b>Status:</b> ABERTO</span>
          <span><b>Nota máxima:</b> {data.get("notaQuestionario","-")}</span>
          <span><b>Gabarito:</b> {f"Será liberado no dia {ms_to_str(data.get('dataGabarito'))}" if data.get('dataGabarito') else "--"}</span>
        </div>
    """

    questoes = list(data["QUESTOES"].values())
    for idx, questao in enumerate(questoes, start=1):
        try:
            anulada_class = "anulada" if questao.get("anulada") else ""
        except AttributeError:
            msg = f"ID errado {data.get('descricao','')} {questao}"
            log_grava(msg=msg)
            continue

        html += f"""
        <div class="questao {anulada_class}">
          <div class="questao-numero">{idx}ª QUESTÃO{" - ANULADA" if questao.get("anulada") else ""}</div>
          <div class="enunciado">{questao["descricaoHtml"]}</div>
          <div class="alternativas-bloco">
            <div class="alternativas-titulo">ALTERNATIVAS</div>
            <div class="alternativas-lista">
        """

        if questao.get("alternativaList"):
            for alt in questao["alternativaList"]:
                alt_text = re.sub(r"^<p[^>]*>|</p>$", "", alt["descricao"].strip(), flags=re.IGNORECASE)
                alt_id = alt.get("idAlternativa")

                if questao.get("gabarito") and alt_id == questao.get("gabarito_id"):
                    alt_extra_class = "alternativa-gabarito"
                    alt_input = "checked"
                else:
                    alt_extra_class = ""
                    alt_input = ""

                html += f"""
                <div class="alternativa-linha {alt_extra_class}">
                  <span class="alternativa-texto">
                    <input type="radio" {alt_input}> {alt_text}
                  </span>
                </div>
                """

        html += """
            </div>
          </div>
        </div>
        """

    html += """
      </div>
    </body>
    </html>
    """
    return html

# print("importou3.1")
# import chardet
# print("importou3.2")
# from xhtml2pdf import pisa
# print("importou3.3")
# import codecs
# print("importou3.4")
# import traceback
# print("importou3.5")

# from system.logger import log_grava
# print("importou3.6")

# def html_to_pdf(html, pdf):

#     try:
#         # Detecta a codificação automaticamente com chardet
#         with open(html, 'rb') as f:
#             raw_data = f.read()
#         charset = chardet.detect(raw_data)['encoding']
        
#         with codecs.open(html, mode="r", encoding=charset) as source_html:
#             content = source_html.read()

#         result_file = open(pdf, "w+b")  # <-- GARANTE ABERTURA AQUI

#     except UnicodeDecodeError as err:
#         msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
#         print("Erro de decodificação detectado. Detalhes:\n", msg)
#         log_grava(err=err, msg="Erro de decodificação detectado. Detalhes:\n")
        
#         with open(html, mode="r", encoding='utf-8', errors='ignore') as source_html:
#             content = source_html.read()
        
#         result_file = open(pdf, "w+b")  # <-- ADICIONADO AQUI TAMBÉM
    
#     except FileNotFoundError:
#         html = html[:240] + ".html"
#         pdf = pdf[:240] + ".pdf"
#         print(f"\n     >>> Tentando renomear\n  {html} \n  {pdf}")
#         charset = chardet.detect(open(html, 'rb').read())['encoding']
#         with codecs.open(html, mode="r", encoding=charset) as source_html:
#             content = source_html.read()
        
#         result_file = open(pdf, "w+b")  # <-- ADICIONADO AQUI TAMBÉM

#     # Agora com certeza temos content e result_file
#     if content is not None:
#         try:
#             pisa.pisaDocument(
#                 src=content,
#                 dest=result_file,
#                 encoding=charset
#             )
#         except Exception as e:
#             print("Erro ao converter HTML para PDF:", e)
#             pisa.pisaDocument(
#                 src=content,
#                 dest=result_file
#             )
#     else:
#         print("Erro: O conteúdo HTML está vazio ou não pôde ser lido.")

#     result_file.close()


# def html_to_pdf_meu(html,pdf):
#     import codecs

#     import chardet
#     from xhtml2pdf import pisa

#     try:
#         charset = chardet.detect(open(html, 'rb').read())['encoding']
#         source_html = codecs.open(html, mode="r", encoding=charset)
#         content = source_html.read()         # the HTML to convert
#         source_html.close()                  # close template file
#         result_file = open(pdf, "w+b")
    
#     except UnicodeDecodeError as err:
#         import traceback
#         msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
#         # ctypes.windll.user32.MessageBoxW(0, "Houve um erro na decodificação, seu texto pode conter falhas.\n\nEvite copiar e colar texto de outras fontes","Erro de Decoficação UTF-8",0)
#         source_html = codecs.open(html, mode="r")

#     except FileNotFoundError:
        
#         html = html[:200]+".html"
#         pdf = pdf[:200]+".pdf"
#         print(f"\n     >>> Tentando renomear\n {html} \n{pdf}")
#         charset = chardet.detect(open(html, 'rb').read())['encoding']
#         source_html = codecs.open(html, mode="r", encoding=charset)
#         content = source_html.read()         # the HTML to convert
#         source_html.close()                  # close template file
#         result_file = open(pdf, "w+b")
    
#     try:
        
#         pisa.pisaDocument(
#             src=content,                # the HTML to convert
#             dest=result_file,       # file handle to recieve result
#             encoding=charset
#         )
        
#     except:
#         print("Erro de Content Type - Verficar html_to_pdf")
#         pisa.pisaDocument(
#             src = content,          # the HTML to convert
#             dest=result_file,           # file handle to recieve result
#         )

#     result_file.close()

# def gera_html(curso, disciplina, atividade, modulo, cabecalho,body):
#     import io
#     import os
    
#     html_inic = "<!DOCTYPE html><html><head><meta charset=\"UTF-8\" /><title>PAPIRON</title></head><body>"
#     html_fim = "</body></html>"
#     html = html_inic+str(cabecalho)+str(body)+html_fim
#     path_file_html = os.path.abspath(os.getcwd())+'\\BD\\atividades\\html.html'  
#     path_file_pdf = os.path.abspath(os.getcwd())+'\\BD\\atividades\\'+curso+" - "+disciplina+" - "+atividade+" - "+modulo.replace("/","")+'.pdf'

    
#     with io.open(path_file_html, 'w', encoding='utf8') as arquivo:
#         arquivo.write(html)

#     html_to_pdf(path_file_html, path_file_pdf)

# import re
# from datetime import datetime

# def ms_to_str(ms):
#     if not ms:
#         return ""
#     return datetime.fromtimestamp(int(ms)//1000).strftime('%d/%m/%Y %H:%M')

# def render_questionario_to_html(data):
#     html = f'''
#     <html lang="pt-br">
#     <head>
#       <meta charset="utf-8">
#       <title>{data["descricao"]}</title>
#       <style>
#         body {{
#           background: #fff;
#           color: #222;
#           font-family: Arial, Helvetica, sans-serif;
#           font-size: 12pt;
#         }}
#         .cabecalho {{
#           display: flex;
#           align-items: flex-start;
#           gap: 1em;
#           margin-bottom: 0.5em;
#         }}

#         /* Troque aqui o src da logo! */
#         .logo-unicesumar {{
#           height: 45px;
#           margin-right: 1.2em;
#         }}

#         .papiron-endereco {{
#           font-size: 0.93em;
#           color: #1463c1;
#           font-weight: bold;
#           margin-top: 0.2em;
#         }}

#         .titulo-pagina {{
#           font-size: 1.32em;
#           font-weight: bold;
#           margin-bottom: 0.3em;
#           padding-bottom: 0.23em;
#           border-bottom: 4px solid #1463c1;
#           color: #232d37;
#         }}
#         .info-top {{
#           border: 1px solid #bbb;
#           padding: 1em;
#           margin-bottom: 1.2em;
#           background: #fafbfc;
#         }}
#         .info-top b {{ color: #232d37; }}
#         .info-top span {{
#           margin-right: 2em;
#           display: inline-block;
#           min-width: 130px;
#         }}
#         .questao {{
#           margin-bottom: 1.7em;
#           page-break-inside: avoid;
#         }}
#         .questao.anulada {{
#           background: #ffeaea !important;
#           border: 2.5px solid #ee2222;
#           border-radius: 8px;
#           padding-top: 0.8em;
#           padding-bottom: 0.8em;
#         }}
#         .questao-numero {{
#           font-size: 1em;
#           font-weight: bold;
#           color: #222;
#           margin-bottom: 0;
#           padding-bottom: 0.15em;
#           border-bottom: 3px solid #1463c1;
#           width: fit-content;
#         }}
#         .enunciado {{
#           border: 1px solid #bbb;
#           border-radius: 4px;
#           margin-bottom: 0.85em;
#           margin-top: 0.6em;
#           padding: 1em 1.2em 0.8em 1.2em;
#           font-size: 1.02em;
#           text-align: justify;
#           background: #fff;
#         }}
#         .alternativas-bloco {{
#           border: 1px solid #bbb;
#           border-radius: 4px;
#           background: #fff;
#           margin-bottom: 0.2em;
#           padding: 0.3em 1.2em 0.8em 1.2em;
#         }}
#         .alternativas-titulo {{
#           font-weight: bold;
#           color: #222;
#           margin-top: 0.5em;
#           margin-bottom: 0.5em;
#           padding-bottom: 0.15em;
#           border-bottom: 3px solid #1463c1;
#           width: fit-content;
#           font-size: 1.05em;
#         }}
#         .alternativas-lista {{
#           margin: 0.2em 0 0 0;
#           padding: 0;
#           display: flex;
#           flex-direction: column;
#           gap: 0.4em;
#         }}
#         .alternativas-lista label {{
#           display: flex;
#           align-items: flex-start;
#           gap: 0.65em;
#           font-size: 1em;
#           padding: 0.4em 0.5em 0.4em 0.3em;
#           border-radius: 5px;
#           cursor: pointer;
#           user-select: none;
#         }}
#         .alternativas-lista label:hover {{
#           background: #f6f7fb;
#         }}
#         .alternativas-lista input[type="radio"] {{
#           accent-color: #1463c1;
#           margin-right: 0.6em;
#         }}
#         .alternativas-lista {{
#             display: block;
#             margin: 0.2em 0 0 0;
#             padding: 0;
#         }}
#         .alternativa-linha {{
#             display: table-row;
#             margin-bottom: 0.9em;
#             height: 2.2em;
#         }}
#         .alternativa-linha input[type="radio"] {{
#             display: table-cell;
#             vertical-align: top;
#             margin-right: 0.6em;
#         }}
#         .alternativa-texto {{
#             color:black;
#             display: table-cell;
#             vertical-align: middle;
#             padding-left: 0.7em;
#             padding-bottom: 0.5em;
#             padding-top: 0.5em;
#             border-radius: 12px;
#         }}
#         .alternativa-gabarito {{
#             background: #fff940 !important;
#             font-weight: bold;
#             color: #664d00;
#             border-radius: 5px;
#             /* pode customizar mais se quiser */
#         }}
#       </style>
#     </head>
#     <body>
#       <div class="questionario">
#         <div class="cabecalho">
#           <!-- Substitua o src abaixo pelo seu logo base64 ou url -->
#           <img src="data:image/png;base64,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">
     
#           <div>
#             <div style="font-size:1.25em; color:#444;">
#               <b>UniCesumar</b> - Ensino a Distância -
#               <span class="papiron-endereco"> https://www.papiron.com.br </span>
#             </div><br>
#           </div>
#         </div>
#         <div class="titulo-pagina">
#           {data["descricao"]}
#         </div>
#         <div class="info-top">
#           <span><b>Período:</b> {ms_to_str(data.get("dataInicial"))} a {ms_to_str(data.get("dataFinal"))}</span>
#           <span><b>Status:</b> ABERTO</span>
#           <span><b>Nota máxima:</b> {data.get("notaQuestionario","-")}</span>
#           <span><b>Gabarito:</b> {f"Será liberado no dia {ms_to_str(data.get('dataGabarito'))}" if data.get('dataGabarito') else "--"}</span>
#         </div>
#     '''

#     questoes = list(data["QUESTOES"].values())
#     for idx, questao in enumerate(questoes, start=1):
#         # Verifica se a questão é anulada
#         try:
#           anulada_class = "anulada" if questao.get("anulada") else ""
#         except AttributeError:
#             # Para retirar erros, mas pode ser retirado mais para frente
#             import winsound
#             winsound.Beep(3000,2000)
#             msg = f"\n\n\n ID errado {data['descricao']} {questao}\n\n"
#             log_grava(msg=msg)
#             continue
        
#         html += f'''
#         <div class="questao {anulada_class}">
#           <div class="questao-numero">{idx}ª QUESTÃO{" - ANULADA" if questao.get("anulada") else ""}</div>
#           <div class="enunciado">{questao["descricaoHtml"]}</div>
#           <div class="alternativas-bloco">
#             <div class="alternativas-titulo">ALTERNATIVAS</div>
#             <div class="alternativas-lista">
#         '''
#         if questao["alternativaList"]:
#             for alt in questao["alternativaList"]:
#                 alt_text = re.sub(r'^<p[^>]*>|</p>$', '', alt["descricao"].strip(), flags=re.IGNORECASE)
#                 alt_id = alt.get("idAlternativa")
#                 # Destaca gabarito, se houver
#                 if questao.get("gabarito") and alt_id == questao["gabarito_id"]:
#                     alt_extra_class = "alternativa-gabarito"
#                     alt_input = "checked"
#                 else:
#                     alt_extra_class = ""
#                     alt_input = ""
#                 html += f'''
#                 <div class="alternativa-linha {alt_extra_class}">
#                     <span class="alternativa-texto"><input type="radio" {alt_input}>{alt_text}</span>
#                 </div>
#                 '''
#         html += '''
#             </div>
#           </div>
#         </div>
#         '''
#     html += '''
#       </div>
#     </body>
#     </html>
#     '''
#     return html


          