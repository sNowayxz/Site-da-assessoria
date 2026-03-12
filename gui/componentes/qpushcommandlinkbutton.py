STYLE="""

/***   QCommandLinkButton   ***/
/* Atenção o nome no arquivo foi alterado para que o componente QCommandLinkButton, */
/* seja carregado após o componente QPushButton, pois aquele elemento herda estilos deste */
/* elemento, ao carregar depois ele acaba dando o "reset" dos estilos e mesmo assim alguns estilos */
/* de hover e pressed não conseguem ser interpretados como no navegador */
/* Caso queira definir o elemento sem a seta deve ser no próprio app definir:  "button.setIcon(QIcon())", */
/* onde button é o elemento QCommandLinkButton */ 

QCommandLinkButton {
    
    background-color: transparent;
    border-radius: 5px;
    text-align: center;

    max-width: 500px;
    
    /* font */
    font-family: Montserrat;
    color: #000000;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-decoration: none;
    qproperty-iconSize: 0px;
}

QCommandLinkButton::hover {
    color: #ff0000; /* sem efeito */
    background-color: rgba(23, 98, 158,0.2);
    font-weight: 700 !important; /* sem efeito */
    font-size: 18px; /* sem efeito */
}

QCommandLinkButton:pressed {
    background-color: rgba(23, 98, 158,0.5);
    color: white !important; /* sem efeito */
}
"""
