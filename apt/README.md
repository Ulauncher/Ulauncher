# Ulauncher APT Repository

This directory contains the infrastructure for building and hosting Ulauncher's APT repository on GitHub Pages.

## Overview

This replaces the legacy Launchpad PPA infrastructure with a modern, self-hosted APT repository that:

- ✅ Uses SHA-256+ signing (no SHA-1 deprecation issues)
- ✅ Supports multiple Ubuntu and Debian versions
- ✅ Hosted on GitHub Pages (free, reliable)
- ✅ Automated builds via GitHub Actions
- ✅ Full control over packaging and distribution

## Architecture

### Build Process

1. **Trigger**: GitHub Actions workflow runs on new releases in main repo
2. **Build**: Uses [nfpm](https://nfpm.goreleaser.com/) to create `.deb` packages from simple YAML config
3. **Sign**: Signs packages with GPG key using SHA-256+
4. **Publish**: Updates APT repository metadata and deploys to GitHub Pages

### Why nfpm?

We use **nfpm** instead of traditional `debian/` directory because:

- **Simpler**: YAML config instead of multiple debian control files
- **No debian/ in main repo**: Packaging stays separate from application code
- **Multi-distro friendly**: Easy to build for different versions
- **Modern**: Actively maintained, designed for CI/CD

## Repository Structure

```
apt/
├── README.md           # This file
├── nfpm.yaml          # Package configuration
├── scripts/
│   ├── build.sh       # Build packages for all distros
│   ├── sign.sh        # Sign packages with GPG
│   └── publish.sh     # Update APT repo and deploy
├── .github/
│   └── workflows/
│       └── build-and-publish.yml  # Main automation workflow
└── repo/              # APT repository structure (generated)
    ├── pool/          # Package files
    ├── dists/         # Distribution metadata
    └── KEY.gpg        # Public signing key
```

## Usage

### For Users

```bash
# Add the repository
curl -fsSL https://apt.ulauncher.io/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg

echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | \
  sudo tee /etc/apt/sources.list.d/ulauncher.list

# Install or update
sudo apt update
sudo apt install ulauncher
```

### For Maintainers

#### Building Locally

```bash
# Install nfpm
go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest
# or download from https://github.com/goreleaser/nfpm/releases

# Build for a specific distro
cd apt/
nfpm package --packager deb --target ./dist/

# Build for all distros
./scripts/build.sh
```

#### Testing Package

```bash
# Install locally built package
sudo dpkg -i dist/ulauncher_*.deb
sudo apt-get install -f  # Fix any missing dependencies
```

#### Publishing (Automated)

Publishing happens automatically when a new release is created in the main repo.

Manual publishing (requires GPG key and write access):
```bash
./scripts/sign.sh      # Sign all packages
./scripts/publish.sh   # Update repo and deploy to GitHub Pages
```

## Configuration

### nfpm.yaml

The main package configuration. Defines:
- Package metadata (name, version, description)
- Dependencies
- Files to include
- Install scripts

### GPG Signing

The repository is signed with a GPG key stored in GitHub Secrets:
- `APT_GPG_PRIVATE_KEY`: Private key for signing
- `APT_GPG_PASSPHRASE`: Passphrase for the private key

## Supported Distributions

- Ubuntu 24.04 LTS (Noble)
- Ubuntu 22.04 LTS (Jammy)
- Ubuntu 20.04 LTS (Focal)
- Debian 12 (Bookworm)
- Debian 11 (Bullseye)

## Migration from Launchpad PPA

Users currently on the Launchpad PPA can migrate:

```bash
# Remove old PPA
sudo add-apt-repository --remove ppa:agornostal/ulauncher

# Add new repository (see "For Users" above)
# ...

# Update and upgrade
sudo apt update
sudo apt upgrade
```

## References

- [nfpm Documentation](https://nfpm.goreleaser.com/)
- [Debian Repository Format](https://wiki.debian.org/DebianRepository/Format)
- [APT Secure](https://wiki.debian.org/SecureApt)