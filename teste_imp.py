# from weasyprint import HTML
# print("começou")
# HTML('modelo.html').write_pdf('saida.pdf')
# print("final")





from xhtml2pdf import pisa

with open('modelo.html', encoding='utf-8') as f:
    html = f.read()

with open('saida2.pdf', 'wb') as f:
    pisa.CreatePDF(html, dest=f)

print("final2")