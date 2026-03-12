import random
import os
import json
import time

from function_bd import abre_json, save_json

def salva_dados(self):
    
    path_file = os.getcwd()+'\\BD\\atividades\\user_data.json'
    username = self.ui.input_login.text()
    password = self.ui.input_senha.text()
    salvar = self.ui.cb_salvar.isChecked()

    if salvar and os.path.isfile(path_file):

        # Salva informações do usuário
        data = abre_json(path_file)
        data['usuario'] = codification(username)
        data['password'] = codification(password)
        data['cb_salvar'] = True
        save_json(data=data, path_file=path_file)


def recupera_dados(self):

    path_file = os.getcwd()+'\\BD\\atividades\\user_data.json'
    username = ''
    password = ''
    
    if os.path.isfile(path_file):
        with open(path_file, encoding='utf-8') as json_file:
            data = json.load(json_file)
        if data['cb_salvar']:
            username = recodification(data['usuario'])
            password = recodification(data['password'])
            self.ui.input_login.setText(username)
            self.ui.input_senha.setText(password)
            self.ui.cb_salva.setChecked(True)
        else:
            username = ''
            password = ''
        
    return username, password


def codification(code):
    import time
    mil = str(int(round(time.time() * 1000)))[-3:]
    aleat = int(mil)%5+2
    alfa = 'E!%Kq8Ow6(pQg1,a}TGR.AX*dC~_;)D9Lcb4MY]hFr{zn$vPZj:52WmeU^kx3=fJHV&u>slNoy0[7S@Bti#<I+-/ '
    alfa = alfa+alfa+alfa+alfa
    code_num = alfa[alfa.find(mil[0])+19]+alfa[alfa.find(mil[1])+23]+alfa[alfa.find(mil[2])+29]
    lcode = list(code)
    new_code = ""
    for i in range (len(lcode)):
        codigo = ''.join(random.choice(alfa) for _ in range(aleat))
        if lcode[i] in alfa:
            new_letter = alfa[alfa.find(lcode[i])+alfa.find(codigo[aleat-1])]
            new_code = new_code+new_letter+codigo 
            #print(new_letter,codigo, "---------",new_code)
        else:
            new_code = new_code+lcode[i]+codigo
    new_code = new_code+code_num
    return new_code[::-1]

def recodification(code):
    import os
    path_env = os.path.abspath(os.getcwd())+"\\"+'.env'

    if code!="":
        try:
            alfa = 'E!%Kq8Ow6(pQg1,a}TGR.AX*dC~_;)D9Lcb4MY]hFr{zn$vPZj:52WmeU^kx3=fJHV&u>slNoy0[7S@Bti#<I+-/ '
            alfa = alfa+alfa+alfa+alfa
            code= code[::-1]
            code_num = alfa[alfa.find(code[-3:][0])-19]+alfa[alfa.find(code[-3:][1])-23]+alfa[alfa.find(code[-3:][2])-29]
            code=code[:-3]
            aleat = int(code_num)%5+2
            lcode = list(code)
            new_code = ""
            for i in range (int(len(code)/((aleat+1)))):
                if lcode[(aleat)*i+1] in alfa:
                    codigo = lcode[(aleat+1)*i]#
                    cod_aleat = code[i+aleat*i+1:(1+aleat)*(i+1)]
                    rcode = lcode[(aleat)+aleat*i+1]
                    l_paradigma = cod_aleat[-1:]
                    l_code = alfa[alfa.rfind(codigo)]
                    new_letter = alfa[alfa.rfind(l_code)-alfa.rfind(l_paradigma)]
                    new_code = new_code+new_letter
                else:
                    new_code = new_code+lcode[(aleat)*i+1]
        except:
            print("\n    Credencial recuperada está danifica ou a chave de criptografia foi atualizada.\
                \n    apague as credencias e insira novamente!\
                \n      >> ATENÇÃO: Altere suas credenciais salvas!")
            return ''
        return new_code
    else:
        return ''
