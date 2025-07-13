# Instalación de WineProton Manager

## Dependencias

- Python 3.6 o superior
- PyQt5
- Wine o Proton instalado
- Konsole (para la salida de terminal)

## Instalación desde código fuente

Ejecutar aplicación

1. Clona el repositorio:
   ```bash
   sudo apt install wine winetricks konsole kdialog libssl3
   git clone https://github.com/EstebanKZL/WineProtonManager.git
   cd WineProtonManager

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt

3. Ejecuta la aplicación:

   ```bash
   python3 main.py


Creación de AppImage

1. Instala linuxdeployqt y AppImage:

   ```bash
   sudo apt install wine winetricks konsole kdialog libssl3
   git clone https://github.com/EstebanKZL/WineProtonManager.git
   cd WineProtonManager
   wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
   chmod +x linuxdeploy-x86_64.AppImage
   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
   chmod +x appimagetool-x86_64.AppImage   
   
2. Crear AppDir/AppRun

   ```bash
   mkdir -p AppDir/
   cat << 'EOF' > AppDir/AppRun
   #!/bin/bash
   HERE="$(dirname "$(readlink -f "$0")")"
   exec "$HERE/usr/bin/main" "$@"
   EOF
   chmod +x AppDir/AppRun
   
3. Construye la AppImage:

   ```bash
   pyinstaller --onefile --add-binary '/usr/lib/x86_64-linux-gnu/libssl.so.3:.' --add-binary '/usr/lib/x86_64-linux-gnu/libcrypto.so.3:.' --add-binary '/usr/lib/x86_64-linux-gnu/libcurl.so.4:.' --add-binary '/usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0:.'  main.py
   ./linuxdeploy-x86_64.AppImage --appdir AppDir -e dist/main -i icons/WineProtonManager.png -d AppDir/WineProtonManager.desktop
   ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir

4. Ejecutar programa
   
   ```bash
   ./WineProtonManager-v1.1.0-x86_64.AppImage
