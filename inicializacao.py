import json
import os
import traceback
from tkinter.tix import Tree

from function_bd import abre_json, save_json
from system.crypto import recodification
from system.logger import log_grava
from system.pastas import verifica_pastas


def chaves_obrigatorias():
    return [
        'cb_chrome_view',
        'cb_atualizar_novos_cadastros',
        'cb_salvar',
        'cb_material_atualizar',
        'cb_download_livros',
        'cb_verificar_idurl_site',
        'cb_discursivas',
        'usuario',
        'password',
        'menu_processos'
        
    ]

def verifica_arq_config():
    path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
    if not os.path.isfile(path_file):
        data = {
            'usuario': '' ,
            'password': '',
            'cb_chrome_view':False,
            'cb_salvar': False,
            'cb_atualizar_novos_cadastros':False,
            'cb_material_atualizar':False,
            'cb_download_livros':True,
            'menu_processos':1,
            'menu_modulo':'2023/54',
        }

    else:
        data = abre_json(path_file)
        keys = chaves_obrigatorias()
        for chave in keys:
            if not chave in data:
                if chave == 'usuario' or chave == 'password':
                    data['usuario'] = ''
                    data['password'] = ''
                elif 'menu_' in chave:
                    data['menu_processos'] = 1
                    data['menu_modulo'] = '2023/52'
                elif 'cb_' in chave:
                    data['cb_chrome_view'] = False
                    data['cb_atualizar_novos_cadastros'] = False
                    data['cb_material_atualizar'] = False
                    if data['usuario'] and data['password']:
                        data['cb_salvar'] = True
                    else:
                        data['cb_salvar'] = False

    save_json(data,path_file)

def verifica_arq_modulo():
    import shutil
    path_dir = os.getcwd()
    path_file = path_dir+'\\BD\\atividades\\modulo.json'
    path_file_alunos_ra = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_ra.json"
    path_file_alunos_mensalistas = os.path.abspath(os.getcwd())+"\\BD\\alunos\\dados_aluno_mensalista.json"
    path_file_logins = os.path.abspath(os.getcwd())+"\\BD\\alunos\\logins_falhas.txt"
    verifica_pastas(pasta = path_dir+'\\BD\\atividades')
    verifica_pastas(pasta = path_dir+'\\BD\\cursos')
    verifica_pastas(pasta = path_dir+'\\BD\\alunos')

        
    # obter o diretório pai do diretório atual
    parent_dir = os.path.dirname(os.getcwd())

    # caminho para a pasta ui_files
    path_ui_files = os.path.join(os.path.dirname(path_dir), "ui_files")

    # Verifica a existência dos arquivos iniciais
    data = {}
    if not os.path.isfile(path_file_alunos_ra):
        save_json(data=data,path_file=path_file_alunos_ra)
    
    if not os.path.isfile(path_file_alunos_mensalistas):
        save_json(data=data,path_file=path_file_alunos_mensalistas)

    if not os.path.isfile(path_file):
        log_grava(msg="[INICIALIZAÇÃO - ARQ MÓDULOS]: Criando arquivo de módulos\n")
        data = {
            '2023/51':{'SITUAÇÃO':'ABERTO'},
            '2023/52':{'SITUAÇÃO':'FECHADO'},    
            '2023/53':{'SITUAÇÃO':'FECHADO'},
            '2023/54':{'SITUAÇÃO':'FECHADO'}
        }

        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(data, f ,ensure_ascii=False)
    else:
        log_grava(msg="[INICIALIZAÇÃO - ARQ MÓDULOS]: Arquivo de módulos registrados")
        with open(path_file, encoding='utf-8') as json_file:
            data = json.load(json_file)

    if not os.path.isfile(path_file_logins):
        with open(path_file_logins, 'w+'):
            pass
    
    # for pasta in data:
    #     path_dir_mod = path_dir+'\\BD\\atividades\\'+pasta.replace('/','')
    #     if not os.path.isdir(path_dir_mod):
    #         os.mkdir(path_dir_mod)

