#!/bin/bash

# Script Git Automático — Versión final robusta
# Autor: IA 🤖

# ==================
# Colores
# ==================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ==================
# Configuración
# ==================
CONFIG_DIR="$HOME/.config/git_auto"
CONFIG_FILE="$CONFIG_DIR/config.conf"
LOG_FILE="$CONFIG_DIR/error.log"

mkdir -p "$CONFIG_DIR"
touch "$LOG_FILE"

# ==================
# Funciones auxiliares
# ==================
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

show_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

show_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_git_installed() {
    if ! command -v git &> /dev/null; then
        log_error "Git no está instalado. Instálalo primero."
        exit 1
    fi
}

# ==================
# Cargar y guardar config
# ==================
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        GIT_USERNAME=""
        GIT_EMAIL=""
        REPO_URL=""
        USE_SSH=false
        TOKEN=""
    fi
}

save_config() {
    cat > "$CONFIG_FILE" <<EOL
GIT_USERNAME="$GIT_USERNAME"
GIT_EMAIL="$GIT_EMAIL"
REPO_URL="$REPO_URL"
USE_SSH=$USE_SSH
TOKEN="$TOKEN"
EOL
    show_info "Configuración guardada."
}

# ==================
# Setup identidad
# ==================
setup_identity() {
    read -p "Usuario GitHub: " GIT_USERNAME
    read -p "Email: " GIT_EMAIL
    git config --global user.name "$GIT_USERNAME"
    git config --global user.email "$GIT_EMAIL"
    show_info "Identidad configurada."
}

setup_token() {
    read -p "Introduce tu GitHub Token (Personal Access Token): " TOKEN
    show_info "Token guardado localmente (no lo compartas)."
}

setup_repository() {
    read -p "¿Usar SSH? (s/N): " use_ssh
    if [[ "$use_ssh" =~ ^[SsYy]$ ]]; then
        USE_SSH=true
        read -p "Usuario GitHub: " gh_user
        read -p "Nombre del repo: " repo_name
        REPO_URL="git@github.com:$gh_user/$repo_name.git"
    else
        USE_SSH=false
        read -p "URL HTTPS del repo: " REPO_URL
    fi

    if git remote | grep -q origin; then
        git remote set-url origin "$REPO_URL"
    else
        git remote add origin "$REPO_URL"
    fi

    save_config
}

get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null
}

# ==================
# Operaciones
# ==================
commit_push() {
    git add .

    if [ -z "$1" ]; then
        read -p "Mensaje de commit (default: 'Update'): " msg
        msg="${msg:-Update}"
    else
        msg="$1"
    fi

    if [ -z "$(git status --porcelain)" ]; then
        show_info "No hay cambios para commit."
        return 0
    fi

    git commit -m "$msg"

    BRANCH=$(get_current_branch)
    if [ -z "$BRANCH" ]; then
        log_error "No se pudo determinar la rama actual."
        return 1
    fi

    show_info "Actualizando con el remoto (pull --rebase)..."

    if ! git pull origin "$BRANCH" --rebase; then
        log_error "Falló el rebase. Revisa conflictos manualmente:"
        echo "  git status"
        echo "  git add <archivos>"
        echo "  git rebase --continue   # para seguir"
        echo "  git rebase --abort      # para cancelar"
        return 1
    fi

    show_info "Rebase completado. Enviando cambios..."

    if ! $USE_SSH; then
        if [ -z "$TOKEN" ]; then
            log_error "No hay token configurado. Usa el menú para configurarlo primero (opción 2)."
            return 1
        fi
        url_with_token="${REPO_URL/https:\/\/github.com/https://$TOKEN@github.com}"
        git push "$url_with_token" "$BRANCH"
    else
        git push origin "$BRANCH"
    fi

    if [ $? -eq 0 ]; then
        show_info "¡Cambios subidos exitosamente!"
    else
        log_error "El push falló. Verifica la conexión, token o acceso SSH."
    fi
}

pull_changes() {
    BRANCH=$(get_current_branch)
    if [ -z "$BRANCH" ]; then
        log_error "No se pudo determinar la rama actual."
        return 1
    fi

    if git pull origin "$BRANCH"; then
        show_info "Repositorio actualizado desde remoto."
    else
        log_error "Falló el pull. Verifica la conexión y rama."
    fi
}

show_config() {
    echo -e "\n${GREEN}=== Configuración actual ===${NC}"
    echo "Usuario: $GIT_USERNAME"
    echo "Email: $GIT_EMAIL"
    echo "Repo URL: $REPO_URL"
    echo "Usa SSH: $USE_SSH"
    echo "Token guardado: $( [ -n "$TOKEN" ] && echo "Sí" || echo "No" )"
    echo "Rama actual: $(get_current_branch)"
    echo -e "${GREEN}==========================${NC}"
}

# ==================
# Menú
# ==================
main_menu() {
    echo -e "\n${GREEN}=== Menú Git Automático ===${NC}"
    echo "1. Configurar identidad"
    echo "2. Configurar token"
    echo "3. Configurar repo remoto"
    echo "4. Mostrar configuración"
    echo "5. Subir cambios (commit + push)"
    echo "6. Bajar cambios (pull)"
    echo "7. Salir"

    read -p "Opción: " opt

    case $opt in
        1) setup_identity; save_config ;;
        2) setup_token; save_config ;;
        3) setup_repository ;;
        4) show_config ;;
        5) commit_push ;;
        6) pull_changes ;;
        7) show_info "¡Hasta luego!"; exit 0 ;;
        *) log_error "Opción no válida." ;;
    esac
}

# ==================
# Ejecución principal
# ==================
check_git_installed
load_config

if [ $# -gt 0 ]; then
    commit_push "$1"
else
    while true; do
        main_menu
        read -p "Presiona Enter para continuar..."
    done
fi
