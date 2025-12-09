#!/usr/bin/env bash
# VibeCast Studio - First-Time Setup Wizard
# Run this script once to configure your environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib.sh"

# ============================================================================
# MAIN SETUP FLOW
# ============================================================================

main() {
    print_header "Setup          "

    # Check if already set up
    if [[ -f "$CONFIG_FILE" ]] && [[ -f "$PROJECT_ROOT/.env" ]]; then
        print_warning "VibeCast Studio appears to be already configured."
        if ! prompt_yes_no "Do you want to reconfigure?" "n"; then
            echo ""
            print_info "Run ./start.sh to launch the application"
            exit 0
        fi
        echo ""
    fi

    # Step 1: Check prerequisites
    check_prerequisites

    # Step 2: Detect and select platform
    select_platform

    # Step 3: Configure environment
    configure_environment

    # Step 4: Platform-specific setup
    local platform
    platform=$(load_config "platform")

    case "$platform" in
        apple)
            setup_apple_silicon
            ;;
        nvidia)
            setup_nvidia
            ;;
        cpu)
            setup_cpu
            ;;
    esac

    # Step 5: Pull Docker images
    pull_docker_images

    # Step 6: Create storage directories
    create_storage_dirs

    # Final message
    print_setup_complete
}

# ============================================================================
# SETUP FUNCTIONS
# ============================================================================

check_prerequisites() {
    print_step "Checking prerequisites..."
    echo ""

    local all_good=true

    # Docker
    if check_docker; then
        print_success "Docker is installed and running"
    else
        all_good=false
    fi

    # Python (only needed for Apple Silicon native mode)
    local python_cmd
    if python_cmd=$(check_python); then
        print_success "Python is available ($python_cmd)"
    else
        print_warning "Python 3.11+ not found (only needed for Apple Silicon native mode)"
    fi

    echo ""

    if [[ "$all_good" == false ]]; then
        print_error "Please install missing prerequisites and try again"
        exit 1
    fi
}

select_platform() {
    print_step "Detecting platform..."
    echo ""

    local detected
    detected=$(detect_platform)
    local detected_name
    detected_name=$(get_platform_name "$detected")

    echo -e "  Detected: ${GREEN}${detected_name}${NC}"
    echo ""

    local platform="$detected"

    # Offer choice for Apple Silicon (can also use CPU mode)
    if [[ "$detected" == "apple" ]]; then
        local choice
        choice=$(prompt_choice "Select mode:" \
            "Use MPS acceleration (recommended for Apple Silicon)" \
            "Use CPU only (Docker, slower but simpler)")

        case "$choice" in
            1) platform="apple" ;;
            2) platform="cpu" ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
    fi

    # Offer choice for NVIDIA (can also use CPU mode)
    if [[ "$detected" == "nvidia" ]]; then
        local choice
        choice=$(prompt_choice "Select mode:" \
            "Use CUDA acceleration (recommended for NVIDIA GPU)" \
            "Use CPU only (Docker, no GPU)")

        case "$choice" in
            1) platform="nvidia" ;;
            2) platform="cpu" ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
    fi

    save_config "platform" "$platform"
    echo ""
    print_success "Platform configured: $(get_platform_name "$platform")"
    echo ""
}

