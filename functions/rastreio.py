from system.system import t
from system.chrome import atualizar_soup


def esperar_carregamento_enunciado(driver , enunciado):           
    # Corrige certos problemas de demora de carregamento de enunciado
    delta_t = 0.1
    T = 6
    # Se deixar apenas T, ele pode entrar em loopíng infinito
    # pois pode nunca chegar a zero!
    if enunciado:
        while T>0 and not enunciado.text:
            soup = atualizar_soup(driver)
            enunciado =  soup.find('div',{"class":"enunciado ng-binding"})
            t(delta_t)
            T -= delta_t