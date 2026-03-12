from agendador import (
    Agendador_de_Tarefas,
    Apaga_Tarefa,
    Data_Inicio_Tarefa,
    Verifica_Agendador,
)

# pyinstaller --windowed --noconfirm agendador_papiron.py 

try:
        import os
        import random
        import sys
        import time
        from datetime import datetime, timedelta

        import requests as rq
        from bs4 import BeautifulSoup

        from escape_uni import escape

        # Cria ou atualiza Tarefa no Agendador do Windows
        task_name = "Papiron"
        if not Verifica_Agendador(task_name):
                Agendador_de_Tarefas()
        else:
                data = Data_Inicio_Tarefa(task_name)
                if data - datetime.now() > timedelta(days=15):
                        Apaga_Tarefa(task_name)
                        Agendador_de_Tarefas()
                        print("Tarefa agendada foi atualizada!")
                else:
                        print("Tarefa agendada está atualizada!")


        #---------- PUBLICAÇÕES NORMAIS ----------------#

        #Faz e leitura das últimas postagens e extraí os ids
        url = "https://www.papiron.com.br/ferramentas/listar_links"
        req = rq.get(url)
        soup = BeautifulSoup(req.content, "html.parser")
        links=soup.find_all("a")

        # Verifica a quantidade de links descobertos
        lista_links = []
        faculdades = [
                        'unicesumar', 
                        'unopar'
                ]
        for link in links:
                id_url = link['href'][-22:]
                
                # Se tiver a faculdade no link ele guarda o link
                if any(faculdade in id_url for faculdade in faculdades):
                        lista_links.append(id_url)


        n = len(lista_links) 

        data_atual = datetime.now()
        data_em_texto = data_atual.strftime('%d/%m/%Y %H:%M')

        # Cria lista de todos id_urls Normais e Consolidados que ainda não foram encontrados
        lista_id_urls = []
        for j in range(len(links)):
                id_url = links[j]['href'][-22:]
                lista_id_urls.append(id_url)

        # i é quantidade de iterações que o app irá fazer no Google
        i=12

        headers = {  "set-cookie": "1P_JAR=2022-11-10-16;expires=Sat, 10-Dec-2022 16:44:49 GMT; path=/; domain=.google.com; Secure; SameSite=none",
                        }
        cont = 5
        while i and len(lista_id_urls) and cont:
                try:
                        id_url = lista_id_urls[random.randint(0,len(lista_id_urls)-1)]

                        for link in links:
                                erro=False
                                if id_url in link['href']:
                                        try:
                                                text = link.text
                                                query = text.split("XXXX ")[1]
                                                query = escape(query)
                                        except IndexError:
                                                erro=True
                                        except Exception as err:
                                                print("ERRO:",err)
                                                erro=True
                                        break

                        if id_url in lista_id_urls and not erro:
                                print("     Selecionou o id "+id_url+" para consulta\n")
                                url = "https://www.google.com/search?q="+query+"&aqs=chrome..69i57j69i60.415j0j7&sourceid=chrome&ie=UTF-8"
             
                                req = rq.get(url , headers=headers)
                                soup = BeautifulSoup(req.content, "html.parser")
                                l_links = soup.find_all('a')

                                # Obter o título
                                for link in links:
                                        if id_url in link['href']:
                                                # print("ll", link.text)
                                                title = link.text.replace("  ","").replace("\r"," ")[1:].split("\n").__getitem__(0) #+link.text.replace("  ","").replace("\r"," ")[1:].split("\n").__getitem__(1)
                                                break

                                posicao_google = "NL"
                                for j, posicao in enumerate(l_links):
                                        if "PAPIRON" in posicao.text.upper() or "MODELITOS" in posicao.text.upper():
                                                print("Posição: ", j-15, posicao.text)
                                                posicao_google = j-15
                                                url_google = "https://www.google.com"+l_links[j]['href']
                                                req = rq.get(url_google, headers=headers)
                                                print("R_google:",req)
                                                break

                                res = lambda posicao_google : "NÃO-LOCALIZADA" if posicao_google == "NL" else "RASTREADA"  

                                # VERIFICA A FACULDADE
                                if "unicesumar" in link:
                                        faculdade = "UNICESUMAR"
                                elif "unicesumar" in link:
                                        faculdade = "UNOPAR"
                                else:
                                        faculdade = "UNICESUMAR"
                                
                                url = "https://www.papiron.com.br/atividades/wkrTu78e/google?id_url="+id_url+"&posicao="+str(posicao_google)+"&faculdade="+faculdade
                                req = rq.get(url)
                                print(f'- {faculdade} {title} - {id_url} - {posicao_google} - {res(posicao_google)} \n')


                                # arquivo = open(path_file, 'a', encoding='utf-8')
                                # arquivo.writelines(u" - "+res(posicao_google)+" - "+str(posicao_google)+" - "+title[:150].replace("\n","  ")+" - https://www.papiron.com.br/lista_links/"+id_url+" \n") 
                                # arquivo.close()
                                time.sleep(10)
                                i-=1
                        # elif id_url in ids_localizados:
                        #         print("     Selecionou um id já indexado")

                        elif 'facebook' not in id_url:
                                print("     Selecionou um link do facebook")
                        
                        elif len(id_url)!=22:
                                print("     Selecionou um link do corpo da página")
                        
                        else:
                                print("     Verificar erro: ", id_url )
                                cont-=1
                        

                        # print("I e Cont", i , cont)
                except TimeoutError:
                        cont-=1
        # path_file = 'C:\\Users\\blitz\\Desktop\\Python\\Unicesumar\\papiron.txt'
        # arquivo = open(path_file, 'a')
        # arquivo.writelines(u"\n >> Links RASTREADOS:"+str(len(ids_localizados))+" >> "+str(100*len(ids_localizados)//(len(lista_links)//1))+"% \n")  
        # arquivo.close()
        sys.exit()

except Exception as err:
    import traceback
    msg = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    print(msg)
#     arquivo = open(path_file, 'a', encoding='utf-8')
#     arquivo.writelines(u" - "+msg+"\n") 
#     arquivo.close()
    time.sleep(180)
