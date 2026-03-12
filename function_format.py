from PyQt6 import QtGui
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


def formatar_tela_cadastro(self):
    # Formata o tamanho das colunas
    self.ui.tableWidget.setColumnWidth(0, 310 )
    self.ui.tableWidget.setColumnWidth(1, 100)        
    self.ui.tableWidget.setColumnWidth(2, 300)
    self.ui.tableWidget.setColumnWidth(3, 100)
    self.ui.tableWidget.setColumnWidth(4, 50)

    # self.ui.tableWidget_dados.setColumnWidth(0, 100)
    # self.ui.tableWidget_dados.setColumnWidth(1, 250)

    # Formata o Cabeçalho das colunas  
    ## Define como Negrito
    header_font = QFont()  # Cria um objeto QFont para a fonte do cabeçalho
    header_font.setBold(True)

    cols =  self.ui.tableWidget.columnCount()
    for i in range(cols):
        item_header = QTableWidgetItem(self.ui.tableWidget.horizontalHeaderItem(i))
        item_header.setFont(header_font) 
        self.ui.tableWidget.setHorizontalHeaderItem(i,item_header)


    # Adiciona Ícones ao Gui

    # Cria um objeto QPixmap com a imagem que será usada como ícone
    pixmap_Check = QPixmap('ui_files//Check.ico')
    pixmap_Uncheck = QPixmap('ui_files//Uncheck.ico')

    # Cria um objeto QIcon e adiciona o pixmap ao mesmo
    self.ui.icon_Check = QtGui.QIcon()
    self.ui.icon_Check.addPixmap(pixmap_Check)

    self.ui.icon_Uncheck = QtGui.QIcon()
    self.ui.icon_Uncheck.addPixmap(pixmap_Uncheck)


def formatar_tela_mensalistas(self):
    # Formata o tamanho das colunas
    self.ui.tableWidget.setColumnWidth(0, 310 )
    self.ui.tableWidget.setColumnWidth(1, 100)        
    self.ui.tableWidget.setColumnWidth(2, 300)
    self.ui.tableWidget.setColumnWidth(3, 350)
    self.ui.tableWidget.setColumnWidth(4, 50)

    # self.ui.tableWidget_dados.setColumnWidth(0, 100)
    # self.ui.tableWidget_dados.setColumnWidth(1, 250)

    # Formata o Cabeçalho das colunas  
    ## Define como Negrito
    header_font = QFont()  # Cria um objeto QFont para a fonte do cabeçalho
    header_font.setBold(True)

    cols =  self.ui.tableWidget.columnCount()
    for i in range(cols):
        item_header = QTableWidgetItem(self.ui.tableWidget.horizontalHeaderItem(i))
        item_header.setFont(header_font) 
        self.ui.tableWidget.setHorizontalHeaderItem(i,item_header)


    # Adiciona Ícones ao Gui

    # Cria um objeto QPixmap com a imagem que será usada como ícone
    pixmap_Check = QPixmap('ui_files//Check.ico')
    pixmap_Uncheck = QPixmap('ui_files//Uncheck.ico')

    # Cria um objeto QIcon e adiciona o pixmap ao mesmo
    self.ui.icon_Check = QtGui.QIcon()
    self.ui.icon_Check.addPixmap(pixmap_Check)

    self.ui.icon_Uncheck = QtGui.QIcon()
    self.ui.icon_Uncheck.addPixmap(pixmap_Uncheck)


def formatar_tela_atividades(self):
    # Formata o tamanho das colunas
    self.ui.tableWidget.setColumnWidth(0, 80)
    self.ui.tableWidget.setColumnWidth(1, 500)        
    self.ui.tableWidget.setColumnWidth(2, 60)
    self.ui.tableWidget.setColumnWidth(3, 60)


    # Formata o Cabeçalho das colunas  
    ## Define como Negrito
    header_font = QFont()  # Cria um objeto QFont para a fonte do cabeçalho
    header_font.setBold(True)

    cols =  self.ui.tableWidget.columnCount()
    for i in range(cols):
        item_header = QTableWidgetItem(self.ui.tableWidget.horizontalHeaderItem(i))
        item_header.setFont(header_font) 
        self.ui.tableWidget.setHorizontalHeaderItem(i,item_header)

def formatar_cor_linha(self,row,color):
    from PyQt6.QtCore import Qt
    
    cores = {
        "branco": [255, 255, 255],
        "preto": [0, 0, 0],
        "vermelho": [255, 0, 0],
        "verde": [0, 255, 0],
        "azul": [0, 0, 255],
        "amarelo": [255, 255, 0],
        "laranja": [255, 165, 0],
        "roxo": [128, 0, 128]
    }

    # Cria formato da cor da linha
    if color in cores:
        cor = cores[color]
        color = QColor(cor[0], cor[1], cor[2])

    cols =  self.ui.tableWidget.columnCount()
    for i in range(cols):
        try:
            item = QTableWidgetItem(self.ui.tableWidget.item(row,i).text())

            if i:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        except AttributeError:
            item = QTableWidgetItem(self.ui.tableWidget.item(row,i))
        

        # Obtém a paleta atual da célula
        font = item.font()

        item.setBackground(color)
        self.ui.tableWidget.setItem(row, i, item)

        # Define a nova paleta da célula
        item.setFont(font)

        

def delete_all_row(self):
    n_rows = self.ui.tableWidget.rowCount()  # número de linhas na tabela
    for row_index in range(n_rows - 1, -1, -1):
        self.ui.tableWidget.removeRow(row_index)