configure_environment() {
    print_step "Configuring environment..."
    echo ""

    # Create .env from .env.example if needed
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success "Created .env from .env.example"
        else
            touch "$PROJECT_ROOT/.env"
            print_success "Created empty .env file"
        fi
    else
        print_info ".env file already exists"
    fi

    # Prompt for Claude API key
    echo ""
    print_info "Claude API key enables AI-powered dialogue enhancement (optional)"

    local current_key=""
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        current_key=$(grep "^CLAUDE_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- || true)
    fi

    if [[ -n "$current_key" ]] && [[ "$current_key" != "your-claude-api-key-here" ]]; then
        print_info "Claude API key is already configured"
        if prompt_yes_no "Do you want to update it?" "n"; then
            current_key=""
        fi
    fi

    if [[ -z "$current_key" ]] || [[ "$current_key" == "your-claude-api-key-here" ]]; then
        echo ""
        local api_key
        api_key=$(prompt_input "Enter Claude API key (or press Enter to skip)")

        if [[ -n "$api_key" ]]; then
            # Update or add the key in .env
            if grep -q "^CLAUDE_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null; then
                sed -i.bak "s|^CLAUDE_API_KEY=.*|CLAUDE_API_KEY=$api_key|" "$PROJECT_ROOT/.env"
                rm -f "$PROJECT_ROOT/.env.bak"
            else
                echo "CLAUDE_API_KEY=$api_key" >> "$PROJECT_ROOT/.env"
            fi
            print_success "Claude API key saved"
        else
            print_info "Skipping Claude API key (can be added later in .env)"
        fi
    fi

    echo ""
}

setup_apple_silicon() {
    print_step "Setting up for Apple Silicon..."
    echo ""

    # Check Python
    local python_cmd
    if ! python_cmd=$(check_python); then
        print_error "Python 3.11+ is required for Apple Silicon native mode"
        print_info "Install with: brew install python@3.11"
        exit 1
    fi

    # Create virtual environment if it doesn't exist
    if ! check_venv; then
        print_info "Creating Python virtual environment..."
        cd "$PROJECT_ROOT/backend"
        $python_cmd -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi

    # Install Python dependencies
    print_info "Installing Python dependencies (this may take a while)..."
    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    deactivate
    print_success "Python dependencies installed"

    echo ""
}

setup_nvidia() {
    print_step "Setting up for NVIDIA GPU..."
    echo ""

    # Verify NVIDIA Container Toolkit
    if ! docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi &>/dev/null; then
        print_warning "Could not verify NVIDIA Container Toolkit"
        print_info "Make sure nvidia-container-toolkit is installed:"
        print_info "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        echo ""
        if ! prompt_yes_no "Continue anyway?" "y"; then
            exit 1
        fi
    else
        print_success "NVIDIA Container Toolkit verified"
    fi

    echo ""
}

setup_cpu() {
    print_step "Setting up for CPU mode..."
    echo ""
    print_info "No additional setup needed for CPU mode"
    print_warning "Note: TTS generation will be significantly slower without GPU acceleration"
    echo ""
}

pull_docker_images() {
    print_step "Pulling Docker images..."
    echo ""

    local compose_cmd
    compose_cmd=$(docker_compose_cmd)

    cd "$PROJECT_ROOT"

    # Pull images in background
    $compose_cmd pull --quiet &
    local pid=$!
    spinner $pid "Pulling images..."
    wait $pid || true

    print_success "Docker images ready"
    echo ""
}

create_storage_dirs() {
    print_step "Creating storage directories..."

    mkdir -p "$PROJECT_ROOT/storage/audio"
    mkdir -p "$PROJECT_ROOT/storage/exports"
    mkdir -p "$PROJECT_ROOT/storage/uploads"
    mkdir -p "$PROJECT_ROOT/storage/music"
    mkdir -p "$PROJECT_ROOT/storage/projects"

    ensure_vibecast_dir

    print_success "Storage directories created"
    echo ""
}

print_setup_complete() {
    local platform
    platform=$(load_config "platform")

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}${BOLD}       Setup Complete!                    ${NC}${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Platform: ${CYAN}$(get_platform_name "$platform")${NC}"
    echo ""
    echo -e "  ${BOLD}Next steps:${NC}"
    echo -e "    ${WHITE}./start.sh${NC}  - Start VibeCast Studio"
    echo -e "    ${WHITE}./stop.sh${NC}   - Stop all services"
    echo -e "    ${WHITE}./status.sh${NC} - Check status"
    echo -e "    ${WHITE}./logs.sh${NC}   - View logs"
    echo ""

    if [[ "$platform" == "apple" ]]; then
        print_info "Apple Silicon mode runs backend natively for MPS acceleration"
    fi
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
