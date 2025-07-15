# 🍷 WineProton Manager ![Python](https://img.shields.io/badge/python-3.8+-blue.svg) ![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg) ![License](https://img.shields.io/badge/license-GPLv3-orange.svg)

---

|  **Description**  |  **Descripción** |
|----------------------|-----------------------|
| **WineProton Manager** is a Python tool that lets you **easily manage, organize, and switch Proton and Wine versions** for your Steam games and Linux applications, including Steam Deck.<br><br> **🔧 Main features**<br>- Manage multiple prefixes (Wine and Proton).<br>- Automated component installation via **Winetricks**.<br>- Support for custom programs (.exe / .msi).<br>- Detailed environment visualization.<br>- Intuitive UI with light and dark themes.<br>- Linux support (Steam Deck included). | **WineProton Manager** es una herramienta desarrollada en Python que te permite **gestionar, organizar y cambiar fácilmente las versiones de Proton y Wine** para tus juegos de Steam y aplicaciones en Linux, incluyendo Steam Deck.<br><br> **🔧 Características principales**<br>- Gestión de múltiples *prefixes* (Wine y Proton).<br>- Instalación automatizada de componentes mediante **Winetricks**.<br>- Soporte para programas personalizados (.exe / .msi).<br>- Visualización detallada de los entornos configurados.<br>- Interfaz intuitiva con temas claro y oscuro.<br>- Compatible con Linux (incluye Steam Deck). |

---

## 🖥️ Screenshots / Capturas
![Screenshot 1](docs/screenshot-01.png) | ![Screenshot 2](docs/screenshot-02.png)
--- | ---
![Screenshot 3](docs/screenshot-03.png) | ![Screenshot 4](docs/screenshot-04.png)
---

## 🚀 Instalación / Installation

```bash
# Requisitos previos / Prerequisites (Linux)
sudo apt install wine winetricks konsole kdialog libssl3

# Clonar repositorio / Clone repo
git clone https://github.com/EstebanKZL/WineProtonManager.git
cd WineProtonManager

# Instalar dependencias / Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ejecutar / Run
python3 main.py
