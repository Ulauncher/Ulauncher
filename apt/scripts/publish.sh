#!/bin/bash
# Publish Ulauncher packages to APT repository and deploy to GitHub Pages

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${APT_DIR}/dist"
REPO_DIR="${APT_DIR}/repo"

# GPG configuration
GPG_KEY_ID="${GPG_KEY_ID:-}"

# Repository configuration
REPO_ORIGIN="Ulauncher"
REPO_LABEL="Ulauncher APT Repository"
REPO_SUITE="stable"
REPO_CODENAME="ulauncher"
REPO_COMPONENTS="main"
REPO_ARCHITECTURES="all amd64 i386 arm64 armhf"
REPO_DESCRIPTION="Official Ulauncher APT repository"

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
    
    if ! command -v dpkg-scanpackages &> /dev/null; then
        log_error "dpkg-scanpackages not found. Install it with: sudo apt-get install dpkg-dev"
        exit 1
    fi
    
    if ! command -v apt-ftparchive &> /dev/null; then
        log_error "apt-ftparchive not found. Install it with: sudo apt-get install apt-utils"
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
        exit 1
    fi
    
    if ! gpg --list-secret-keys "$GPG_KEY_ID" &> /dev/null; then
        log_error "GPG key $GPG_KEY_ID not found in keyring"
        exit 1
    fi
    
    log_success "GPG key $GPG_KEY_ID found"
}

create_repo_structure() {
    log_info "Creating repository structure..."
    
    # Create directory structure
    mkdir -p "$REPO_DIR"/{pool,dists/"$REPO_CODENAME"/"$REPO_COMPONENTS"/binary-all}
    
    log_success "Repository structure created"
}

