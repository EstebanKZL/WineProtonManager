# Changelog Novedades

## [v1.4.0] - 2025-07-12 🎉

**¡Esta versión trae una renovación significativa en la interfaz de usuario y mejoras internas clave para una experiencia más fluida y robusta!**

### ✨ Novedades y Mejoras:

* **Diseño de Interfaz Casi Nuevo (Breeze Style):**
    * Implementación de un sistema de estilos inspirado en "Breeze" de Plasma 6.0, con colores y tipografías centralizadas para un aspecto más moderno y consistente.
    * Se han definido y aplicado paletas de colores separadas para temas claros y oscuros, mejorando la legibilidad y la estética general.
    * Estilos mejorados para botones, tablas, GroupBox, listas, árboles, campos de texto (QLineEdit) y combobox (QComboBox), incluyendo efectos de `:hover` y `:pressed` para una mejor interactividad.
    * **MODIFICACIÓN 3:** Ajuste del tamaño de fuente en varios widgets como QListWidget y QTreeWidget para mejorar la densidad de información y la lectura.

* **Gestión de Logs Unificada y Mejorada:**
    * Centralización de la gestión de logs de instalación en un archivo `installation.log` dentro del directorio de configuración.
    * Implementación de un log de backup separado (`backup.log`) para un seguimiento más claro de las operaciones de respaldo.
    * Todos los mensajes de log incluyen ahora marcas de tiempo y el nombre del programa o acción, facilitando la depuración y el seguimiento.

* **Lógica de Backup Renovada y más Segura:**
    * **MODIFICACIÓN:** La ruta del último backup completo ahora se almacena por *cada configuración* de Wine/Proton, permitiendo backups incrementales (Rsync) más precisos para entornos específicos.
    * El proceso de backup completo crea una carpeta con un `timestamp` para evitar sobrescrituras accidentales.
    * Los backups incrementales (Rsync) ahora requieren un backup completo previo para la configuración actual, con advertencias claras si no existe.
    * Diálogos de backup más informativos y con opciones claras para "Rsync (Incremental)" o "Backup Completo (Nuevo)".
    * Mejoras en el manejo de errores durante el proceso de backup y limpieza de archivos temporales.

* **Mejoras en la Instalación de Programas y Componentes:**
    * **MODIFICACIÓN 1:** La lista de instalación ahora mantiene el estado de los ítems ("Finalizado", "Error", "Omitido", "Cancelado"), y los ítems con error/cancelados permanecen marcados para facilitar reintentos.
    * **MODIFICACIÓN 1:** Introducción de un `item_error` signal en `InstallerThread` para manejar errores de ítems individuales sin detener toda la secuencia de instalación.
    * El diálogo de progreso de instalación ahora es "NonModal", permitiendo al usuario interactuar con la ventana principal (ver la tabla de ítems, por ejemplo) mientras la instalación está en curso, aunque los botones de control de instalación se deshabilitan correctamente.
    * Al re-tildar un programa en la tabla después de una instalación, su estado se restablece a "Pendiente".
    * Mensajes de advertencia más claros al intentar añadir programas/componentes que ya están en la lista o registrados como instalados en el prefijo.
    * El proceso de inicialización de prefijos (`wineboot`) ahora se maneja de forma más robusta y con mensajes de progreso.
    * **MODIFICACIÓN 3:** Los registros de instalación exitosa en `wineprotonmanager.ini` ahora incluyen el tipo de ítem y la ruta/nombre original para mayor detalle.

* **Direccionamiento y Persistencia de Rutas de Carpeta:**
    * **MODIFICACIÓN 4:** La aplicación ahora recuerda la última carpeta explorada para diferentes tipos de archivos (prefijos Wine/Proton, instalaciones de Wine/Proton, programas, Winetricks), mejorando la usabilidad al abrir diálogos de archivo.

* **Robustez y Manejo de Errores:**
    * Mejora general en el manejo de excepciones y validaciones de rutas para operaciones críticas (descargas, descompresiones, comandos de Wine/Proton).
    * Aumento del límite de recursión de Python para prevenir `RecursionError` en entornos con muchas configuraciones o listas largas.
    * Manejo más eficiente de la interrupción de hilos de descarga e instalación.

### ⚠️ Consideraciones Importantes:

* **Reiniciar la Aplicación:** Los cambios en la configuración del tema y otras configuraciones generales ahora requieren un reinicio completo de la aplicación para aplicarse globalmente. El diálogo de configuración lo indicará y facilitará el reinicio.
* **Permisos de Winetricks:** Se ha mejorado la detección y validación de la ruta de Winetricks. Si tienes problemas, asegúrate de que el archivo `winetricks` tenga permisos de ejecución.
* **Compatibilidad de Winetricks Scripts (.wtr):** La adición de scripts `.wtr` personalizados para instalación de componentes de Winetricks permite mayor flexibilidad.
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
-   **Nuevo**: Cierre automático de Konsole al finalizar cada instalación
-   **Cambio**: Reemplazo de `--noclose` por `--hold` para mejor comportamiento
-   **Añadido**: Comando `exit` explícito para garantizar cierre de terminal
-   **Optimización**: Tiempo de espera reducido entre instalaciones

#### Sistema de Logs Mejorado
-   **Nuevo**: Captura completa del output de consola en archivos log
-   **Mejora**: Formato estandarizado con marcas de inicio/fin
-   **Añadido**: Registro del comando exacto ejecutado
-   **Fijo**: Corrección de encoding (UTF-8) para caracteres especiales

#### Flujo de Instalación
-   **Optimización**: Uso de `subprocess.Popen` + `wait()` para mejor control
-   **Mejora**: Manejo consistente para .exe y componentes winetricks
-   **Fijo**: Eliminación adecuada de archivos temporales post-instalación

#### Experiencia de Usuario
-   **Nuevo**: Mensajes de progreso más descriptivos
-   **Mejora**: Códigos de error más informativos
-   **Optimización**: Verificación previa de dependencias (konsole)

### Correcciones de Bugs
-   **Fijo**: Consola que no se cerraba automáticamente
-   **Fijo**: Pérdida de logs en instalaciones rápidas
-   **Fijo**: Manejo de paths con espacios especiales
-   **Fijo**: Limpieza de procesos residuales

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