def verifica_css():
    import shutil

    path_dir = os.getcwd()
    path_file = path_dir+'\\ui_files\\unicesumar.css'
    dir_css = os.path.join(os.path.expanduser("~"), "Desktop\\Papiron\\files")
    path_css = dir_css+"\\unicesumar.css"
    
    # Verifica se existe a pasta para inserir o css, e pode criar
    verifica_pastas(pasta = dir_css)

    if not os.path.isfile(path_css):
        shutil.copy(path_file,path_css)

def tela_config_iniciais(self):

    # Aloca uma dict vazia para alocar os atributos das configurações iniciais
    self.config = {}

    # Obtem os registros salvos do usuário
    path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
    data = abre_json(path_file)

    # Desempacotando possíveis elementos
    for dado in data:
        self.config[dado] = data[dado]

def tela_cadastro_render(self):

    try:
        # Renderiza os elementos salvos:
        self.ui.cb_chrome.setChecked(self.config['cb_chrome_view'])
        self.ui.cb_novos.setChecked(self.config['cb_atualizar_novos_cadastros'])

    except KeyError as err:
        log_grava(err=err)
        print(err)


def tela_mensalistas_render(self):

    try:
        # Renderiza os elementos salvos:
        self.ui.cb_chrome.setChecked(self.config['cb_chrome_view'])
        self.ui.cb_novos.setChecked(self.config['cb_atualizar_novos_cadastros'])

    except KeyError as err:
        log_grava(err=err)
        print(err)

def tela_atividades_render(self):

    try:

        # if self.config['cb_salvar']:
        #     username = recodification(self.config['usuario'])
        #     password = recodification(self.config['password'])
        #     self.ui.cb_salvar.setChecked(True)
        # else:
        #     username = ''
        #     password = ''
        #     self.ui.cb_salvar.setChecked(False)

        # self.ui.input_login.setText(username)
        # self.ui.input_senha.setText(password)

        # Renderiza os elementos CHECKBOX e MENU salvos, na tela inicial:
        # Se for inserir NÃO esqueca do "cb_"
        # self.ui.cb_chrome.setChecked(self.config['cb_chrome_view'])
        self.ui.menu_processos.setCurrentText(str(self.config['menu_processos']))
        # self.ui.cb_scg.setChecked(self.config['cb_scg'])
        self.ui.cb_geral.setChecked(self.config['cb_geral'])
        self.ui.cb_download_livros.setChecked(self.config['cb_download_livros']) 
        self.ui.cb_material_atualizar.setChecked(self.config['cb_material_atualizar']) 
        # self.ui.cb_ect.setChecked(self.config['cb_ect'])
    
    except KeyError as err:
        log_grava(err=err)
        print(err)


def tela_envio_render(self):

    try:

        if self.config['cb_salvar']:
            username = recodification(self.config['usuario'])
            password = recodification(self.config['password'])
            self.ui.cb_salvar.setChecked(True)
        else:
            username = ''
            password = ''
            self.ui.cb_salvar.setChecked(False)

        self.ui.input_login.setText(username)
        self.ui.input_senha.setText(password)

        # Renderiza os elementos CHECKBOX e MENU salvos, na tela inicial:
        # Se for inserir NÃO esqueca do "cb_"
        self.ui.menu_processos.setCurrentText(str(self.config['menu_processos']))
        self.ui.cb_scg.setChecked(self.config['cb_scg'])
        self.ui.cb_verificar_idurl_site.setChecked(self.config['cb_verificar_idurl_site']) 
        self.ui.cb_discursivas.setChecked(self.config['cb_discursivas']) 
        self.ui.cb_salvar.setChecked(self.config['cb_salvar'])
        self.ui.cb_corrige_gabarito.setChecked(self.config['cb_corrige_gabarito'])
    
    except KeyError as err:
        log_grava(err=err)
        print(err)


def salva_config_user(**kwargs):

    # Obtem os registros salvos do usuário
    path_file = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
    with open(path_file, encoding='utf-8') as json_file:
            data = json.load(json_file)

    for kwarg in kwargs:
        data[kwarg] = kwargs[kwarg]

    # Se não houver falhas ele salva os novos dados no BD.
    with open(path_file, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii = False)
