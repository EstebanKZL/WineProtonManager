#!/usr/bin/env bash

# Script unificado para construir WineProtonManager como AppImage
set -ex

APP_NAME="WineProtonManager"
APP_VERSION="1.4.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
ICONS_DIR="$SCRIPT_DIR/icons"
SRC_DIR="$SCRIPT_DIR/src"

echo "🔧 Instalando dependencias del sistema..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    wine winetricks git wget \
    python3 python3-pip python3-venv \
    libssl3 libgobject-2.0-0 libcurl4 \
    qtbase5-dev qtdeclarative5-dev qml-module-qtquick2 \
    libqt5quickcontrols2-5 libqt5svg5 libicu74 \
    libqt53dcore5 libqt53dquick5 libqt53dquickscene2d5 libqt53drender5 \
    imagemagick

sudo apt-get install -y --no-install-recommends \
    file konsole kdialog libssl3

echo "⬇️ Descargando herramientas de construcción..."
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
wget -nc https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget -nc https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage appimagetool-x86_64.AppImage

echo "🐍 Configurando entorno virtual Python..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando paquetes Python..."
pip install --upgrade pip
pip install pyinstaller==6.2.0 PyQt5==5.15.10 pyqt5-sip==12.13.0 setuptools==80.9.0

echo "🔨 Compilando con PyInstaller..."
pyinstaller --onefile --noconfirm --clean \
    --name "$APP_NAME" \
    --distpath "$BUILD_DIR/dist" \
    --workpath "$BUILD_DIR/build" \
    --specpath "$BUILD_DIR" \
    --add-data "/usr/lib/x86_64-linux-gnu/libssl.so.3:." \
    --add-data "/usr/lib/x86_64-linux-gnu/libcrypto.so.3:." \
    --add-data "/usr/lib/x86_64-linux-gnu/libcurl.so.4:." \
    --add-data "/usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0:." \
    --add-data "/usr/lib/x86_64-linux-gnu/qt5/plugins/:plugins" \
    --add-data "/usr/lib/x86_64-linux-gnu/qt5/qml/:qml" \
    --exclude-module PyQt5.Qt3D \
    --exclude-module PyQt5.Qt3DAnimation \
    --exclude-module PyQt5.QtBodymovin \
    "$SCRIPT_DIR/main.py"

echo "📁 Preparando AppDir..."
rm -rf "$BUILD_DIR/AppDir"
mkdir -p "$BUILD_DIR/AppDir/usr/bin"

# Copiar winetricks (descargar si no existe en src)
if [ -f "$SRC_DIR/winetricks" ]; then
    cp "$SRC_DIR/winetricks" "$BUILD_DIR/AppDir/usr/bin/winetricks"
else
    wget -O "$BUILD_DIR/AppDir/usr/bin/winetricks" https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
fi
chmod +x "$BUILD_DIR/AppDir/usr/bin/winetricks"

cp "$BUILD_DIR/dist/$APP_NAME" "$BUILD_DIR/AppDir/usr/bin/main"

echo "🏃 Creando AppRun..."
cat << 'EOF' > "$BUILD_DIR/AppDir/AppRun"
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}/usr/lib/plugins"
export QML2_IMPORT_PATH="${HERE}/usr/lib/qml"
exec "${HERE}/usr/bin/main" "$@"
EOF
chmod +x "$BUILD_DIR/AppDir/AppRun"

echo "🖥️ Creando archivo .desktop..."
cat << EOF > "$BUILD_DIR/AppDir/$APP_NAME.desktop"
[Desktop Entry]
Name=$APP_NAME v$APP_VERSION
Exec=main
Icon=$APP_NAME
Type=Application
Categories=Utility;
Comment=Herramienta de gestión para Wine/Proton
EOF

echo "🖼️ Procesando icono..."
mkdir -p "$BUILD_DIR/AppDir/usr/share/icons/hicolor/512x512/apps"
if [ -f "$ICONS_DIR/$APP_NAME.png" ]; then
    cp "$ICONS_DIR/$APP_NAME.png" "$BUILD_DIR/AppDir/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"
else
    echo "⚠️ Creando icono temporal..."
    convert -size 512x512 xc:white -fill black -draw "circle 256,256 256,50" "$BUILD_DIR/AppDir/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"
fi

echo "🏗️ Construyendo AppImage..."
cd "$BUILD_DIR"
./linuxdeploy-x86_64.AppImage \
    --appdir AppDir \
    -e "AppDir/usr/bin/main" \
    -i "AppDir/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png" \
    -d "AppDir/$APP_NAME.desktop" \
    --output appimage

ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir

echo "🔍 Finalizando construcción..."
APPIMAGE_OUT=$(ls "$BUILD_DIR"/*.AppImage | grep "$APP_NAME" | head -n 1)
if [ -n "$APPIMAGE_OUT" ]; then
    mv "$APPIMAGE_OUT" "$SCRIPT_DIR/$APP_NAME-v$APP_VERSION-x86_64.AppImage"
    echo -e "\n\033[1;32m✅ ¡Compilación exitosa!\033[0m"
    echo "AppImage creada: $SCRIPT_DIR/$APP_NAME-v$APP_VERSION-x86_64.AppImage"
else
    echo -e "\n\033[1;31m❌ Error: No se pudo encontrar la AppImage generada\033[0m"
    exit 1
fi
