import os

from function_bd import abre_json, save_json

PATH_BD = os.path.abspath(os.getcwd())+"\\BD\\atividades\\user_data.json"
data = abre_json(PATH_BD)

def cb_default(self, key):
    self.config[key] = None
    data[key] = None

def cb_chrome(self):
    
    if self.ui.cb_chrome.isChecked():
        self.config ['cb_chrome_view']  = True
    else:
        self.config ['cb_chrome_view'] = False

    data['cb_chrome_view'] = self.config ['cb_chrome_view'] 
    save_json(data,PATH_BD)

    print(f"Chrome_view: {self.config ['cb_chrome_view']}")

def cb_download_livros(self):
    
    cb_default(self, 'cb_download_livros')

    if self.ui.cb_download_livros.isChecked():
        self.download_livros = True
        self.config['cb_download_livros'] = True
        
    else:
        self.download_livros = False
        self.config['cb_download_livros']  = False
    
    data['cb_download_livros'] = self.config ['cb_download_livros'] 
    save_json(data,PATH_BD)

    print(f"Donwload Livros: {self.config ['cb_download_livros']}")

def cb_novos_cadastros(self):

    self.config['cb_atualizar_novos_cadastros']

    if self.ui.cb_novos.isChecked():
        self.config['cb_atualizar_novos_cadastros'] = True
    else:
        self.config['cb_atualizar_novos_cadastros'] = False

    data['cb_atualizar_novos_cadastros'] = self.config ['cb_atualizar_novos_cadastros'] 
    save_json(data,PATH_BD)

    print(f"Apenas novos: {self.config['cb_atualizar_novos_cadastros']}")
   
def cb_material_atualizar(self):
    if self.ui.cb_material_atualizar.isChecked():
        self.config['cb_material_atualizar'] = True
    else:
        self.config['cb_material_atualizar'] = False

    data['cb_material_atualizar'] = self.config ['cb_material_atualizar'] 
    save_json(data,PATH_BD)

    print(f"Material Didático atualizar : {self.config['cb_material_atualizar']}")


def cb_scg_atualizar(self):
    
    if self.ui.cb_scg.isChecked():
        self.config['cb_scg'] = True
    else:
        self.config['cb_scg'] = False

    data['cb_scg'] = self.config ['cb_scg'] 
    save_json(data,PATH_BD)

    print(f"Semana de Conhecimentos Gerais : {self.config['cb_scg']}")


def cb_geral_atualizar(self):
    
    if self.ui.cb_geral.isChecked():
        self.config['cb_geral'] = True
    else:
        self.config['cb_geral'] = False

    data['cb_geral'] = self.config ['cb_geral'] 
    save_json(data,PATH_BD)

    print(f"Atividades Gerais : {self.config['cb_geral']}")


def cb_ect_atualizar(self):
    
    if self.ui.cb_ect.isChecked():
        self.config['cb_ect'] = True
    else:
        self.config['cb_ect'] = False

    data['cb_ect'] = self.config ['cb_ect'] 
    save_json(data,PATH_BD)

    print(f"Período com AV de ECT : {self.config['cb_ect']}")

def cb_verificar_idurl_site(self):
    
    if self.ui.cb_verificar_idurl_site.isChecked():
        self.config['cb_verificar_idurl_site'] = True
    else:
        self.config['cb_verificar_idurl_site'] = False

    data['cb_verificar_idurl_site'] = self.config ['cb_verificar_idurl_site'] 
    save_json(data,PATH_BD)

    print(f"Verificar se está publicado no site : {self.config['cb_verificar_idurl_site']}")


def cb_discursivas(self):
    
    if self.ui.cb_discursivas.isChecked():
        self.config['cb_discursivas'] = True
    else:
        self.config['cb_discursivas'] = False

    data['cb_discursivas'] = self.config ['cb_discursivas'] 
    save_json(data,PATH_BD)

    print(f"Verificar se está publicado no site : {self.config['cb_discursivas']}")



def cb_corrige_gabarito(self):
    
    if self.ui.cb_corrige_gabarito.isChecked():
        self.config['cb_corrige_gabarito'] = True
    else:
        self.config['cb_corrige_gabarito'] = False

    data['cb_corrige_gabarito'] = self.config ['cb_corrige_gabarito'] 
    save_json(data,PATH_BD)

    print(f"Verificar e corrigir se o gabarito estiver errado: {self.config['cb_corrige_gabarito']}")
