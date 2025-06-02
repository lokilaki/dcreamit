import requests

def verificar_acesso(url="https://monero.hashvault.pro/en/"):
    try:
        resposta = requests.get(url, timeout=5)
        return resposta.status_code
    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar o site: {e}"

# Teste
print(verificar_acesso())
