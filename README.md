# 🍷 WineProton Manager  

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/license-GPLv3-orange.svg)

## **Herramienta GUI para gestionar entornos Wine/Proton e instalar componentes con interfaz gráfica Qt.**  

🔧 **Características principales**:  
- Gestión de múltiples prefixes (Wine y Proton)  
- Instalación automatizada de componentes via Winetricks  
- Soporte para programas personalizados (.exe/.msi)
- Visualización detallada de entornos  
- Interfaz intuitiva con temas claro/oscuro
- Plataforma (Linux)  

---
## Requisitos
- Python 3.8+
- PyQt5
- Wine/Proton instalado
- Winetricks

🖼️ **Captura**:  
![Screenshot](docs/screenshot.png)

---
🚀 Instalación  

    ```bash
    # Requisitos previos
    sudo apt install wine winetricks konsole kdialog libssl3  # Para Linux
    
    # Clonar repositorio
    git clone https://github.com/EstebanKZL/WineProtonManager.git
    cd WineProtonManager
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    # Ejecutar
    python3 src/WineProtonManager.py
    
    Consulta el archivo [INSTALL.md](docs/INSTALL.md) para instrucciones detalladas.

## Licencia
Este proyecto está licenciado bajo [GPL-3.0](LICENSE).
