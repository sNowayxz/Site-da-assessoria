import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
# from PyQt6.QtWidgets import *
# from PyQt6.QtWidgets import 

# app = QApplication([])
class File_Dialog(QMessageBox):

    def __init__(self):
        super().__init__()
    
    def pathFile(self , dir):

            # Abre pop de buscador de arquivo
            filename, _ = QFileDialog.getOpenFileName(
                None, 
                'Selecionar arquivo de texto', 
                dir, 
                'Arquivos de texto (*.txt)'
            )
            if filename:
                return filename
            else:
                 return None