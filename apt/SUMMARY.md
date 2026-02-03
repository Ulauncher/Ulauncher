# APT Repository Infrastructure - Summary

This directory contains a complete, modern APT repository infrastructure for distributing Ulauncher packages to Debian and Ubuntu users.

## What We've Built

### 📦 Package Builder
- **Tool**: [nfpm](https://nfpm.goreleaser.com/) - Modern, YAML-based package builder
- **Configuration**: `nfpm.yaml` - Single file replacing the entire `debian/` directory
- **Benefits**: Simpler, faster, easier to maintain than traditional Debian packaging

### 🔧 Build Scripts
Three automated scripts in `scripts/`:

1. **build.sh** - Builds `.deb` packages for all supported distributions
   - Ubuntu 24.04 LTS (Noble)
   - Ubuntu 22.04 LTS (Jammy)
   - Ubuntu 20.04 LTS (Focal)
   - Debian 12 (Bookworm)
   - Debian 11 (Bullseye)

2. **sign.sh** - Signs packages with GPG using SHA-256+ (not deprecated SHA-1)

3. **publish.sh** - Creates APT repository structure and metadata for hosting

### 🤖 GitHub Actions Automation
- **Workflow**: `.github/workflows/build-and-publish.yml`
- **Triggers**: 
  - New releases in main repository (via repository_dispatch)
  - Manual workflow runs
  - Changes to apt/ directory
- **Actions**:
  - Builds packages for all distros
  - Signs with GPG key from GitHub Secrets
  - Publishes to GitHub Pages
  - Optionally attaches .deb files to main repo releases

### 📚 Documentation

- **README.md** - Overview and user-facing instructions
- **QUICKSTART.md** - Step-by-step guide for maintainers
- **COMPARISON.md** - Detailed comparison with old Launchpad PPA approach
- **MIGRATION.md** - Complete guide for moving to separate repository
- **SUMMARY.md** - This file

## Problem Solved

### The Issue
Debian users were getting this error:

```
Warning: Policy will reject signature within a year
Audit: SHA1 is not considered secure since 2026-02-01T00:00:00Z
```

Launchpad PPA uses SHA-1 signatures which are now deprecated. Launchpad controls the signing key, so we can't fix it.

### The Solution
Self-hosted APT repository with:
- ✅ SHA-256+ signatures (modern and secure)
- ✅ Our own GPG key (full control)
- ✅ GitHub Pages hosting (free, reliable)
- ✅ Automated builds (fast and transparent)
- ✅ Support for both Ubuntu and Debian

## How It Works

### For Users

```bash
# One-time setup
curl -fsSL https://apt.ulauncher.io/KEY.gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg

echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | \
  sudo tee /etc/apt/sources.list.d/ulauncher.list

# Install/update
sudo apt update
sudo apt install ulauncher
```

### For Maintainers

1. **Create release** in main Ulauncher repository
2. **Automation kicks in**:
   - Checkout source code
   - Build .deb packages (one per distro)
   - Sign with GPG
   - Update APT repository metadata
   - Deploy to GitHub Pages
3. **Users get updates** via normal `apt update && apt upgrade`

## File Structure

```
apt/
├── README.md                    # User documentation
├── QUICKSTART.md               # Maintainer guide
├── COMPARISON.md               # Old vs new approach
├── MIGRATION.md                # Moving to separate repo
├── SUMMARY.md                  # This file
├── nfpm.yaml                   # Package configuration
├── .gitignore                  # Ignore build artifacts
├── scripts/
│   ├── build.sh               # Build packages
│   ├── sign.sh                # Sign packages
│   └── publish.sh             # Publish repository
└── .github/
    └── workflows/
        └── build-and-publish.yml  # GitHub Actions automation
```

Generated during build (ignored by git):
```
apt/
├── build/                      # Temporary build directory
├── dist/                       # Built .deb packages
└── repo/                       # Published APT repository
    ├── pool/                   # Package files
    ├── dists/                  # Distribution metadata
    ├── KEY.gpg                 # Public signing key
    └── index.html              # User instructions
```

## Key Features

### 1. No `debian/` Directory Needed
Instead of maintaining multiple files:
- ❌ `debian/control`
- ❌ `debian/rules`
- ❌ `debian/changelog`
- ❌ `debian/compat`
- ❌ `debian/copyright`
- ❌ `debian/source/format`

We have one simple YAML file:
- ✅ `nfpm.yaml`

### 2. Multi-Distro Support
One build command creates packages for:
- All Ubuntu LTS versions (20.04, 22.04, 24.04)
- All current Debian versions (11, 12)
- Easy to add more (one line in `scripts/build.sh`)

### 3. Fast Builds
- **Old**: Upload to Launchpad, wait hours for build, hope it works
- **New**: Build locally in seconds, or on GitHub Actions in minutes

### 4. Full Control
- Own GPG key (can update hash algorithm)
- Own build process (can debug locally)
- Own hosting (GitHub Pages, 99.9% uptime)
- Own timeline (no waiting for Launchpad)

### 5. Better Security
- SHA-256+ signatures (vs deprecated SHA-1)
- Modern APT repository format
- Transparent build process (open source CI)

## Next Steps

### Immediate (In Main Repo)
- ✅ Test package builds locally
- ✅ Verify packages install correctly
- ✅ Test scripts work end-to-end

### Short Term (Move to Separate Repo)
1. Create `ulauncher/apt` repository
2. Copy this directory there
3. Set up GitHub Pages
4. Configure GitHub Secrets (GPG key)
5. Test automated builds
6. Update main repo's release workflow

### Long Term (Production)
1. Announce migration to users
2. Update documentation
3. Monitor for issues
4. Deprecate Launchpad PPA
5. Celebrate working APT repository! 🎉

## Requirements

### For Local Development
- `nfpm` - Package builder
- `dpkg-dev` - Debian package tools
- `dpkg-sig` - Package signing
- `apt-utils` - Repository tools
- `gnupg` - GPG signing
- Standard tools: `gzip`, `rsync`, `bash`

### For GitHub Actions
- GitHub Secrets:
  - `APT_GPG_PRIVATE_KEY` - Base64-encoded private key
  - `APT_GPG_PASSPHRASE` - GPG key passphrase
- GitHub Pages enabled
- Repository permissions configured

### For Users
- Modern APT (supports SHA-256)
- Debian 11+ or Ubuntu 20.04+
- Internet connection

## Technical Details

### Package Versioning
Format: `X.Y.Z~distro`

Examples:
- `6.0.0~noble` - Ubuntu 24.04
- `6.0.0~jammy` - Ubuntu 22.04
- `6.0.0~bookworm` - Debian 12

The tilde (`~`) ensures proper version sorting in APT.

### Repository Structure
Standard Debian repository format:
```
repo/
├── pool/                           # All package files
│   └── ulauncher_*.deb
├── dists/
│   └── ulauncher/                 # Codename
│       ├── Release                # Signed metadata
│       ├── Release.gpg            # Detached signature
│       ├── InRelease              # Inline signature
│       └── main/
│           └── binary-all/
│               ├── Packages       # Package index
│               └── Packages.gz
└── KEY.gpg                        # Public signing key
```

### Signing
- **Algorithm**: SHA-256 or stronger
- **Key Type**: RSA 4096-bit
- **Signatures**: Both detached (`Release.gpg`) and inline (`InRelease`)
- **Package Signing**: Using `dpkg-sig` with builder role

## Benefits Summary

| Aspect | Old (Launchpad) | New (This) |
|--------|----------------|------------|
| **Signing** | SHA-1 (broken) | SHA-256+ (secure) |
| **Build Time** | Hours | Minutes |
| **Control** | None | Full |
| **Debugging** | Black box | Transparent |
| **Distros** | Ubuntu only | Ubuntu + Debian |
| **Cost** | Free | Free |
| **Reliability** | Dependent | Self-hosted |
| **Configuration** | Complex `debian/` | Simple YAML |

## Support

- **Issues**: Open in the APT repository
- **Questions**: GitHub Discussions
- **Documentation**: See `README.md`, `QUICKSTART.md`, `MIGRATION.md`

## License

Same as main Ulauncher project (GPL-3.0)

## Credits

Built to solve the SHA-1 deprecation issue affecting Debian users.

Replaces the legacy Launchpad PPA infrastructure with a modern, maintainable, self-hosted solution.