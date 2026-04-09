#!/bin/bash
# Script de instalación para WILLKA

set -e  # Salir en error

echo "🚀 Instalando WILLKA..."
echo "========================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Instale Python 3.11+ primero."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION detectado"

# Verificar uv
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env 2>/dev/null || true
fi

echo "✓ uv instalado"

# Crear entorno virtual
echo "🔧 Creando entorno virtual..."
uv venv .venv --python 3.11

# Activar entorno
source .venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
uv sync

# Instalar en modo desarrollo
echo "🔨 Instalando WILLKA en modo desarrollo..."
uv pip install -e .

# Crear directorios de datos
echo "📁 Creando estructura de directorios..."
mkdir -p data/input data/stems data/midi data/output/{musicxml,pdf,partes,png}

# Crear archivo de audio de prueba
echo "🎵 Creando audio de prueba..."
python3 -c "
import numpy as np
import soundfile as sf

sample_rate = 44100
duration = 2.0
t = np.linspace(0, duration, int(sample_rate * duration), False)
audio = 0.5 * np.sin(2 * np.pi * 440 * t)
sf.write('data/input/test_audio.wav', audio, sample_rate)
print('Audio de prueba creado: data/input/test_audio.wav')
"

# Verificar instalación
echo "🔍 Verificando instalación..."
if willka check; then
    echo ""
    echo "✅ ¡WILLKA instalado exitosamente!"
    echo ""
    echo "📋 Comandos disponibles:"
    echo "   willka run <audio.mp3>     # Pipeline completo"
    echo "   willka stems <audio.mp3>   # Solo separación de stems"
    echo "   willka check               # Verificar sistema"
    echo ""
    echo "🎵 Para probar:"
    echo "   willka run data/input/test_audio.wav --device cpu"
    echo ""
    echo "⚠️  Notas importantes:"
    echo "   1. Para uso real, instale ffmpeg: sudo apt install ffmpeg"
    echo "   2. Para exportación real, instale MuseScore 4"
    echo "   3. Use --device cuda si tiene GPU NVIDIA"
else
    echo "❌ Hubo un problema con la instalación"
    exit 1
fi