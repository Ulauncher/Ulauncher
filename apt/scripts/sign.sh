#!/bin/bash
# Sign Ulauncher .deb packages with GPG

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${APT_DIR}/dist"

# GPG configuration
GPG_KEY_ID="${GPG_KEY_ID:-}"
GPG_PASSPHRASE="${GPG_PASSPHRASE:-}"

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
    
    if ! command -v dpkg-sig &> /dev/null; then
        log_error "dpkg-sig not found. Install it with: sudo apt-get install dpkg-sig"
        exit 1
    fi
    
    if ! command -v gpg &> /dev/null; then
        log_error "gpg not found. Please install GnuPG."
        exit 1
    fi
    
    log_success "All dependencies found"
}

check_gpg_key() {
    log_info "Checking GPG configuration..."
    
    if [[ -z "$GPG_KEY_ID" ]]; then
        log_error "GPG_KEY_ID not set"
        log_info "Export GPG_KEY_ID environment variable with your signing key ID"
        log_info "Example: export GPG_KEY_ID=your-key-id"
        exit 1
    fi
    
    # Check if key exists
    if ! gpg --list-secret-keys "$GPG_KEY_ID" &> /dev/null; then
        log_error "GPG key $GPG_KEY_ID not found in keyring"
        log_info "Import your key with: gpg --import your-secret-key.asc"
        exit 1
    fi
    
    log_success "GPG key $GPG_KEY_ID found"
}

sign_package() {
    local deb_file="$1"
    
    log_info "Signing $(basename "$deb_file")..."
    
    # Sign with dpkg-sig using SHA-256
    if [[ -n "$GPG_PASSPHRASE" ]]; then
        # Use passphrase from environment (for CI)
        echo "$GPG_PASSPHRASE" | dpkg-sig \
            --sign builder \
            --gpg-options "--pinentry-mode loopback --passphrase-fd 0 --digest-algo SHA256" \
            -k "$GPG_KEY_ID" \
            "$deb_file"
    else
        # Interactive mode (will prompt for passphrase)
        dpkg-sig \
            --sign builder \
            --gpg-options "--digest-algo SHA256" \
            -k "$GPG_KEY_ID" \
            "$deb_file"
    fi
    
    # Verify signature
    if dpkg-sig --verify "$deb_file" &> /dev/null; then
        log_success "Signed and verified: $(basename "$deb_file")"
        return 0
    else
        log_error "Failed to verify signature for $(basename "$deb_file")"
        return 1
    fi
}

main() {
    log_info "Starting package signing process..."
    
    # Check dependencies
    check_dependencies
    
    # Check GPG key
    check_gpg_key
    
    # Find all .deb files
    if [[ ! -d "$DIST_DIR" ]]; then
        log_error "Distribution directory not found: $DIST_DIR"
        log_info "Run build.sh first to create packages"
        exit 1
    fi
    
    local deb_files=("$DIST_DIR"/*.deb)
    
    if [[ ! -e "${deb_files[0]}" ]]; then
        log_error "No .deb files found in $DIST_DIR"
        log_info "Run build.sh first to create packages"
        exit 1
    fi
    
    log_info "Found ${#deb_files[@]} package(s) to sign"
    
    # Sign each package
    local signed_count=0
    local failed_count=0
    
    for deb_file in "${deb_files[@]}"; do
        if sign_package "$deb_file"; then
            ((signed_count++))
        else
            ((failed_count++))
        fi
    done
    
    # Summary
    echo ""
    log_info "Signing summary:"
    log_success "Successfully signed: ${signed_count} packages"
    
    if [[ $failed_count -gt 0 ]]; then
        log_error "Failed: ${failed_count} packages"
        exit 1
    fi
    
    log_success "All packages signed successfully!"
}

# Run main function
main "$@"