STYLE = """

/*** QPushButton ***/

QPushButton {
    min-width: 100px;
	min-height:30px;
    max-width: 250px;
    max-height:30px;
    background-color: rgb(23, 98, 158);
    border-color: rgb(23, 98, 158);
    border-radius: 2px;

    /* font */
    font-family: 'Open Sans';
    color: #f1f5f7;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.1em;
}

QPushButton:hover {
    background-color: #003672;
	border-color:#003672;
}

QPushButton[amarelo='true'] {
    background-color: #ffc107;
    color: black;
}

QPushButton[amarelo='true']:hover {
    background-color: #ffca2c;
}

QPushButton[verde='true'] {
    background-color: #006723;
    color: white;
}

QPushButton[verde='true']:hover {
    background-color: #0a7f3c;
}
"""
