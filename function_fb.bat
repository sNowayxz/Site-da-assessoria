@echo off

REM Mudar para o diretório onde o arquivo .bat está localizado
cd /d %~dp0

REM Ativar o ambiente virtual
call "venv_papiron\Scripts\activate.bat"

REM Executar o script Python
python "function_facebook.py"