# camApp

Aplicación de escritorio en Python para previsualizar una webcam física y reenviarla a una cámara virtual.

## Stack

- Python 3.12
- PySide6
- OpenCV
- pyvirtualcam
- PyInstaller

## Archivos principales

- `logitech_webcam_app.py`: app principal
- `pyproject.toml`: metadatos y dependencias modernas del proyecto
- `requirements.txt`: dependencias runtime
- `requirements-dev.txt`: dependencias de desarrollo y build
- `Makefile`: atajos para instalar, ejecutar, validar y empaquetar
- `webcam_app.spec`: configuración de PyInstaller

## Funcionalidad actual

- Vista previa en vivo de la cámara física
- Selección de cámara detectada
- Selección de resolución
- Ajuste de FPS
- Inicio y detención de cámara virtual
- Empaquetado con PyInstaller mediante `webcam_app.spec`

## Requisitos

- Linux de escritorio
- Python 3.12
- Una webcam accesible por OpenCV
- Soporte de cámara virtual en el sistema

Nota:
En Linux, `pyvirtualcam` puede requerir un backend del sistema como `v4l2loopback`.

## Instalación local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

O con `make`:

```bash
make install
```

## Ejecutar

```bash
source .venv/bin/activate
python logitech_webcam_app.py
```

O con `make`:

```bash
make run
```

## Validación rápida

```bash
make check
```

## Empaquetar binario

```bash
source .venv/bin/activate
pyinstaller --noconfirm webcam_app.spec
```

O con `make`:

```bash
make build
```

El binario generado queda en `dist/webcam_app`.

## Estado

Proyecto funcional como MVP.

Pendientes razonables para siguientes iteraciones:

- Mejor detección y etiquetado de cámaras
- Persistencia de configuración
- Manejo más fino de errores de backend
- Controles de imagen
