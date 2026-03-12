STYLE="""

/***   QComboBox    ***/

QComboBox1 {
    min-width: 27px;
	min-height:23px;
    font-size:10px;
    font-family: Montserrat, sans-serif;
    color: #fff;
    background-color: #17629e; 
    border: 1px solid rgb(133,133,133);
    border-radius: 5px;

    /* Distância lateral do componente mais próximo */
    margin-left:0px;

    /* Espaçamento do elemento selecionado dentro do Box*/
    padding:0px 5px;
}

QComboBox  {
    min-width:18px;
    color: #000;
    border: 1px solid rgb(133,133,133);
    border-radius: 3px;

    /* Espaçamento do elemento selecionado dentro do Box*/
    padding:0px 5px;
}

QDateEdit  {
    min-height:22px;
    min-width: 90px;
    border: 1px solid rgb(133,133,133);
    border-radius: 3px;
    padding:0px 0px;
    margin:auto;
    padding:0px 0px 0px 5px;

}

QComboBox::drop-down {
    background-color: #17629e; 
    subcontrol-origin: padding;
    subcontrol-position: top right;

    /* Largura da área do botão de seta */
    width: 22px; 
    
    /* Borda entre o texto e o botão de seta */
    border-left-width: 1px; 
    border-left-color: darkgray; 
    border-left-style: solid; 
    border-top-right-radius: 3px; 
    border-bottom-right-radius: 3px;
}

QDateEdit::drop-down {
    background-color: #17629e; 
    subcontrol-origin: padding;
    subcontrol-position: top right;

    /* Largura da área do botão de seta */
    width: 22px; 
    
    /* Borda entre o texto e o botão de seta */
    border-left-width: 1px; 
    border-left-color: darkgray; 
    border-left-style: solid; 
    border-top-right-radius: 3px; 
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow {

    /* Caminho para o ícone da seta para baixo */
    image: url(gui/img/icon_arrow_down.png); 

}

 QDateEdit::drop-arrow {

    /* Caminho para o ícone da seta para baixo */
    image: url(gui/img/icon_arrow_down.png); 

}

QComboBox QAbstractItemView {
    
    /* Borda da lista suspensa */    
    border: 1px solid darkgray; 

    /* Cor da fonte do item selecionado */
    selection-color: #17629e;

    /* Cor de fundo dos itens da lista */
    background-color: lightgray;
}

QComboBox QAbstractItemView::item:hover {

    /* Borda da lista suspensa */    
    border: 1px solid darkgray; 

    /* Cor de fundo do item selecionado */
    selection-background-color: rgba(23, 98, 158, 0.2); 

    /* Cor da fonte do item selecionado */
    selection-color: rgba(23, 98, 158, 0.8);  

    /* Cor de fundo dos itens da lista */
    background-color: rgba(23, 98, 158, 0.2);
}

QComboBox QAbstractItemView::item {

    /* Itens da lista do menu suspenso */
    border-bottom: 1px solid darkgray; 
    padding:4px 12px;
}

QComboBox QAbstractItemView::item:selected, QDateEdit QAbstractItemView::item:selected {

    /* Cor de fundo do item selecionado na lista */
    background-color: rgba(23, 98, 158, 0.2);
    border: 0px
}


"""
