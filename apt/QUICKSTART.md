# Quick Start Guide

This guide helps you get started with the new APT packaging system for Ulauncher.

## Prerequisites

### For Local Development

```bash
# Install nfpm (package builder)
# Option 1: Using Go
go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest

# Option 2: Download binary
curl -sfL https://goreleaser.com/install.sh | sh -s -- -b /usr/local/bin nfpm

# Install Debian packaging tools
sudo apt-get install -y dpkg-dev dpkg-sig apt-utils gnupg gzip rsync
```

### For GitHub Actions (Automated)

You'll need to set up these GitHub Secrets in the **apt repository** (once you move this directory to its own repo):

- `APT_GPG_PRIVATE_KEY`: Your GPG private key (base64 encoded)
- `APT_GPG_PASSPHRASE`: Passphrase for the GPG key

## Building Packages Locally

### 1. Build all packages

```bash
cd apt/scripts
./build.sh
```

This will create `.deb` packages for all supported distributions in `apt/dist/`:
- `ulauncher_X.Y.Z~noble_all.deb` (Ubuntu 24.04)
- `ulauncher_X.Y.Z~jammy_all.deb` (Ubuntu 22.04)
- `ulauncher_X.Y.Z~focal_all.deb` (Ubuntu 20.04)
- `ulauncher_X.Y.Z~bookworm_all.deb` (Debian 12)
- `ulauncher_X.Y.Z~bullseye_all.deb` (Debian 11)

### 2. Test a package locally

```bash
# Install the package
sudo dpkg -i apt/dist/ulauncher_*_noble_all.deb

# Fix any missing dependencies
sudo apt-get install -f

# Run Ulauncher
ulauncher
```

### 3. Sign packages (optional for local testing)

```bash
# Set your GPG key ID
export GPG_KEY_ID="your-key-id"

# Sign all packages
cd apt/scripts
./sign.sh
```

### 4. Publish to local APT repository

```bash
# Set your GPG key ID
export GPG_KEY_ID="your-key-id"

# Create/update the APT repository
cd apt/scripts
./publish.sh
```

This creates the APT repository in `apt/repo/` with:
- `pool/` - Package files
- `dists/` - Repository metadata
- `KEY.gpg` - Public signing key
- `index.html` - User-facing instructions

## Creating a GPG Key for Signing

If you don't have a GPG key yet:

```bash
# Generate a new key
gpg --full-generate-key

# Choose:
# - RSA and RSA
# - 4096 bits
# - Key does not expire (or set expiration)
# - Real name: Ulauncher
# - Email: ulauncher.app@gmail.com

# List your keys to find the ID
gpg --list-secret-keys --keyid-format LONG

# Export for GitHub Secrets (base64 encoded)
gpg --armor --export-secret-keys YOUR_KEY_ID | base64 -w0
```

## GitHub Actions Workflow

Once you move the `apt/` directory to a separate repository (e.g., `ulauncher/apt`):

### 1. Set up GitHub Pages

In the repository settings:
- Go to Settings → Pages
- Source: GitHub Actions
- Configure custom domain (optional): `apt.ulauncher.io`

### 2. Add GitHub Secrets

In Settings → Secrets and variables → Actions:
- `APT_GPG_PRIVATE_KEY`: Your base64-encoded private key
- `APT_GPG_PASSPHRASE`: Your key passphrase

### 3. Trigger builds

The workflow can be triggered by:

**Automatic (when configured):**
- New releases in the main Ulauncher repository

**Manual:**
- Go to Actions → Build and Publish APT Repository → Run workflow

## Modifying Package Configuration

### Add/Remove Files

Edit `apt/nfpm.yaml` and modify the `contents` section:

```yaml
contents:
  - src: path/to/source/file
    dst: /usr/share/destination/path
    type: file
    file_info:
      mode: 0644
```

### Change Dependencies

Edit the `depends`, `recommends`, or `suggests` sections in `apt/nfpm.yaml`.

### Add New Distribution

Edit `apt/scripts/build.sh` and add to the `DISTROS` array:

```bash
DISTROS=(
    "ubuntu:noble:24.04"
    "ubuntu:jammy:22.04"
    "debian:bookworm:12"
    "debian:trixie:13"  # New distribution
)
```

## Testing the APT Repository

### Serve locally

```bash
cd apt/repo
python3 -m http.server 8000
```

Then on the same machine:

```bash
# Add the local repository
echo "deb [trusted=yes] http://localhost:8000 /" | \
  sudo tee /etc/apt/sources.list.d/ulauncher-local.list

# Update and install
sudo apt update
sudo apt install ulauncher
```

### Test with Docker

```bash
# Ubuntu 24.04
docker run -it --rm ubuntu:24.04 bash

# Inside container:
apt update
apt install -y curl gnupg
curl -fsSL https://apt.ulauncher.io/KEY.gpg | gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg
echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" > /etc/apt/sources.list.d/ulauncher.list
apt update
apt install ulauncher
```

## Troubleshooting

### "nfpm: command not found"

Make sure nfpm is installed and in your PATH:

```bash
which nfpm
# or
go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest
```

### "GPG key not found"

Make sure you've set the `GPG_KEY_ID` environment variable:

```bash
export GPG_KEY_ID=$(gpg --list-secret-keys --keyid-format LONG | grep sec | awk '{print $2}' | cut -d'/' -f2 | head -n1)
```

### "Could not determine Ulauncher version"

Make sure you're running build.sh from a properly set up Ulauncher source tree with the `ulauncher` Python module available.

### Package build fails

Check that all source files exist:
- `ulauncher/**/*.py` - Python package
- `bin/ulauncher` - Main executable
- `bin/ulauncher-toggle` - Toggle script
- `data/` - Application data
- `ulauncher.1` - Man page (will be gzipped automatically)

## Next Steps

1. **Test locally** - Build and install packages on your development machine
2. **Move to separate repo** - Create `ulauncher/apt` repository and move this directory
3. **Set up GitHub Pages** - Configure Pages and secrets
4. **Update documentation** - Update main Ulauncher README with new installation instructions
5. **Announce migration** - Inform users about the switch from Launchpad PPA

## Resources

- [nfpm Documentation](https://nfpm.goreleaser.com/)
- [Debian Repository Format](https://wiki.debian.org/DebianRepository/Format)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GPG Documentation](https://gnupg.org/documentation/)