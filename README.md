# 🛡️ negação_de_servico – Ferramenta Educacional de Teste de Estresse

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)

> **⚠️ AVISO ÉTICO E LEGAL**  
> Esta ferramenta foi desenvolvida **exclusivamente para fins educacionais** no ambiente do **NetLab Educacional** ou em laboratórios próprios com autorização explícita.  
> **O uso não autorizado contra sistemas de terceiros é crime.** Consulte as leis do seu país (no Brasil, Lei 12.737/2012 e art. 266 do Código Penal).  
> Ao utilizar este software, você assume total responsabilidade por suas ações.

---

## 📚 Sobre o Projeto

O repositório **negação_de_servico** contém uma ferramenta de linha de comando escrita em Python puro (`ferramentaddos.py`) para demonstrar, na prática, o funcionamento de ataques de negação de serviço (DoS/DDoS) em **ambientes controlados e isolados**, como o **NetLab Educacional**.

O **NetLab Educacional** é um laboratório virtual de redes e segurança, onde alunos podem experimentar cenários reais sem riscos à infraestrutura externa. Esta ferramenta é parte do material didático do NetLab, permitindo que os estudantes:

- Compreendam os mecanismos de flooding (TCP, UDP, HTTP, HTTPS).
- Observem o impacto da concorrência (múltiplas threads) no consumo de recursos do servidor.
- Pratiquem análise de logs e identificação de tráfego malicioso.
- Testem técnicas de mitigação como rate limiting e firewalls.

---

## 🎯 Público-alvo

- Alunos de cursos técnicos e superiores em Redes de Computadores, Segurança da Informação e áreas afins.
- Instrutores que desejam demonstrações práticas em sala de aula.
- Pesquisadores em segurança cibernética em ambiente controlado.

---

## ⚙️ Requisitos

- **Python 3.6 ou superior** (nenhuma biblioteca externa necessária)
- Sistemas operacionais: Windows, Linux, macOS ou **Termux (Android)**
- Acesso ao **NetLab Educacional** ou a um servidor próprio em laboratório isolado

---

## 📦 Instalação

1. Clone este repositório ou baixe o arquivo `ferramenta.py`:

   ```bash
   git clone https://github.com/Yurigonpav/negacao_de_servico.git
   cd negacao_de_servico
