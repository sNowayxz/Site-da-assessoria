from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from function_format import delete_all_row, formatar_cor_linha
from system.logger import log_grava
from system.system import t


def fcn_w_preenche_tela_cadastro(self):
    # Apaga dados da tabela
    delete_all_row(self)

    # dados = sorted(self.dados_alunos)
    for ra in self.dados_alunos:
        
            # Obtém dados do aluno
            nome = self.dados_alunos[ra]['NOME']
            ra = self.dados_alunos[ra]['RA']
            curso = self.dados_alunos[ra]['CURSO']
            senha = self.dados_alunos[ra]['SENHA']
            situacao = self.dados_alunos[ra]['SITUAÇÃO']

            if self.dados_alunos[ra]['SENHA_OK'] == 'OK':
                verifica_senha = "OK"
                
            elif self.dados_alunos[ra]['SENHA_OK'] == 'FALHOU SENHA':
                verifica_senha = "Senha Incorreta"

            else:
                verifica_senha = "Senha não verificada"

            # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
            rowPosition = self.ui.tableWidget.rowCount()

            # Insere uma nova linha na tabela
            self.ui.tableWidget.insertRow(rowPosition)

            # cria o elemento referente a uma célula da tabela, para que seja possível formatar a célula
            item_nome = QTableWidgetItem(nome)
            try:
                item_curso = QTableWidgetItem(self.curso_nome[curso])
            except KeyError:
                if not curso or curso == "NÃO RASTREADO":
                    item_curso = QTableWidgetItem("Não foi possível acessar o portal")
                else:
                    item_curso = QTableWidgetItem("Pedir para o Alex cadastrar: "+curso)
            


            item_ra = QTableWidgetItem(ra)
            item_situacao = QTableWidgetItem(situacao)
            item_senha = QTableWidgetItem("")

            # centraliza H e V o widget no item
            item_nome.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            item_curso.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ra.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_situacao.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_nome.setFlags(item_nome.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_curso.setFlags(item_curso.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_ra.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_situacao.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)

            
            # adiciona os atríbutos atribuídos a "item" na célula da Tabela
            self.ui.tableWidget.setItem(rowPosition,0, item_nome)
            self.ui.tableWidget.setItem(rowPosition,1, item_ra)
            self.ui.tableWidget.setItem(rowPosition,2, item_curso)
            self.ui.tableWidget.setItem(rowPosition,3, item_situacao)

            # Adiciona o Icone de Check ou de UnCheck
            # e formata a cor das linhas
            self.ui.tableWidget.setItem(rowPosition,4, item_senha) # precisa alocar um valor, para após inserir o Icon
            if situacao == "FORMADO":
                formatar_cor_linha(self,rowPosition,"azul")
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Check))
            
            elif situacao == "TRANCADO":
                formatar_cor_linha(self,rowPosition,"laranja")
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Check))

            elif "Alex" in item_curso.text():
                formatar_cor_linha(self,rowPosition,"verde")
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Check))
                
            elif verifica_senha == "OK":
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Check))

            else:
                formatar_cor_linha(self,rowPosition,"vermelho")
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Uncheck)) 
                # define a cor de fundo como vermelha da linha


