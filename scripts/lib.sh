#!/usr/bin/env bash
# VibeCast Studio - Shared Library Functions
# This file is sourced by all other scripts

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VIBECAST_DIR="$PROJECT_ROOT/.vibecast"
PID_DIR="$VIBECAST_DIR/pids"
LOG_DIR="$VIBECAST_DIR/logs"
CONFIG_FILE="$VIBECAST_DIR/config"

# ============================================================================
# COLORS
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}${BOLD}         VibeCast Studio $1${NC}${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${DIM}ℹ${NC} $1"
}

print_url() {
    echo -e "  ${CYAN}$1${NC}: ${WHITE}$2${NC}"
}

# Spinner for long operations
spinner() {
    local pid=$1
    local message=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i + 1) % 10 ))
        printf "\r${BLUE}${spin:$i:1}${NC} %s" "$message"
        sleep 0.1
    done
    printf "\r"
}

# ============================================================================
# PLATFORM DETECTION
# ============================================================================

detect_platform() {
    # Check for NVIDIA GPU first
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
        echo "nvidia"
    # Check for Apple Silicon
    elif [[ "$(uname -s)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
        echo "apple"
    # Fallback to CPU
    else
        echo "cpu"
    fi
}

get_platform_name() {
    local platform=$1
    case "$platform" in
        nvidia) echo "NVIDIA GPU (CUDA)" ;;
        apple)  echo "Apple Silicon (MPS)" ;;
        cpu)    echo "CPU Only" ;;
        *)      echo "Unknown" ;;
    esac
}

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

ensure_vibecast_dir() {
    mkdir -p "$VIBECAST_DIR" "$PID_DIR" "$LOG_DIR"
}

save_config() {
    local key=$1
    local value=$2
    ensure_vibecast_dir

    if [[ -f "$CONFIG_FILE" ]]; then
        # Remove existing key if present
        grep -v "^${key}=" "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" 2>/dev/null || true
        mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
    fi

    echo "${key}=${value}" >> "$CONFIG_FILE"
}

load_config() {
    local key=$1
    local default=${2:-}

    if [[ -f "$CONFIG_FILE" ]]; then
        local value
        value=$(grep "^${key}=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2-)
        if [[ -n "$value" ]]; then
            echo "$value"
            return
        fi
    fi

    echo "$default"
}

# ============================================================================
# PROCESS MANAGEMENT
# ============================================================================

save_pid() {
    local name=$1
    local pid=$2
    ensure_vibecast_dir
    echo "$pid" > "$PID_DIR/${name}.pid"
}

get_pid() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if [[ -f "$pid_file" ]]; then
        cat "$pid_file"
    fi
}

is_process_running() {
    local name=$1
    local pid
    pid=$(get_pid "$name")

    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

kill_process() {
    local name=$1
    local pid
    pid=$(get_pid "$name")

    if [[ -n "$pid" ]]; then
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [[ $count -lt 30 ]]; do
                sleep 0.5
                ((count++))
            done
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$PID_DIR/${name}.pid"
    fi
}

# ============================================================================
# DOCKER HELPERS
# ============================================================================

docker_compose_cmd() {
    local platform
    platform=$(load_config "platform" "cpu")

    if [[ "$platform" == "nvidia" ]]; then
        echo "docker compose -f docker-compose.yml -f docker-compose.nvidia.yml"
    else
        echo "docker compose"
    fi
}

is_docker_running() {
    docker info &>/dev/null
}

are_containers_running() {
    local compose_cmd
    compose_cmd=$(docker_compose_cmd)

    cd "$PROJECT_ROOT"
    local running
    running=$($compose_cmd ps -q 2>/dev/null | wc -l | tr -d ' ')
    running=${running:-0}

    [[ "$running" -gt 0 ]]
}

get_container_status() {
    local service=$1
    local compose_cmd
    compose_cmd=$(docker_compose_cmd)

    cd "$PROJECT_ROOT"
    $compose_cmd ps "$service" --format "{{.Status}}" 2>/dev/null | head -1
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

check_backend_health() {
    curl -sf http://localhost:8000/api/v1/health &>/dev/null
}

check_frontend_health() {
    curl -sf http://localhost:3000/health &>/dev/null
}

check_redis_health() {
    docker exec vibecast-studio-redis-1 redis-cli ping &>/dev/null 2>&1 || \
    docker exec vibecast-studio_redis_1 redis-cli ping &>/dev/null 2>&1
}

wait_for_service() {
    local name=$1
    local check_cmd=$2
    local timeout=${3:-60}
    local count=0

    while ! eval "$check_cmd" && [[ $count -lt $timeout ]]; do
        sleep 1
        ((count++))
    done

    if [[ $count -ge $timeout ]]; then
        return 1
    fi
    return 0
}

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

check_docker() {
    if ! command -v docker &>/dev/null; then
        print_error "Docker is not installed"
        echo "  Install from: https://docs.docker.com/get-docker/"
        return 1
    fi

    if ! is_docker_running; then
        print_error "Docker is not running"
        echo "  Please start Docker Desktop or the Docker daemon"
        return 1
    fi

    return 0
}

check_python() {
    if command -v python3.11 &>/dev/null; then
        echo "python3.11"
    elif command -v python3 &>/dev/null; then
        local version
        version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$version" == "3.11" ]] || [[ "$version" == "3.12" ]] || [[ "$version" == "3.13" ]]; then
            echo "python3"
        else
            return 1
        fi
    else
        return 1
    fi
}

check_venv() {
    [[ -d "$PROJECT_ROOT/backend/venv" ]] && [[ -f "$PROJECT_ROOT/backend/venv/bin/activate" ]]
}

# ============================================================================
# INTERACTIVE PROMPTS
# ============================================================================

prompt_yes_no() {
    local prompt=$1
    local default=${2:-y}
    local response

    if [[ "$default" == "y" ]]; then
        read -r -p "$prompt [Y/n]: " response
        response=${response:-y}
    else
        read -r -p "$prompt [y/N]: " response
        response=${response:-n}
    fi

    [[ "$response" =~ ^[Yy] ]]
}

prompt_choice() {
    local prompt=$1
    shift
    local options=("$@")

    echo "" >&2
    echo "$prompt" >&2
    echo "" >&2

    local i=1
    for opt in "${options[@]}"; do
        echo -e "  ${CYAN}[$i]${NC} $opt" >&2
        ((i++))
    done
    echo "" >&2

    local choice
    read -r -p "Enter choice [1-${#options[@]}]: " choice

    if [[ "$choice" =~ ^[0-9]+$ ]] && [[ "$choice" -ge 1 ]] && [[ "$choice" -le ${#options[@]} ]]; then
        echo "$choice"
    else
        echo "0"
    fi
}

prompt_input() {
    local prompt=$1
    local default=${2:-}
    local response

    if [[ -n "$default" ]]; then
        read -r -p "$prompt [$default]: " response
        echo "${response:-$default}"
    else
        read -r -p "$prompt: " response
        echo "$response"
    fi
}

prompt_secret() {
    local prompt=$1
    local response

    read -r -s -p "$prompt: " response
    echo ""
    echo "$response"
}
