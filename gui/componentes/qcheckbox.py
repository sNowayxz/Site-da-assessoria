STYLE="""

/*** QCheckBox ***/


QCheckBox  {
    font-family: Montserrat, sans-serif;
    font-size: 11px;
}

QCheckBox::indicator {
    border-radius: 14px;
    width: 15px;
    height: 15px;
    border: 1px solid rgb(133,133,133);
    border-radius: 4px;
}

QCheckBox::indicator:hover {
    /* Cor de fundo ao passar o mouse */
    background-color: rgba(23, 98, 158, 0.2); 
}
    
QCheckBox::indicator:checked {
    width:  15px;
    height: 15px;
    image: url(gui/img/checked.png);
    background-color: #17629e; 
}
"""