def fcn_w_preenche_tela_mensalistas(self, **kwargs):
    
    # Apaga dados da tabela
    # delete_all_row(self)

    # nome_arquivo = kwargs.get('nome',None)

    # dados = sorted(self.dados_alunos)
    for ra in self.dados_alunos:
        
            # Obtém dados do aluno
            # nome = nome_arquivo if nome_arquivo else self.dados_alunos[ra]['NOME']
            nome = self.dados_alunos[ra]['NOME']
            ra = self.dados_alunos[ra]['RA']
            curso = self.dados_alunos[ra]['CURSO']
            senha = self.dados_alunos[ra]['SENHA']
            atividades = self.dados_alunos[ra]['ATIVIDADES']

            # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
            rowPosition = self.ui.tableWidget.rowCount()

            # Insere uma nova linha na tabela
            self.ui.tableWidget.insertRow(rowPosition)

            # cria o elemento referente a uma célula da tabela, para que seja possível formatar a célula
            item_nome = QTableWidgetItem(nome)
            try:
                item_curso = QTableWidgetItem(self.curso_nome[curso])
            except KeyError:
                if not curso or curso == "NÃO RASTREADO":
                    item_curso = QTableWidgetItem("Não foi possível acessar o portal")
                else:
                    item_curso = QTableWidgetItem("Pedir para o Alex cadastrar: "+curso)
            
            item_ra = QTableWidgetItem(ra)
            item_senha = QTableWidgetItem("")

            # centraliza H e V o widget no item
            item_nome.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            item_curso.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ra.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_nome.setFlags(item_nome.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_curso.setFlags(item_curso.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_ra.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            

            
            # adiciona os atríbutos atribuídos a "item" na célula da Tabela
            self.ui.tableWidget.setItem(rowPosition,0, item_nome)
            self.ui.tableWidget.setItem(rowPosition,1, item_ra)
            self.ui.tableWidget.setItem(rowPosition,2, item_curso)

            self.ui.tableWidget.setItem(rowPosition,4, item_senha)
            icon=self.ui.tableWidget.item(rowPosition,4)
            icon.setIcon(QIcon(self.ui.icon_Check))


            for atividade in atividades:

                if "Sem atividades pendentes" in atividades[atividade]:
                    continue

                try:

                    # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
                    rowPosition = self.ui.tableWidget.rowCount()

                    # Insere uma nova linha na tabela
                    self.ui.tableWidget.insertRow(rowPosition)

                    # cria o elemento referente a uma célula da tabela, para que seja possível formatar a célula
                    item_atividade = QTableWidgetItem(atividade)
                    item_prazo = QTableWidgetItem(atividades[atividade])
                    
                    item_atividade.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item_prazo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    item_atividade.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)
                    item_prazo.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)

                    self.ui.tableWidget.setItem(rowPosition,2, item_atividade)
                    self.ui.tableWidget.setItem(rowPosition,3, item_prazo)

                    lista_prazo = [ " 5 dias" ," 4 dias" ," 3 dias" , " 2 dias" , " 1 dia" , "um dia" , "hora" , "minutos"]

                    if any(prazo in  atividades[atividade] for prazo in lista_prazo):
                    # "25 dias" in atividades[atividade] or "2 dias" in atividades[atividade] or "1 dia" in atividades[atividade] or "um dia" in atividades[atividade] or "hora" in atividades[atividade] or "minutos" in atividades[atividade]:
                        formatar_cor_linha(self,rowPosition,"vermelho")
                
                except RuntimeError as err:
                    log_grava(err=err)
                    t(2)
            
            # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
            rowPosition = self.ui.tableWidget.rowCount()

            # Insere uma nova linha na tabela
            self.ui.tableWidget.insertRow(rowPosition)

            # separa conta dos alunos
            formatar_cor_linha(self,rowPosition,"preto")

            
                
def fcn_w_preenche_tela_atividades(self):
    # Apaga dados da tabela
    delete_all_row(self)

    # dados = sorted(self.dados_alunos)
    for nome in self.dados_alunos:
        if nome != "0000-procurar":

            # Obtém dados do aluno
            curso = ""
            if 'CURSO' in self.dados_alunos[nome]:
                curso = self.dados_alunos[nome]['CURSO']
            
            ra = self.dados_alunos[nome]['LOGIN']
            senha = self.dados_alunos[nome]['SENHA']
            situacao = self.dados_alunos[nome]['SITUAÇÃO']

            if self.dados_alunos[nome]['SENHA_OK'] == 'OK':
                verifica_senha = "OK"
            else:
                verifica_senha = "Senha Incorreta"

            # Obtém a quantidade de linhas na tabela atualmente (a cada ciclo)
            rowPosition = self.ui.tableWidget.rowCount()

            # Insere uma nova linha na tabela
            self.ui.tableWidget.insertRow(rowPosition)

            # cria o elemento referente a uma célula da tabela, para que seja possível formatar a célula
            item_nome = QTableWidgetItem(nome)
            item_curso = QTableWidgetItem(self.curso_nome[curso])
            item_ra = QTableWidgetItem(ra)
            item_situacao = QTableWidgetItem(situacao)
            item_senha = QTableWidgetItem("")
            

            # centraliza H e V o widget no item
            item_nome.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            item_curso.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ra.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_situacao.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_nome.setFlags(item_nome.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_curso.setFlags(item_curso.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_ra.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)
            item_situacao.setFlags(item_ra.flags() ^ Qt.ItemFlag.ItemIsSelectable)

            
            # adiciona os atríbutos atribuídos a "item" na célula da Tabela
            self.ui.tableWidget.setItem(rowPosition,0, item_nome)
            self.ui.tableWidget.setItem(rowPosition,1, item_ra)
            self.ui.tableWidget.setItem(rowPosition,2, item_curso)
            self.ui.tableWidget.setItem(rowPosition,3, item_situacao)

            # Adiciona o Icone de Check ou de UnCheck
            self.ui.tableWidget.setItem(rowPosition,4, item_senha) # precisa alocar um valor, para após inserir o Icon
            if verifica_senha == "OK":
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Check))
            else:
                formatar_cor_linha(self,rowPosition,"vermelho")
                icon=self.ui.tableWidget.item(rowPosition,4)
                icon.setIcon(QIcon(self.ui.icon_Uncheck)) 
                # define a cor de fundo como vermelha da linha
      
def fcn_w_insere_tabela_tela_atividades(self, info):
    self.ui.tabela_registro.insertItem(0, info)
