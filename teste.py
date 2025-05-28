import subprocess

# Comando para ativar o Wi-Fi usando netsh
comando = ['netsh', 'interface', 'set', 'interface', 'name="Wi-Fi 4"', 'admin=enable']

try:
    # Executa o comando
    resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
    print("Wi-Fi ativado com sucesso!")
except subprocess.CalledProcessError as e:
    print(f"Erro ao ativar o Wi-Fi: {e.stderr}")