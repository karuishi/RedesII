# Sistema de Streaming RTSP/RTP com Áudio e Vídeo

Este repositório contém a implementação de um sistema de streaming de mídia em tempo real usando arquitetura Cliente-Servidor. O sistema suporta:

- Transmissão de vídeo e áudio simultâneos
- Controle de sessão RTSP (SETUP, PLAY, PAUSE, TEARDOWN)
- Criptografia de payloads via Fernet
- Múltiplos clientes simultâneos

## Conceitos

### RTSP

RTSP (Real-Time Streaming Protocol) opera sobre TCP (porta `8554`) e funciona como um controle remoto da transmissão. Ele gerencia o estado da sessão para cada cliente individualmente.

### RTP

RTP (Real-time Transport Protocol) opera sobre UDP e entrega os dados de mídia. O servidor encapsula os quadros de vídeo e as amostras de áudio em pacotes RTP com cabeçalhos que contêm:

- tipo de payload
- número de sequência
- timestamps

Isso garante ordem e sincronização corretas durante a reprodução.

## Fluxo de Funcionamento

1. O servidor aguarda conexões RTSP.
2. O cliente conecta-se e envia `SETUP`, informando as portas UDP para áudio e vídeo.
3. O servidor cria uma sessão isolada para o cliente e inicia as threads de extração de mídia.
4. Ao receber `PLAY`, o servidor lê os dados de mídia, criptografa o payload e envia os pacotes RTP via UDP.
5. O cliente recebe os pacotes, descarta o cabeçalho RTP, descriptografa o conteúdo e reproduz o vídeo com OpenCV e o áudio com PyAudio.
6. `TEARDOWN` encerra a sessão e libera os sockets usados.

## Pré-requisitos

Recomendado em Linux (Ubuntu/Debian), pois o projeto depende de bibliotecas de áudio e de interface gráfica do sistema operacional.

## Como usar

### 1. Configurar o ambiente

O projeto inclui um script `setup.sh` que instala dependências do sistema, cria um ambiente virtual e instala os pacotes Python necessários.

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Preparar o vídeo

Coloque um arquivo MP4 na pasta raiz do projeto. O servidor espera um arquivo com o nome `hobi67.mp4`.

### 3. Ativar o ambiente virtual

```bash
source venv/bin/activate
```

### 4. Iniciar o servidor

```bash
python server.py
```

O servidor ficará aguardando conexões RTSP.

### 5. Iniciar os clientes

Em outro terminal, ative o ambiente virtual e execute o cliente com portas UDP diferentes para vídeo e áudio.

```bash
source venv/bin/activate
python client.py 5000 5002
```

Para um segundo cliente:

```bash
source venv/bin/activate
python client.py 6000 6002
```

### 6. Usar a interface do cliente

Na interface gráfica do cliente:

1. Clique em `SETUP` para iniciar a sessão e alocar portas.
2. Clique em `PLAY` para iniciar o fluxo RTP.
3. Clique em `PAUSE` para suspender a transmissão.
4. Clique em `TEARDOWN` para encerrar a sessão e liberar portas.

## Estrutura de arquivos

- `server.py`: lógica do servidor, controle RTSP, extração de mídia e envio RTP.
- `client.py`: interface gráfica em Tkinter, controle de sessão, decodificação e reprodução.
- `utils.py`: definições comuns, encapsulamento RTP e geração de chaves de criptografia.
- `setup.sh`: script de instalação de dependências e configuração do ambiente.
- `.gitignore`: arquivos e pastas que não devem ser versionados.

## Observações

- Garanta que as portas UDP usadas pelos clientes não estejam em uso.
- O arquivo de vídeo deve estar no mesmo diretório do projeto e nomeado corretamente.
- Ative o ambiente virtual antes de rodar o servidor e o cliente.