copy_packages_to_pool() {
    log_info "Copying packages to pool..."
    
    if [[ ! -d "$DIST_DIR" ]]; then
        log_error "Distribution directory not found: $DIST_DIR"
        exit 1
    fi
    
    local deb_files=("$DIST_DIR"/*.deb)
    
    if [[ ! -e "${deb_files[0]}" ]]; then
        log_error "No .deb files found in $DIST_DIR"
        exit 1
    fi
    
    # Copy all .deb files to pool
    for deb_file in "${deb_files[@]}"; do
        cp -v "$deb_file" "$REPO_DIR/pool/"
    done
    
    log_success "Packages copied to pool"
}

generate_packages_index() {
    log_info "Generating Packages index..."
    
    cd "$REPO_DIR"
    
    # Generate Packages file
    dpkg-scanpackages \
        --multiversion \
        pool \
        /dev/null \
        > "dists/$REPO_CODENAME/$REPO_COMPONENTS/binary-all/Packages"
    
    # Compress Packages file
    gzip -9 -k -f "dists/$REPO_CODENAME/$REPO_COMPONENTS/binary-all/Packages"
    
    log_success "Packages index generated"
}

generate_release_file() {
    log_info "Generating Release file..."
    
    cd "$REPO_DIR/dists/$REPO_CODENAME"
    
    # Create Release file
    cat > Release << EOF
Origin: $REPO_ORIGIN
Label: $REPO_LABEL
Suite: $REPO_SUITE
Codename: $REPO_CODENAME
Architectures: $REPO_ARCHITECTURES
Components: $REPO_COMPONENTS
Description: $REPO_DESCRIPTION
Date: $(date -R -u)
EOF
    
    # Generate checksums for Packages files
    {
        echo "MD5Sum:"
        find "$REPO_COMPONENTS" -type f -exec md5sum {} \; | sed 's|^| |'
        echo "SHA1:"
        find "$REPO_COMPONENTS" -type f -exec sha1sum {} \; | sed 's|^| |'
        echo "SHA256:"
        find "$REPO_COMPONENTS" -type f -exec sha256sum {} \; | sed 's|^| |'
        echo "SHA512:"
        find "$REPO_COMPONENTS" -type f -exec sha512sum {} \; | sed 's|^| |'
    } >> Release
    
    log_success "Release file generated"
}

sign_release() {
    log_info "Signing Release file..."
    
    cd "$REPO_DIR/dists/$REPO_CODENAME"
    
    # Remove old signatures
    rm -f Release.gpg InRelease
    
    # Create detached signature
    gpg --default-key "$GPG_KEY_ID" \
        --armor \
        --detach-sign \
        --digest-algo SHA256 \
        --sign \
        --output Release.gpg \
        Release
    
    # Create inline signature (InRelease)
    gpg --default-key "$GPG_KEY_ID" \
        --armor \
        --clearsign \
        --digest-algo SHA256 \
        --sign \
        --output InRelease \
        Release
    
    log_success "Release file signed"
}

export_public_key() {
    log_info "Exporting public GPG key..."
    
    # Export ASCII-armored key
    gpg --armor --export "$GPG_KEY_ID" > "$REPO_DIR/KEY.asc"
    
    # Export binary key
    gpg --export "$GPG_KEY_ID" > "$REPO_DIR/KEY.gpg"
    
    log_success "Public key exported to $REPO_DIR/KEY.gpg and KEY.asc"
}

create_index_html() {
    log_info "Creating index.html..."
    
    cat > "$REPO_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ulauncher APT Repository</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1 { color: #5D4EC2; }
        h2 { color: #666; margin-top: 30px; }
        pre {
            background: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            margin: 20px 0;
        }
        a { color: #5D4EC2; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Ulauncher APT Repository</h1>
    <p>Official APT repository for <a href="https://ulauncher.io">Ulauncher</a> - Application launcher for Linux</p>

    <h2>Installation</h2>
    <p>Add the repository to your system:</p>
    <pre><code># Download and add the GPG key
curl -fsSL https://apt.ulauncher.io/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg

# Add the repository
echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | \
  sudo tee /etc/apt/sources.list.d/ulauncher.list

# Update and install
sudo apt update
sudo apt install ulauncher</code></pre>

    <h2>Supported Distributions</h2>
    <ul>
        <li>Ubuntu 24.04 LTS (Noble)</li>
        <li>Ubuntu 22.04 LTS (Jammy)</li>
        <li>Ubuntu 20.04 LTS (Focal)</li>
        <li>Debian 12 (Bookworm)</li>
        <li>Debian 11 (Bullseye)</li>
    </ul>

    <div class="warning">
        <strong>Note:</strong> This repository uses SHA-256 signatures and is compatible with modern APT versions.
    </div>

    <h2>Manual Download</h2>
    <p>You can also download packages directly from <a href="https://github.com/Ulauncher/Ulauncher/releases">GitHub Releases</a>.</p>

    <h2>Migration from Launchpad PPA</h2>
    <p>If you're migrating from the old Launchpad PPA:</p>
    <pre><code># Remove old PPA
sudo add-apt-repository --remove ppa:agornostal/ulauncher

# Follow installation instructions above</code></pre>

    <h2>Links</h2>
    <ul>
        <li><a href="https://ulauncher.io">Official Website</a></li>
        <li><a href="https://github.com/Ulauncher/Ulauncher">GitHub Repository</a></li>
        <li><a href="https://github.com/Ulauncher/Ulauncher/issues">Issue Tracker</a></li>
        <li><a href="https://docs.ulauncher.io">Documentation</a></li>
    </ul>
</body>
</html>
EOF
    
    log_success "index.html created"
}

main() {
    log_info "Starting APT repository publication process..."
    
    # Check dependencies
    check_dependencies
    
    # Check GPG key
    check_gpg_key
    
    # Create repository structure
    create_repo_structure
    
    # Copy packages to pool
    copy_packages_to_pool
    
    # Generate Packages index
    generate_packages_index
    
    # Generate Release file
    generate_release_file
    
    # Sign Release file
    sign_release
    
    # Export public key
    export_public_key
    
    # Create index.html
    create_index_html
    
    # Summary
    echo ""
    log_success "APT repository published successfully!"
    echo ""
    log_info "Repository location: $REPO_DIR"
    log_info "To deploy to GitHub Pages, commit and push the repo/ directory to gh-pages branch"
    echo ""
    log_info "Quick deployment command:"
    echo "  git subtree push --prefix apt/repo origin gh-pages"
    echo ""
}

# Run main function
main "$@"