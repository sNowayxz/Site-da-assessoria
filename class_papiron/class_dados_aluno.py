from class_papiron.class_error import AlunoNotScrappedError

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from function import atualizar_soup, ult_div

class Aluno:
    """
    Classe que contém todos os atributos necessários de um aluno
    Realiza médotos próprios de uma publicação
    """
    def __init__(self,driver):
        import time

        from class_papiron.class_error import AlunoNotScrappedError

        cont = 3
        while cont:
            ult_div(driver)
            soup = atualizar_soup(driver)
            try:
                self.nome = soup.find("h5",{"ng-bind":"$ctrl.usuarioLogado.nmUsuario"}).text
                self.curso = soup.find("dd",{"ng-show":"$ctrl.usuarioLogado.cursoList.length == 1"}).text
                self.ra = soup.find("dd",{"ng-bind":"$ctrl.usuarioLogado.cdUsuario"}).text
                break
            
            except AttributeError:
                cont-=1
                time.sleep(5)
                if not cont:
                    print("ERRO no NOME")
                    raise AlunoNotScrappedError
                else:
                    print(f"   >>> Tenta obter novamente o NOME  [{cont}]")

    def __str__(self):
        return str(self.nome)+" - "+str(self.curso)+" - "+str(self.ra)


class Mensalista:
    """
    Classe que contém todos os atributos necessários de um aluno
    Realiza médotos próprios de uma publicação
    """
    def __init__(self,driver):
        import time
        cont = 2
        while cont:
            ult_div(driver)
            soup = atualizar_soup(driver)
            try:
                self.nome = soup.find("h5",{"ng-bind":"$ctrl.usuarioLogado.nmUsuario"}).text
                self.curso = soup.find("dd",{"ng-show":"$ctrl.usuarioLogado.cursoList.length == 1"}).text
                self.ra = soup.find("dd",{"ng-bind":"$ctrl.usuarioLogado.cdUsuario"}).text
                
                xpath_btn = "//a[@ng-if='$ctrl.exibir']"
                wait = WebDriverWait(driver,15)
                btn_aviso = wait.until(EC.presence_of_element_located((By.XPATH,xpath_btn)))
                driver.execute_script("arguments[0].click();", btn_aviso)

                xtable = "//table[@class='table acomptable']"
                wait.until(EC.presence_of_element_located((By.XPATH,xtable)))

                soup = atualizar_soup(driver)

                lista_atividades = soup.find("table",{"class":"table acomptable"}).find_all("p")
                lista_nome_atividades = soup.find("table",{"class":"table acomptable"}).find_all("span",{"ng-bind-html":"item.nmDisciplina | limitTo:85 "})

                print("atividades:", lista_atividades)
                print("\n nome atividades:", lista_nome_atividades)

                self.atividades = []
                for i , atividade in enumerate(lista_atividades):
                    # if "3 dias" in atividade.text or "2 dias" in atividade.text or "1 dia" in atividade.text or "um dia" in atividade.text or "hora" in atividade.text or "minutos" in atividade.text:
                        self.atividades.append([lista_nome_atividades[i],atividade])

                break
            
            except AttributeError:
                cont-=1
                time.sleep(5)
                if not cont:
                    print("ERRO no NOME")
                    raise AlunoNotScrappedError
                else:
                    print(f"   >>> Tenta obter novamente o NOME  [{cont}]")

            except TimeoutException:

                soup = atualizar_soup(driver)
                elemento = soup.find('div', {'class': 'modal-title text-left', 'id': 'modal-title'})

                if elemento and elemento.find('h4') and 'Acompanhamento de Atividades' in elemento.find('h4').text:
                    print("Acompanhamento de Atividades encontrado!")
                    self.atividades = []
                    break

                else:
                    print("Acompanhamento de Atividades NÃO LOCALIZADO.")
                    cont-=1
                    print("     Erro TimeOutException", cont)
                    if not cont:
                        print("ERRO TimeoutException")
                        raise TimeoutException

    def __str__(self):
        return str(self.nome)+" - "+str(self.curso)+" - "+str(self.ra)


class AlunoScrapped:
    """
    Classe que contém todos os atributos necessários de um aluno
    Realiza médotos próprios de uma publicação
    """
    def __init__(self):
        pass

    def dados(self, nome, curso, ra):
        self.nome = nome
        self.curso = curso
        self.curso_real = curso
        self.ra = ra

    def __str__(self):
        return str(self.nome)+" - "+str(self.curso)+" - "+str(self.ra)
    
class Disciplina:
    """"
    Classe de atributos das disciplinas cursadas pelo aluno
    """
    def __init__(self,disciplina:str,modulo:str,dt_inicio:str, serie_ideal:str, status:str):
        self.disciplina = disciplina.rstrip()
        self.dt_inicio = dt_inicio
        self.dt_fim = None
        self.modulo = modulo
        self.status = status
        self.serie_ideal = serie_ideal
    
    def __str__(self):
        return str(self.disciplina)+" - "+str(self.modulo)+" - "+str(self.dt_inicio)
