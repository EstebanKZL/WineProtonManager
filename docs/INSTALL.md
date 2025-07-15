# WineProton Manager Installation Guide

This guide provides instructions on how to run WineProton Manager from the source code or build your own AppImage from scratch.

## Run the Application

1. Prerequisites
   ```bash
   # 🔧 Instalando dependencias del sistema
   sudo apt update
   sudo apt install python3-venv git wine winetricks konsole kdialog libssl3

2. Clone the Repository:
   ```bash
   # 📦 Descargar Repositor
   sudo apt install wine winetricks konsole kdialog libssl3
   git clone https://github.com/EstebanKZL/WineProtonManager.git
   cd WineProtonManager

3. Set Up a Virtual Environment and Install Dependencies:
   ```bash
   # Create the virtual environment
   python3 -m venv .venv
   
   # Activate the environment
   source .venv/bin/activate
   
   # Upgrade pip and install packages from requirements.txt
   pip install --upgrade pip
   pip install -r requirements.txt

3. Run the Application:

   ```bash
   # 🏃 Ejecutar
   python3 main.py

---

## Building the AppImage (for Developers)

1. Prerequisites
   ```bash
   # 🔧 Instalando dependencias del sistema
   sudo apt update
   sudo apt install python3-venv git wine winetricks konsole kdialog libssl3 imagemagick

2. Clone the Repository:

   ```bash
   # 📦 Descargar Repositor
   git clone https://github.com/EstebanKZL/WineProtonManager.git
   cd WineProtonManager
   
3. Download AppImage Build Tools:

   ```bash
   # ⬇️ Descargando herramientas de construcción
   wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
   chmod +x linuxdeploy-x86_64.AppImage
   
   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
   chmod +x appimagetool-x86_64.AppImage

3. Set Up a Virtual Environment and Install Dependencies:
   ```bash
   # Create the virtual environment
   python3 -m venv .venv
   
   # Activate the environment
   source .venv/bin/activate
   
   # Upgrade pip and install packages from requirements.txt
   pip install --upgrade pip
   pip install -r requirements.txt

   # 🔨 Compilando con PyInstaller
   pyinstaller --onefile --noconfirm --clean \
    --add-data "/usr/lib/x86_64-linux-gnu/libssl.so.3:." \
    --add-data "/usr/lib/x86_64-linux-gnu/libcrypto.so.3:." \
    --add-data "/usr/lib/x86_64-linux-gnu/libcurl.so.4:." \
    --add-data "/usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0:." \
    --add-data "/usr/lib/x86_64-linux-gnu/qt5/plugins/:plugins" \
    --add-data "/usr/lib/x86_64-linux-gnu/qt5/qml/:qml" \
    --exclude-module PyQt5.Qt3D \
    --exclude-module PyQt5.Qt3DAnimation \
    --exclude-module PyQt5.QtBodymovin \
    main.py
   
2. Crear AppRun & Desktop & Icon
   ```bash
   # 📁 Preparando AppDir
   mkdir -p AppDir/

   #🏃 Creando AppRun
   cat << 'EOF' > ./AppDir/AppRun
   #!/bin/sh
   HERE="$(dirname "$(readlink -f "$0")")"
   export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
   export QT_PLUGIN_PATH="${HERE}/usr/lib/plugins"
   export QML2_IMPORT_PATH="${HERE}/usr/lib/qml"
   export QT_QPA_PLATFORM=xcb
   export GDK_BACKEND=x11
   exec "${HERE}/usr/bin/main" "$@"
   EOF
   chmod +x ./AppDir/AppRun

   # 🖥️ Creando archivo .desktop
   cat << EOF > ./AppDir/WineProtonManager.desktop
   #!/bin/sh
   [Desktop Entry]
   Name=WineProtonManager
   Exec=main
   Icon=WineProtonManager
   Type=Application
   Categories=Utility;
   Comment=Herramienta de gestión para Wine/Proton
   EOF

   # 🖼️ Procesando icono
   mkdir -p AppDir/usr/share/icons/hicolor/512x512/apps
   cp icons/WineProtonManager.png AppDir/usr/share/icons/hicolor/512x512/apps/WineProtonManager.png
   
3. Construye la AppImage:

   ```bash

   # 🏗️ Construyendo AppImage
   ./linuxdeploy-x86_64.AppImage \
    --appdir AppDir \
    -e "AppDir/usr/bin/main" \
    -i "AppDir/usr/share/icons/hicolor/512x512/apps/WineProtonManager.png" \
    -d "AppDir/WineProtonManager.desktop" \
    --output appimage

   mkdir -p /AppDir/usr/share/icons/hicolor/512x512/apps
   cp /icons/WineProtonManager.png /AppDir/usr/share/icons/hicolor/512x512/apps/WineProtonManager.png
   convert -size 512x512 xc:white -fill black -draw "circle 256,256 256,50" /AppDir/usr/share/icons/hicolor/512x512/apps/WineProtonManager.png
   
   ./linuxdeploy-x86_64.AppImage --appdir AppDir -e dist/main -i icons/WineProtonManager.png -d AppDir/WineProtonManager.desktop
   ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir

4. Ejecutar programa
   
   ```bash
   ./WineProtonManager-v1.1.0-x86_64.AppImage
