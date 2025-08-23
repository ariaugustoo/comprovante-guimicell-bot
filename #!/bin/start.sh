#!/bin/bash
echo "Instalando Tesseract..."
apt-get update && apt-get install -y tesseract-ocr

echo "Iniciando o bot..."
python3 main.py
