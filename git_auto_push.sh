#!/bin/bash

# Script automatizado para GitHub
# Versión: 2.0
# Autor: Generado y mejorado con IA

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CONFIG_DIR="$HOME/.config/git_auto"
CONFIG_FILE="$CONFIG_DIR/config.conf"
LOG_FILE="$CONFIG_DIR/error.log"

mkdir -p "$CONFIG_DIR"
touch "$LOG_FILE"

# Funciones auxiliares

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

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        GIT_USERNAME=""
        GIT_EMAIL=""
        REPO_URL=""
        DEFAULT_BRANCH="main"
        USE_SSH=false
        TOKEN=""
    fi
}

save_config() {
    cat > "$CONFIG_FILE" <<EOL
GIT_USERNAME="$GIT_USERNAME"
GIT_EMAIL="$GIT_EMAIL"
REPO_URL="$REPO_URL"
DEFAULT_BRANCH="$DEFAULT_BRANCH"
USE_SSH=$USE_SSH
TOKEN="$TOKEN"
EOL
    show_info "Configuración guardada."
}

setup_identity() {
    read -p "Usuario GitHub: " GIT_USERNAME
    read -p "Email: " GIT_EMAIL
    git config --global user.name "$GIT_USERNAME"
    git config --global user.email "$GIT_EMAIL"
    show_info "Identidad configurada."
}

setup_token() {
    read -p "Introduce tu GitHub Token (Personal Access Token): " TOKEN
    show_info "Token guardado localmente (no recomendado compartir)."
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

    read -p "Rama predeterminada (main/master): " DEFAULT_BRANCH
    DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

    if [ ! -d ".git" ]; then
        read -p "¿Clonar repo (c) o iniciar nuevo (i)? [c/i]: " choice
        if [[ "$choice" =~ ^[Cc]$ ]]; then
            git clone "$REPO_URL" .
        else
            git init
            git remote add origin "$REPO_URL"
        fi
    else
        git remote set-url origin "$REPO_URL"
    fi

    save_config
}

status_repo() {
    git status --short
}

commit_push() {
    git add .
    if [ -z "$1" ]; then
        read -p "Mensaje de commit (default: 'Update'): " msg
        msg="${msg:-Update}"
    else
        msg="$1"
    fi
    git commit -m "$msg"

    # Pull antes para evitar conflictos
    git pull origin "$DEFAULT_BRANCH" --rebase

    # Push con HTTPS y token
    if ! $USE_SSH; then
        url_with_token="${REPO_URL/https:\/\/github.com/https://$TOKEN@github.com}"
        git push "$url_with_token" "$DEFAULT_BRANCH"
    else
        git push origin "$DEFAULT_BRANCH"
    fi

    show_info "Cambios subidos exitosamente."
}

pull_changes() {
    git pull origin "$DEFAULT_BRANCH"
    show_info "Repo actualizado desde remoto."
}

show_config() {
    echo -e "\n${GREEN}=== Configuración actual ===${NC}"
    echo "Usuario: $GIT_USERNAME"
    echo "Email: $GIT_EMAIL"
    echo "Repo URL: $REPO_URL"
    echo "Rama: $DEFAULT_BRANCH"
    echo "Usa SSH: $USE_SSH"
    echo -e "${GREEN}==========================${NC}"
}

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
        5) status_repo; commit_push ;;
        6) pull_changes ;;
        7) show_info "¡Hasta luego!"; exit 0 ;;
        *) log_error "Opción no válida." ;;
    esac
}

# --- MAIN ---
check_git_installed
load_config

if [ $# -gt 0 ]; then
    status_repo
    commit_push "$1"
else
    while true; do
        main_menu
        read -p "Presiona Enter para continuar..."
    done
fi
