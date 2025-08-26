#!/bin/bash
echo "Iniciando o bot com webhook..."
gunicorn main:app --bind 0.0.0.0:$PORT --timeout 0
