class SenhaError(Exception):
    """
    Erro de senha
    """

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "A senha expirou"
    
class StatusAlunoError(Exception):
    """
    Aluno trancou matricula
    """

    def __init__(self) -> None:
        self.msg = "Erro de matricula"

    def __str__(self) -> str:
        return "Aluno trancou matricula"
    
class StatusScrappedError(Exception):
    """
    Já realizou o Scrapped para o Aluno ou para o curso
    """

    def __init__(self) -> None:
        self.msg = "Erro"

    def __str__(self) -> str:
        return "Já realizou o Scrapped para o Aluno"
    
class DisciplinaScrappedError(Exception):
    """
    Não existem disciplinas a serem rastreadas
    """

    def __init__(self) -> None:
        self.msg = "Erro"

    def __str__(self) -> str:
        return "Não existem disciplinas a serem rastreadas"
    
class AlunoNotScrappedError(Exception):
    """
    Sem dados do scrapped do Aluno
    """

    def __init__(self) -> None:
        self.msg = "Erro"

    def __str__(self) -> str:
        return "Sem dados do scrapped do Aluno"
    

class ModuloError(Exception):
    """
    Módulo selecionado está fechado
    """

    def __init__(self) -> None:
        self.msg = "Erro"

    def __str__(self) -> str:
        return "Módulo selecionado está fechado"
    

class FileLoginError(Exception):
    """
    Arquivo de logins está vazio
    """

    def __init__(self) -> None:
        self.msg = "Erro"

    def __str__(self) -> str:
        return "O Arquivo de logins está vazio"
    
class CPFError(Exception):
    """
    Login com CPF
    """

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Login com CPF"


class MaterialError(Exception):
    """
    Não há material novo a ser baixado
    """

    def __init__(self) -> None:
        self.msg = "Erro"

    def __str__(self) -> str:
        return "Não há novo material a ser baixado."
    
class DisciplinaError(Exception):
    """
    Erro em acessar a disciplina, por algum motivo logou
    e não conseguiu acessar as disciplinas
    """

    def __init__(self) -> None:
        self.msg = "Erro nas Disciplinas"

    def __str__(self) -> str:
        return "Não foi possível acessar as disciplinas"

class ScrappedError(Exception):
    """
    Erro relacionado à algum Scrapped incorreto
    """

    def __init__(self) -> None:
        self.msg = "Erro ao realizar o SCRAPPED"

    def __str__(self) -> str:
        return "Não foi possível acessar rastrear"


class BrainlyError(Exception):
    """
    Erro relacionado à resposta do Brainly
    """

    def __init__(self) -> None:
        self.msg = "Erro ao realizar o SCRAPPED do Brainly"

    def __str__(self) -> str:
        return "Erro ao rastrear o Brainly"


class DisciplinaNotNew(Exception):
    """
    Não foram localizadas novas disciplinas para o módulo
    """
    
    def __init__(self) -> None:
        self.msg = "Não foram localizadas novas disciplinas para o módulo"

    def __str__(self) -> str:
        return "Não foram localizadas novas disciplinas para o módulo"
    


class RastreioError(Exception):
    """
    Houve erro no rastreio
    """

    def __init__(self) -> None:
        self.msg = "Erro no rastreio"

    def __str__(self) -> str:
        return "Houve um erro durante o rastreio"
    

class DisciplinaNotIniciadaError(Exception):
    """
    Houve erro no rastreio
    """

    def __init__(self) -> None:
        self.msg = "Erro no rastreio"

    def __str__(self) -> str:
        return "Houve um erro durante o rastreio"