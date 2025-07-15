# 🍷 WineProton Manager

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/license-GPLv3-orange.svg)

## Descripción

**WineProtonManager es una herramienta en Python que te permite gestionar, organizar y cambiar fácilmente las versiones de Proton y Wine para tus juegos en Steam y aplicaciones en Linux (incluyendo Steam Deck).**

🔧 **Características principales**:  
- Gestión de múltiples prefixes (Wine y Proton)
- Instalación automatizada de componentes via Winetricks
- Soporte para programas personalizados (.exe/.msi)
- Visualización detallada de entornos
- Interfaz intuitiva con temas claro/oscuro
- Compatible con Linux (incluye Steam Deck)

---

## Description

**WineProtonManager is a Python tool that allows you to easily manage, organize, and switch Proton and Wine versions for your Steam games and Linux applications (including Steam Deck).**

🔧 **Main features**:  
- Manage multiple prefixes (Wine and Proton)
- Automated component installation via Winetricks
- Support for custom programs (.exe/.msi)
- Detailed environment visualization
- Intuitive UI with light/dark themes
- Linux platform support (Steam Deck included)

---

## 🖥️ Screenshots / Capturas

<table style="width: 100%; border-collapse: collapse;">
  <tr>
    <td style="width: 50%; padding: 5px;">
      <img src="docs/screenshot-01.png" style="width: 100%; height: auto; object-fit: contain; border: 1px solid #ddd;">
    </td>
    <td style="width: 50%; padding: 5px;">
      <img src="docs/screenshot-02.png" style="width: 100%; height: auto; object-fit: contain; border: 1px solid #ddd;">
    </td>
  </tr>
  <tr>
    <td style="width: 50%; padding: 5px;">
      <img src="docs/screenshot-03.png" style="width: 100%; height: auto; object-fit: contain; border: 1px solid #ddd;">
    </td>
    <td style="width: 50%; padding: 5px;">
      <img src="docs/screenshot-04.png" style="width: 100%; height: auto; object-fit: contain; border: 1px solid #ddd;">
    </td>
  </tr>
</table>

---

## 🚀 Instalación / Installation

```bash
# Requisitos previos / Prerequisites (Linux)
sudo apt install wine winetricks konsole kdialog libssl3

# Clonar repositorio / Clone repo
git clone https://github.com/EstebanKZL/WineProtonManager.git
cd WineProtonManager

# Instalar dependencias / Install dependencies
pip install -r requirements.txt

# Ejecutar / Run
python3 main.py

cd WineProtonManager

