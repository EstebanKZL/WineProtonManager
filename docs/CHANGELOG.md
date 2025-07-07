# Changelog

## [v1.2.0] - 2025-07-06 🎉

#### 1. Gestión de Consola (Konsole)
- **Nuevo**: Cierre automático de Konsole al finalizar cada instalación
- **Cambio**: Reemplazo de `--noclose` por `--hold` para mejor comportamiento
- **Añadido**: Comando `exit` explícito para garantizar cierre de terminal
- **Optimización**: Tiempo de espera reducido entre instalaciones

#### 2. Sistema de Logs Mejorado
- **Nuevo**: Captura completa del output de consola en archivos log
- **Mejora**: Formato estandarizado con marcas de inicio/fin
- **Añadido**: Registro del comando exacto ejecutado
- **Fijo**: Corrección de encoding (UTF-8) para caracteres especiales

#### 3. Flujo de Instalación
- **Optimización**: Uso de `subprocess.Popen` + `wait()` para mejor control
- **Mejora**: Manejo consistente para .exe y componentes winetricks
- **Fijo**: Eliminación adecuada de archivos temporales post-instalación

#### 4. Experiencia de Usuario
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
