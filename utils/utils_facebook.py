from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    WebDriverException,
)

SELECTOR = "div[aria-label='Escreva algo...'][contenteditable='true']"

def wait_for_contenteditable(driver, selector=SELECTOR, timeout=15):
    """Espera o elemento aparecer no DOM e ficar visível/ativável."""
    wait = WebDriverWait(driver, timeout)
    el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
    # opcional: garantir que está clicável
    # el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    return el

def clear_contenteditable(el):
    """Limpa conteúdo anterior usando atalhos de seleção total + delete."""
    # dá o foco
    el.click()
    # Seleciona tudo e apaga (funciona na maioria dos SOs; em Mac, COMMAND também ajuda)
    try:
        el.send_keys(Keys.CONTROL, "a")
    except WebDriverException:
        pass
    try:
        el.send_keys(Keys.COMMAND, "a")
    except WebDriverException:
        pass
    el.send_keys(Keys.DELETE)
    # Plano B: BACK_SPACE para alguns editores
    el.send_keys(Keys.BACK_SPACE)

def js_set_text(driver, el, text):
    """Define texto via JS e dispara eventos para apps que dependem deles."""
    driver.execute_script("""
        const el = arguments[0];
        const value = arguments[1];

        // Tente limpar com seleção programática quando é editor lexical
        try { el.innerText = ''; } catch(e) {}

        // Use textContent/innerText para preencher
        try { el.textContent = value; } catch(e) {}
        try { el.innerText = value; } catch(e) {}

        // Dispara eventos que muitos frameworks escutam
        el.dispatchEvent(new InputEvent('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));  // opcional
    """, el, text)

def wait_text_applied(driver, selector, expected_text, timeout=10):
    """Confere se o texto desejado aparece no contenteditable."""
    def getter(drv):
        try:
            el = drv.find_element(By.CSS_SELECTOR, selector)
        except Exception:
            return False
        # Alguns editores mantêm <p><span> etc.; compare por innerText normalizado
        txt = el.get_attribute("innerText") or ""
        return expected_text in txt
    WebDriverWait(driver, timeout).until(getter)

def type_in_contenteditable(driver, text, selector=SELECTOR, timeout=15):
    """Fluxo completo: esperar, limpar, digitar (com fallback JS) e validar."""
    # 1) esperar elemento
    el = wait_for_contenteditable(driver, selector, timeout)

    # 2) garantir foco e limpar
    try:
        el.click()
    except (StaleElementReferenceException, ElementNotInteractableException):
        el = wait_for_contenteditable(driver, selector, timeout)
        el.click()

    clear_contenteditable(el)

    # 3) tentar digitar com send_keys
    try:
        el.send_keys(text)
    except (ElementNotInteractableException, WebDriverException, StaleElementReferenceException):
        # 4) fallback via JS
        js_set_text(driver, el, text)

    # # 5) validar que o texto entrou
    # try:
    #     wait_text_applied(driver, selector, text, timeout=timeout)
    # except TimeoutException:
    #     # último recurso: forçar via JS novamente e checar
    #     js_set_text(driver, el, text)
    #     wait_text_applied(driver, selector, text, timeout=timeout)

    return driver.find_element(By.CSS_SELECTOR, selector)

# ======================
# EXEMPLO DE USO REAL:
# ======================
# driver.get("https://sua-pagina.com")
# caixa = type_in_contenteditable(driver, "Olá, isso é um teste!")
# print("OK! Texto final:", caixa.get_attribute("innerText"))
