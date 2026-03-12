import re
from bs4 import BeautifulSoup

def escape_html(texto:str):
    texto = str(texto).replace("\r\n\r\n"," ").replace("\r\n"," ").replace("\r","").replace("\n"," ").replace("\\xa0"," ").replace("\\xa1"," ").replace("\\u200b"," ").replace("\xa0"," ").replace("\u200b"," ").replace("\xa1"," ")
    texto = normalizar_espacos(texto=texto)
    texto = remover_style_img(texto)
    return str(texto)

def normalizar_espacos(texto):
    # Remove múltiplos espaços, tabs e quebras de linha
    return re.sub(r'\s+', ' ', texto).strip()

def remover_style(html):
    # Remove style="alguma coisa"
    return re.sub(r'\s*style="[^"]*"', '', html)

def remover_style_img(html):
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all('img'):
        if 'style' in img.attrs:
            del img.attrs['style']
    return str(soup)