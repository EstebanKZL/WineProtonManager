#!/bin/bash

# Salir en caso de error
set -e

# Actualizar e instalar dependencias
sudo apt update && sudo apt upgrade -y
sudo apt install -y wine winetricks konsole kdialog libssl3 git wget

# Descargar linuxdeploy y appimagetool
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage

wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Crear AppDir y AppRun
mkdir -p AppDir/usr/bin

cat << 'EOF' > AppDir/AppRun
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/main" "$@"
EOF

chmod +x AppDir/AppRun

# Compilar binario con PyInstaller
pyinstaller --onefile \
  --add-binary '/usr/lib/x86_64-linux-gnu/libssl.so.3:.' \
  --add-binary '/usr/lib/x86_64-linux-gnu/libcrypto.so.3:.' \
  --add-binary '/usr/lib/x86_64-linux-gnu/libcurl.so.4:.' \
  --add-binary '/usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0:.' \
  main.py

# Copiar binario a AppDir
cp dist/main AppDir/usr/bin/

# Asegurarse de tener icono y desktop file
if [ ! -f "icons/WineProtonManager.png" ]; then
  echo "Advertencia: No se encontró icons/WineProtonManager.png"
fi

if [ ! -f "AppDir/WineProtonManager.desktop" ]; then
  echo "Advertencia: No se encontró AppDir/WineProtonManager.desktop"
fi

# Construir AppImage
./linuxdeploy-x86_64.AppImage --appdir AppDir -e dist/main -i icons/WineProtonManager.png -d AppDir/WineProtonManager.desktop
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir

echo ""
echo "? Construcción completa. Para ejecutar:"
echo "./WineProtonManager-v1.3.0-x86_64.AppImage"
