#!/bin/bash
# Build Ulauncher .deb packages for multiple distributions

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APT_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$APT_DIR")"
BUILD_DIR="${APT_DIR}/build"
DIST_DIR="${APT_DIR}/dist"

# Supported distributions
DISTROS=(
    "ubuntu:noble:24.04"     # Ubuntu 24.04 LTS (Noble)
    "ubuntu:jammy:22.04"     # Ubuntu 22.04 LTS (Jammy)
    "ubuntu:focal:20.04"     # Ubuntu 20.04 LTS (Focal)
    "debian:bookworm:12"     # Debian 12 (Bookworm)
    "debian:bullseye:11"     # Debian 11 (Bullseye)
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v nfpm &> /dev/null; then
        log_error "nfpm not found. Install it from: https://github.com/goreleaser/nfpm/releases"
        log_info "Quick install: go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest"
        exit 1
    fi
    
    if ! command -v gzip &> /dev/null; then
        log_error "gzip not found. Please install it."
        exit 1
    fi
    
    log_success "All dependencies found"
}

get_version() {
    # Get version from ulauncher Python module
    cd "$ROOT_DIR"
    VERSION=$(python3 -c "import ulauncher; print(ulauncher.version)")
    
    if [[ -z "$VERSION" ]]; then
        log_error "Could not determine Ulauncher version"
        exit 1
    fi
    
    # Replace hyphens with tildes for proper Debian version sorting
    # e.g., 6.0.0-beta1 becomes 6.0.0~beta1
    VERSION="${VERSION//-/~}"
    
    echo "$VERSION"
}

prepare_build_dir() {
    log_info "Preparing build directory..."
    
    # Clean and create build directory
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    # Copy source files to build directory
    rsync -a \
        --exclude='.git' \
        --exclude='.github' \
        --exclude='.venv' \
        --exclude='.pytest_cache' \
        --exclude='.mypy_cache' \
        --exclude='.ruff_cache' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.tmp' \
        --exclude='build' \
        --exclude='dist' \
        --exclude='debian' \
        --exclude='nix' \
        --exclude='apt/build' \
        --exclude='apt/dist' \
        --exclude='apt/repo' \
        --exclude='tests' \
        --exclude='docs' \
        --exclude='scripts' \
        "$ROOT_DIR/" "$BUILD_DIR/"
    
    # Ensure manpage is gzipped
    if [[ -f "$BUILD_DIR/ulauncher.1" ]] && [[ ! -f "$BUILD_DIR/ulauncher.1.gz" ]]; then
        log_info "Compressing manpage..."
        gzip -9 -c "$BUILD_DIR/ulauncher.1" > "$BUILD_DIR/ulauncher.1.gz"
    fi
    
    log_success "Build directory prepared"
}

build_package() {
    local distro_type="$1"
    local distro_codename="$2"
    local distro_version="$3"
    local version="$4"
    
    # Create version with distro suffix for proper APT versioning
    local pkg_version="${version}~${distro_codename}"
    
    log_info "Building package for ${distro_type} ${distro_codename} (${distro_version})..."
    
    # Create dist directory if it doesn't exist
    mkdir -p "$DIST_DIR"
    
    # Export version for nfpm to use
    export VERSION="$pkg_version"
    
    # Build the package
    cd "$BUILD_DIR"
    nfpm package \
        --config "$APT_DIR/nfpm.yaml" \
        --packager deb \
        --target "$DIST_DIR/ulauncher_${pkg_version}_all.deb"
    
    if [[ -f "$DIST_DIR/ulauncher_${pkg_version}_all.deb" ]]; then
        log_success "Built: ulauncher_${pkg_version}_all.deb"
    else
        log_error "Failed to build package for ${distro_codename}"
        return 1
    fi
}

main() {
    log_info "Starting Ulauncher package build process..."
    
    # Check dependencies
    check_dependencies
    
    # Get version
    VERSION=$(get_version)
    log_info "Building Ulauncher version: ${VERSION}"
    
    # Prepare build directory
    prepare_build_dir
    
    # Build packages for each distro
    local built_count=0
    local failed_count=0
    
    for distro_spec in "${DISTROS[@]}"; do
        IFS=':' read -r distro_type distro_codename distro_version <<< "$distro_spec"
        
        if build_package "$distro_type" "$distro_codename" "$distro_version" "$VERSION"; then
            ((built_count++))
        else
            ((failed_count++))
        fi
    done
    
    # Summary
    echo ""
    log_info "Build summary:"
    log_success "Successfully built: ${built_count} packages"
    
    if [[ $failed_count -gt 0 ]]; then
        log_error "Failed: ${failed_count} packages"
    fi
    
    echo ""
    log_info "Packages available in: ${DIST_DIR}"
    ls -lh "$DIST_DIR"/*.deb 2>/dev/null || true
    
    if [[ $failed_count -gt 0 ]]; then
        exit 1
    fi
    
    log_success "All packages built successfully!"
}

# Run main function
main "$@"