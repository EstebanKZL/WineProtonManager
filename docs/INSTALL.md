# WineProton Manager Installation Guide

This guide provides instructions on how to run WineProton Manager from the source code or build your own AppImage from scratch.

## Run the Application

1. Install Prerequisites:
   ```bash
   # 🔧 Install system dependencies
   sudo apt update
   sudo apt install python3-venv git wine winetricks konsole kdialog libssl3

2. Clone the Repository:
   ```bash
   # 📦 Clone repository
   sudo apt install wine winetricks konsole kdialog libssl3
   git clone https://github.com/EstebanKZL/WineProtonManager.git
   cd WineProtonManager

3. Set Up a Virtual Environment and Install Dependencies:
   ```bash
   # 🐍 Install packages from requirements.txt
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt

3. Run the Application:
   ```bash
   # 🏃 Run
   python3 main.py

---

## Building the AppImage (for Developers)

1. Install Prerequisites
   ```bash
   # 🔧 Install system dependencies
   sudo apt update
   sudo apt install python3-venv git wine winetricks konsole kdialog libssl3 imagemagick

2. Clone the Repository:
   ```bash
   # 📦 Clone repository
   git clone https://github.com/EstebanKZL/WineProtonManager.git
   cd WineProtonManager
   
3. Download AppImage Build Tools:
   ```bash
   # ⬇️ Download build tools
   wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
   chmod +x linuxdeploy-x86_64.AppImage appimagetool-x86_64.AppImage

4. Set Up a Virtual Environment and Install Dependencies:
   ```bash
   # 🐍 install packages from requirements.txt
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt

   # 🔨 Compile with PyInstaller
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
   
5. Create AppRun, Desktop File, and Icon:
   ```bash
   # 📁 Prepare AppDir
   mkdir -p AppDir/usr/bin
   cp dist/main AppDir/usr/bin/main

   #🔨 Create AppRun
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

   # 🖥️ Create .desktop file
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

   # 🖼️ Process icon
   mkdir -p AppDir/usr/share/icons/hicolor/512x512/apps
   cp icons/WineProtonManager.png AppDir/usr/share/icons/hicolor/512x512/apps/WineProtonManager.png
   
6. Build the AppImage:
   ```bash
   # 🏗️ Build AppImage
   ./linuxdeploy-x86_64.AppImage \
    --appdir AppDir \
    -e "AppDir/usr/bin/main" \
    -i "AppDir/usr/share/icons/hicolor/512x512/apps/WineProtonManager.png" \
    -d "AppDir/WineProtonManager.desktop" \
    --output appimage

   🔍 Finalize build
    ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir
   
7. Ejecutar programa
   ```bash
    # 🏃 Run AppImage
   ./WineProtonManager-x86_64.AppImage
