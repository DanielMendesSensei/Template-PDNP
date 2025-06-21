#!/bin/bash
set -e

echo "🌸 Iniciando Celery Worker - Desenvolvimento"

# Função para esperar serviços
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    
    echo "⏳ Aguardando $service..."
    while ! nc -z $host $port; do
        sleep 0.1
    done
    echo "✅ $service está pronto!"
}

# Aguardar serviços dependentes
wait_for_service postgres 5432 "PostgreSQL"
wait_for_service redis 6379 "Redis"
wait_for_service backend 8000 "Backend"

echo "🔧 Configurando ambiente Celery..."
export DJANGO_SETTINGS_MODULE=config.settings.development

# Aguardar um pouco mais para backend estar pronto
sleep 10

echo "🎉 Celery Worker configurado!"
echo "🚀 Executando comando: $@"
exec "$@"
