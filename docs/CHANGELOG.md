# Changelog Novedades

## [v1.3.0] - 2025-07-09 🎉
### Descarga de Repositorios para Wine y Proton
- Nueva pestaña "Descargas de Versiones" en el diálogo de configuración
  - Permite añadir/eliminar/habilitar/deshabilitar repositorios de GitHub
- Búsqueda y listado de versiones disponibles:
  - Proton: desde (API de GitHub)
  - Wine: desde (API de GitHub)
- Descarga y descompresión automática en:
  - `~/.config/WineProtonManager/Wine`
  - `~/.config/WineProtonManager/Proton`
- Operaciones en hilos separados:
  - `DownloadThread` para descargas
  - `DecompressionThread` para descompresión
  - Con diálogo de progreso interactivo
- Verificación de espacio en disco antes de descargar

### Instalación Forzada (--force)
- Nueva opción de configuración (global y por sesión)
- Permite forzar instalación de componentes Winetricks con `--force`
- Útil para reinstalar/reparar componentes existentes

## Mejoras

### Diseño y Estilo (inspirado en Steam Deck)
- Rediseño completo de la interfaz con estética Steam Deck
- Centralización de variables de color
- Estilos unificados (`STYLE_STEAM_DECK`)
- Paletas de colores personalizadas para:
  - `QApplication`, `QWidget`, `QPushButton`, `QGroupBox`
  - `QLabel`, `QComboBox`, `QLineEdit`, `QListWidget`
  - `QTableWidget`, `QTreeWidget`
- Ajustes en:
  - Tamaños de fuente
  - Bordes y rellenos
  - Estados visuales (hover, pressed, disabled)

### Método de Instalación de Programas (Winetricks, EXE y WTR)
- Proceso unificado de instalación (`InstallerThread`):
  - Soporta `.exe` y `.msi`
  - Componentes Winetricks por nombre
  - Scripts Winetricks personalizados (`.wtr`)
- Ejecución en ventana Konsole separada (`nohup konsole -e ...`)
- Sistema de registro detallado por programa (`ConfigManager.write_to_log`)
- Registro de instalaciones en prefijos (`wineprotonmanager.log`)
- Tabla principal muestra estados:
  - Pendiente, Instalando..., Finalizado
  - Error, Cancelado, Omitido
  - Con indicadores de color
- Funcionalidades adicionales:
  - Selección/deselección de elementos
  - Reordenación con "Mover Arriba"/"Mover Abajo"
  - Auto-desmarcado de instalaciones exitosas

### Descripciones de Componentes en Winetricks
- Nueva columna "Descripción" en diálogo de selección
- Descripciones detalladas para:
  - Librerías de Visual Basic
  - Tiempos de ejecución de Visual C++
  - .NET Framework
  - DirectX y multimedia
  - DXVK/VKD3D
  - Códecs
  - Componentes del sistema

## Cambios Internos

### Gestión de Configuración (ConfigManager)
- Refactorización completa para centralizar configuraciones
- Inicialización con valores por defecto (ej. "Wine-System")
- Mejor manejo de variables de entorno Wine/Proton
- Nueva función `get_installed_winetricks` para historial de instalaciones

### Hilos de Ejecución
- Uso consistente de `QThread` para operaciones largas
- Mejoras en sistema de señales y slots
- Comunicación más eficiente entre hilos y GUI

### Diálogos Modales
- Aplicación automática del tema actual (`apply_theme_to_dialog`)

### Manejo de Errores
- Mayor robustez en:
  - Operaciones con archivos
  - Operaciones de red
  - Procesos externos
- Mensajes de error más informativos
- Logs temporales para instalaciones

## [v1.2.0] - 2025-07-06 🎉
#### Gestión de Consola (Konsole)
- **Nuevo**: Cierre automático de Konsole al finalizar cada instalación
- **Cambio**: Reemplazo de `--noclose` por `--hold` para mejor comportamiento
- **Añadido**: Comando `exit` explícito para garantizar cierre de terminal
- **Optimización**: Tiempo de espera reducido entre instalaciones

#### Sistema de Logs Mejorado
- **Nuevo**: Captura completa del output de consola en archivos log
- **Mejora**: Formato estandarizado con marcas de inicio/fin
- **Añadido**: Registro del comando exacto ejecutado
- **Fijo**: Corrección de encoding (UTF-8) para caracteres especiales

#### Flujo de Instalación
- **Optimización**: Uso de `subprocess.Popen` + `wait()` para mejor control
- **Mejora**: Manejo consistente para .exe y componentes winetricks
- **Fijo**: Eliminación adecuada de archivos temporales post-instalación

#### Experiencia de Usuario
- **Nuevo**: Mensajes de progreso más descriptivos
- **Mejora**: Códigos de error más informativos
- **Optimización**: Verificación previa de dependencias (konsole)

### Correcciones de Bugs
- **Fijo**: Consola que no se cerraba automáticamente
- **Fijo**: Pérdida de logs en instalaciones rápidas
- **Fijo**: Manejo de paths con espacios especiales
- **Fijo**: Limpieza de procesos residuales

### Notas de Actualización
    ```bash
    # Recomendaciones post-actualización:
    1. Verificar permisos en ~/.config/WineProtonManager/logs/
    2. Los logs antiguos mantienen su formato original
    3. El modo silencioso ahora aplica consistentemente

## [v1.1.0] - 2025-07-05 🎉
### Fixed
- Corrección de errores en gestión de prefixes
- Mejoras en la detección de versiones
- Fixed reparacion en la instlacion (.exe y .msi)

## [v1.0.0] - 2025-07-05 🎉
### Added
- Implementación inicial del gestor de entornos
- Soporte para Wine y Proton
- Sistema de instalación de componentes via Winetricks
- Interfaz con temas claro/oscuro

### Fixed
- Corrección de errores en gestión de prefixes
- Mejoras en la detección de versiones

### Known Issues
- Problemas conocidos con prefixes de 32 bits
