
import os

import pythoncom
import win32com.client


def Agendador_de_Tarefas():
    import datetime

    # Diretório Base
    dir_base = 'C:\\Papiron_Agendador'

    # Nome da Tarefa
    task_name = "Papiron"

    # Cria uma instancia do Agendador de Tarefas
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    root_folder = scheduler.GetFolder('\\')
    task_def = scheduler.NewTask(0)

    # Verifica se há um agendador 
    if Verifica_Agendador(task_name):
        Apaga_Tarefa(task_name)

    # Create trigger
    start_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
    TASK_TRIGGER_TIME = 2
    trigger = task_def.Triggers.Create(TASK_TRIGGER_TIME)
    trigger.StartBoundary = start_time.isoformat()
    trigger.Id = 'Trigger1'
    # trigger.StartBoundary = '2023-03-10T10:20:00'  # data e hora de inicio
    trigger.EndBoundary = '2030-03-14T10:00:00'  # data e hora de f
    trigger.Repetition.Interval = 'PT1H'  # intervalo de tempo em horas
    trigger.Repetition.Duration = 'PT23H'  # intervalo de tempo em horas
    # trigger.StopIfGoingOnBatteries = True
    trigger.Repetition.StopAtDurationEnd = True


    # Define a ação a ser executada pela tarefa
    TASK_ACTION_EXEC = 0
    action = task_def.Actions.Create(TASK_ACTION_EXEC)
    action.ID = 'Realize as verificações'
    action.Path = os.getcwd()+'\\agendador_papiron.py'


    # Set parameters
    task_def.Settings.Hidden = False
    task_def.Settings.RunOnlyIfIdle = False
    task_def.Settings.ExecutionTimeLimit = 'PT1H'
    task_def.RegistrationInfo.Description = task_name
    task_def.Settings.Enabled = True
    task_def.Settings.StopIfGoingOnBatteries = False
    task_def.Settings.AllowDemandStart = True
    task_def.Settings.WakeToRun = True
    task_def.Settings.StartWhenAvailable = True

    # Register task
    # If task already exists, it will be updated
    TASK_CREATE_OR_UPDATE = 6
    TASK_LOGON_NONE = 0
    root_folder.RegisterTaskDefinition(
        task_name,  # Task name
        task_def,
        TASK_CREATE_OR_UPDATE,
        '',  # No user
        '',  # No password
        TASK_LOGON_NONE)
    print("Tarefa incluída com sucesso no Agendador de Tarefas do Windows")

def Verifica_Agendador(task_name:str)->bool:
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    root_folder = scheduler.GetFolder('\\')
    
    for task in root_folder.GetTasks(0):
        if task.Name == task_name:
            return True
    return False

def Apaga_Tarefa(task_name:str)->str:
    # Cria instância de Agendamento
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    root_folder = scheduler.GetFolder('\\')

    for task in root_folder.GetTasks(0):
        if task.Name == task_name:
            # Obtém a tarefa e a exclui
            root_folder.DeleteTask(task_name, 0)
            print('A tarefa foi excluída com sucesso.')
            break

def Data_Inicio_Tarefa(task_name:str):
    from datetime import datetime
    task_service = win32com.client.Dispatch('Schedule.Service')
    task_service.Connect()
    try:
        root_folder = task_service.GetFolder('\\')
        task = root_folder.GetTask(task_name)

        for task in root_folder.GetTasks(0):
            if task.Name == task_name:
                triggers = task.Definition.Triggers
                for trigger in triggers:
                    if trigger.Type == 2:  # 0 indica um disparador de tempo (time trigger)
                        start_time = trigger.StartBoundary
                        start_time_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
                        print(f'Início agendado: {start_time_dt}')
                        return start_time_dt
        
    except pythoncom.com_error as e:
        print("\nNão foi possível acessar a Tarefa solicitada:",task_name,"\n\nCode Error:", e.hresult)
        return None
        