#!/usr/bin/env bash
# VibeCast Studio - Start Application
# Starts all services based on configured platform

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib.sh"

# ============================================================================
# MAIN START FLOW
# ============================================================================

main() {
    print_header "Start          "

    # Check if setup has been run
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "VibeCast Studio has not been set up yet"
        print_info "Run ./setup.sh first"
        exit 1
    fi

    # Check Docker
    if ! check_docker; then
        exit 1
    fi

    # Load platform configuration
    local platform
    platform=$(load_config "platform" "cpu")

    print_info "Starting VibeCast Studio ($(get_platform_name "$platform"))..."
    echo ""

    # Check if already running
    if are_containers_running || is_process_running "backend"; then
        print_warning "VibeCast Studio appears to be already running"
        if ! prompt_yes_no "Do you want to restart?" "n"; then
            echo ""
            print_info "Use ./status.sh to check current status"
            exit 0
        fi
        echo ""
        "$SCRIPT_DIR/stop.sh" --quiet
        echo ""
    fi

    # Start based on platform
    case "$platform" in
        apple)
            start_apple_silicon
            ;;
        nvidia)
            start_nvidia
            ;;
        cpu)
            start_cpu
            ;;
        *)
            print_error "Unknown platform: $platform"
            exit 1
            ;;
    esac

    # Wait for services and show status
    wait_for_services "$platform"
    print_ready
}

# ============================================================================
# START FUNCTIONS
# ============================================================================

start_apple_silicon() {
    print_step "Starting Docker services (Redis, Frontend)..."

    cd "$PROJECT_ROOT"
    docker compose up -d redis frontend flower &>/dev/null

    print_success "Redis started"
    print_success "Frontend started"
    print_success "Flower started"
    echo ""

    # Start native backend
    print_step "Starting native backend (MPS acceleration)..."

    if ! check_venv; then
        print_error "Python virtual environment not found"
        print_info "Run ./setup.sh to configure"
        exit 1
    fi

    # Ensure log directory exists
    ensure_vibecast_dir

    # Start backend
    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate

    # Kill any existing processes on the ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true

    # Start uvicorn in background
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 \
        > "$LOG_DIR/backend.log" 2>&1 &
    save_pid "backend" $!

    print_success "Backend started (PID: $(get_pid backend))"

    # Start Celery worker
    nohup celery -A app.workers.celery_app worker -l info -c 1 -Q generation,export \
        > "$LOG_DIR/worker.log" 2>&1 &
    save_pid "worker" $!

    print_success "Worker started (PID: $(get_pid worker))"

    deactivate
    echo ""
}

start_nvidia() {
    print_step "Starting all Docker services (NVIDIA GPU)..."
    echo ""

    cd "$PROJECT_ROOT"

    # Start services one by one for better feedback
    docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d redis &>/dev/null
    print_success "Redis started"

    docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d backend &>/dev/null
    print_success "Backend started"

    docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d worker &>/dev/null
    print_success "Worker started"

    docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d beat &>/dev/null
    print_success "Beat started"

    docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d flower &>/dev/null
    print_success "Flower started"

    docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d frontend &>/dev/null
    print_success "Frontend started"

    echo ""
}

start_cpu() {
    print_step "Starting all Docker services (CPU mode)..."
    echo ""

    cd "$PROJECT_ROOT"

    # Start services one by one for better feedback
    docker compose up -d redis &>/dev/null
    print_success "Redis started"

    docker compose up -d backend &>/dev/null
    print_success "Backend started"

    docker compose up -d worker &>/dev/null
    print_success "Worker started"

    docker compose up -d beat &>/dev/null
    print_success "Beat started"

    docker compose up -d flower &>/dev/null
    print_success "Flower started"

    docker compose up -d frontend &>/dev/null
    print_success "Frontend started"

    echo ""
}

wait_for_services() {
    local platform=$1

    print_step "Waiting for services to be ready..."

    # Wait for backend health
    local backend_ready=false
    for i in {1..60}; do
        if check_backend_health; then
            backend_ready=true
            break
        fi
        sleep 1
    done

    if [[ "$backend_ready" == false ]]; then
        print_warning "Backend health check timed out (may still be starting)"
    fi

    # Wait for frontend
    local frontend_ready=false
    for i in {1..30}; do
        if check_frontend_health; then
            frontend_ready=true
            break
        fi
        sleep 1
    done

    if [[ "$frontend_ready" == false ]]; then
        print_warning "Frontend health check timed out (may still be starting)"
    fi

    echo ""
}

print_ready() {
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}${BOLD}    VibeCast Studio is ready!             ${NC}${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    print_url "Frontend" "http://localhost:3000"
    print_url "API Docs" "http://localhost:8000/docs"
    print_url "Flower  " "http://localhost:5555"
    echo ""
    echo -e "  ${DIM}Run ./stop.sh to shut down${NC}"
    echo -e "  ${DIM}Run ./logs.sh to view logs${NC}"
    echo ""
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
