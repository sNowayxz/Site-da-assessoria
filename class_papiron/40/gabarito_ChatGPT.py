from PyQt6.QtCore import QObject, pyqtSignal
import traceback
import random
import string

import requests as rq
from requests_toolbelt import MultipartEncoder
from bs4 import BeautifulSoup as BS

from function_bd import integridade_bd, save_json
from dict_lista_curso import dict_curso_sigla_nome
from functions.curso import dict_curso
from system.chrome import login_papiron, t
from system.logger import log_grava

keys_exclusao = ["STATUS_ATIVIDADE", "ID_URL", "LISTA_ID_URL", "DT_INICIO", "DT_FIM"]
FACULDADE = "UNICESUMAR"

class RotinasGabarito(QObject):
    finished = pyqtSignal()

    updateProgress_gabarito = pyqtSignal(int, str)

    def __init__(self, ui, cursos, modulo, username, password, i, config):
        super().__init__()
        self.ui = ui
        self.cursos = cursos
        self.username = username
        self.password = password
        self.i = i
        self.config = config
        self.modulos_abertos = config['MODULOS_ABERTOS']
        self.url_base = "https://www.modelitos.com.br"
        self.lista_exclusiva = [item.strip().upper() for item in self.config.get('postar_cursos', '').split(',') if item.strip()]

    def run_enviar_gabaritos(self):
        try:
            headers = login_papiron(self.username, self.password, self.url_base)
            cursos_apelido = dict_curso(opcao=5)

            for sigla in self.cursos:
                for modulo in self.modulos_abertos:
                    data, path_file = integridade_bd(sigla, modulo)
                    if not data or not data.get(sigla):
                        self.emitir_status(1, f"Não há dados do Curso: {sigla}")
                        continue

                    self.processar_dados(headers, data, path_file, sigla, modulo, cursos_apelido)
                    self.emitir_status(1, f"[{sigla}] Salvando informações no Banco de Dados:")
                    save_json(data, path_file)
                    print(f"Finalizou: {sigla}\n{' x - ' * 10}")

        except KeyError as err:
            self.tratar_erro(err, "[PAPIRON] - Falha no login Papiron")

        except Exception as err:
            self.tratar_erro(err, f">>>>>> FALHA NO CURSO: {sigla if 'sigla' in locals() else 'SEM SIGLA'}")

    def processar_dados(self, headers, data, path_file, sigla, modulo, cursos_apelido):
        for curso in data:
            if self.lista_exclusiva and curso not in self.lista_exclusiva:
                continue
            if curso == 'GERAL' and not self.config['cb_geral']:
                continue

            print(f"\n  - {self.i}: INICIANDO O ENVIO DOS GABARITOS EM: {cursos_apelido[sigla]}")

            for disciplina in data[curso]:
                if self.config['disciplina_unica'] and self.config['disciplina_unica'].upper() != disciplina.upper():
                    continue
                if self.config['cb_scg'] and "SEMANA DE CONHECIMENTOS GERAIS" not in disciplina:
                    continue
                if not self.config['cb_scg'] and "SEMANA DE CONHECIMENTOS GERAIS" in disciplina:
                    continue

                if modulo in data[curso][disciplina]:
                    atividades = data[curso][disciplina][modulo]['ATIVIDADE']
                    for atividade in atividades:
                        if atividade in keys_exclusao:
                            continue
                        self.processar_atividade(headers, data, data[curso][disciplina][modulo], path_file, atividade, curso, disciplina)

    def processar_atividade(self, headers, data, modulo_data, path_file, atividade, curso, disciplina):
        print("    >>", atividade)
        atividade_data = modulo_data['ATIVIDADE'][atividade]

        for questao in atividade_data:
            if questao in keys_exclusao:
                continue
            data_questao = atividade_data[questao]
            if data_questao['ESTILO'] != 'QUESTIONARIO':
                continue

            id_url_questao = data_questao.get('ID_URL')
            if not id_url_questao:
                continue

            gabarito = data_questao.get('GABARITO')
            if not gabarito:
                continue

            if data_questao.get("GABARITO_OK"):
                if self.config['cb_corrige_gabarito']:
                    try:
                        self.corrigir_gabarito(headers, id_url_questao, data, data_questao, path_file, atividade, questao)
                    except InterruptedError:
                        return
                    except Exception as err:
                        log_grava(err=err)
                continue

            url_gabarito = f"{self.url_base}/atividades/form/gabarito_automatico"
            r = self.enviar_gabarito(headers, id_url_questao, gabarito, url_gabarito, questao)
            if r.status_code == 200:
                data_questao['GABARITO_OK'] = "OK"
                print(f"         >> Envio do gabarito finalizado com sucesso: {curso} - {disciplina} - {atividade} {id_url_questao}")
            else:
                print(f"         >> ERRO AO ENVIAR O GABARITO [CODE00]: {id_url_questao}")
                t(30)
            save_json(data, path_file)

    def enviar_gabarito(self, headers, id_url, gabarito, url, enunciado):
        r = rq.get(url, headers=headers)
        soup = BS(r.content, "html.parser")
        token = soup.find("input", {"name": "csrfmiddlewaretoken"})['value']
        
        fields = {
            'csrfmiddlewaretoken': token,
            'id_url': id_url,
            'gabarito': gabarito,
            'enunciado': enunciado,
        }

        boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
        m = MultipartEncoder(fields=fields, boundary=boundary)

        headers_b = {
            "Accept": "*/*",
            "Cookie": headers['Cookie'],
            "Content-Length": str(len(str(m))),
            "Host": "www.papiron.com.br",
            "Origin": "https://www.papiron.com.br",
            "Referer": url,
            "Content-Type": m.content_type,
            "Upgrade-Insecure-Requests": "1"
        }

        return rq.post(url, headers=headers_b, data=m, allow_redirects=False, timeout=60)

    def corrigir_gabarito(self, headers, id_url, data, data_questao, path_file, atividade, questao):
        url_verificacao = f"{self.url_base}/atividades/idurl/{id_url}"
        r = rq.get(url_verificacao)

        if r.status_code == 404:
            data_questao['ID_URL'] = None
            raise InterruptedError
        elif r.status_code != 200:
            t(60)
            return

        url_gabarito = f"{self.url_base}/atividades/gabarito/{id_url}"
        r_gab = rq.get(url_gabarito, headers=headers)

        if r_gab.status_code in [200, 404]:
            gabarito = data_questao['GABARITO']
            r_envio = self.enviar_gabarito(headers, id_url, gabarito, questao)
            if r_envio.status_code == 200:
                data_questao['GABARITO_OK'] = "OK"
                save_json(data, path_file)
        elif r.status_code == 200:
            data_questao['GABARITO_OK'] = "OK"
            save_json(data, path_file)

    def emitir_status(self, code, msg):
        self.updateProgress_gabarito.emit(code, msg)

    def tratar_erro(self, err, mensagem):
        msg = "".join(traceback.format_exception(type(err), err, err.__traceback__)) + mensagem
        self.emitir_status(1000, mensagem)
        self.finished.emit()
        print(msg)
        log_grava(msg=msg)