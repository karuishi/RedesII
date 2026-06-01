#!/bin/bash

echo "Verificando/Instalando dependências do sistema operacional..."
# O sudo pedirá sua senha no terminal
sudo apt update
sudo apt install -y python3-venv portaudio19-dev python3-dev python3-tk

echo "----------------------------------------"

# Verifica se a pasta venv já existe, se não, cria
if [ ! -d "venv" ]; then
    echo "Criando o ambiente virtual (venv)..."
    python3 -m venv venv
else
    echo "Ambiente virtual já existe. Pulando criação."
fi

echo "----------------------------------------"
echo "Instalando pacotes do Python..."

# O comando source ativa o venv dentro deste script temporariamente para o pip funcionar
source venv/bin/activate

# Atualiza o pip e instala as bibliotecas que usamos
pip install --upgrade pip
pip install opencv-python numpy pyaudio cryptography moviepy

echo "----------------------------------------"
echo "Dependências instaladas com sucesso!"
echo "Para ativar o ambiente virtual neste terminal, execute o comando abaixo:"
echo ""
echo "source venv/bin/activate"
echo ""