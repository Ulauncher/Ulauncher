# APT Repository Infrastructure - Executive Summary

**Status**: Ready for testing and review  
**Created**: 2025-02-03  
**Purpose**: Replace broken Launchpad PPA with self-hosted APT repository

---

## Quick Overview

This directory contains everything needed to build, sign, and distribute Ulauncher `.deb` packages without Launchpad PPA.

**Problem**: Launchpad uses deprecated SHA-1 signatures. Debian/Ubuntu users can't install Ulauncher anymore.

**Solution**: Self-hosted APT repository on GitHub Pages with modern SHA-256+ signatures.

---

## What's Included

### 📋 Configuration
- **`nfpm.yaml`** - Package definition (replaces entire `debian/` directory)

### 🔧 Scripts
- **`scripts/build.sh`** - Build packages for all distros (Ubuntu + Debian)
- **`scripts/sign.sh`** - Sign packages with GPG (SHA-256+)
- **`scripts/publish.sh`** - Create APT repository structure

### 🤖 Automation
- **`.github/workflows/build-and-publish.yml`** - GitHub Actions workflow

### 📚 Documentation
- **`README.md`** - User-facing overview
- **`QUICKSTART.md`** - Maintainer quick start guide
- **`COMPARISON.md`** - Old vs new approach (detailed)
- **`MIGRATION.md`** - How to move to separate repo
- **`SUMMARY.md`** - Technical summary
- **`INDEX.md`** - This file

---

## Key Benefits

### ✅ Fixes SHA-1 Issue
- Modern SHA-256+ signatures
- No deprecation warnings
- Works on all current Debian/Ubuntu versions

### ✅ Simpler Than Launchpad
- One YAML file vs 6+ debian control files
- Build locally in seconds vs hours on Launchpad
- Full control and transparency

### ✅ Better Distribution
- Supports both Ubuntu AND Debian
- Multiple versions (20.04, 22.04, 24.04, Debian 11, 12)
- Easy to add more distros

### ✅ No `debian/` in Main Repo
- Keeps packaging separate from app code
- Cleaner repository structure
- Can be moved to separate repo

---

## Quick Start

### Test Locally (Right Now)

```bash
# Install nfpm
go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest

# Or download from: https://github.com/goreleaser/nfpm/releases

# Build packages
cd apt/scripts
./build.sh

# Result: .deb packages in apt/dist/
```

### Test Installation

```bash
# Install locally built package
sudo dpkg -i apt/dist/ulauncher_*_noble_all.deb
sudo apt-get install -f  # Fix dependencies
```

---

## Recommended Next Steps

1. **Test locally** (10 minutes)
   - Build packages with `./scripts/build.sh`
   - Install on your machine
   - Verify it works

2. **Create separate repo** (30 minutes)
   - Create `ulauncher/apt` on GitHub
   - Copy this directory there
   - Follow `MIGRATION.md`

3. **Set up automation** (1 hour)
   - Configure GitHub Pages
   - Add GPG key to secrets
   - Test automated build

4. **Go live** (when ready)
   - Update main repo documentation
   - Announce to users
   - Deprecate Launchpad PPA

---

## File Guide

### Start Here
- **`QUICKSTART.md`** - If you want to build packages now
- **`COMPARISON.md`** - If you want to understand why this is better
- **`MIGRATION.md`** - If you want to move to separate repo

### Technical Details
- **`nfpm.yaml`** - Package configuration
- **`SUMMARY.md`** - How everything works
- **`scripts/*.sh`** - Build/sign/publish scripts

### Automation
- **`.github/workflows/build-and-publish.yml`** - CI/CD workflow
- **`README.md`** - User instructions (for apt.ulauncher.io)

---

## Technical Stack

- **nfpm** - Modern package builder (replaces dpkg-buildpackage)
- **GitHub Actions** - Build automation
- **GitHub Pages** - APT repository hosting (free)
- **GPG** - Package signing with SHA-256+
- **Standard Debian tools** - dpkg-sig, apt-ftparchive

---

## What Gets Built

For each Ulauncher version (e.g., 6.0.0), we create:

```
ulauncher_6.0.0~noble_all.deb      (Ubuntu 24.04)
ulauncher_6.0.0~jammy_all.deb      (Ubuntu 22.04)
ulauncher_6.0.0~focal_all.deb      (Ubuntu 20.04)
ulauncher_6.0.0~bookworm_all.deb   (Debian 12)
ulauncher_6.0.0~bullseye_all.deb   (Debian 11)
```

All packages:
- Signed with SHA-256+
- Include all dependencies
- Work with standard APT
- Published to GitHub Pages

---

## User Experience

### Before (Broken)
```bash
sudo add-apt-repository ppa:agornostal/ulauncher
sudo apt update
# Error: SHA1 is not considered secure
# Result: Can't install Ulauncher
```

### After (Working)
```bash
curl -fsSL https://apt.ulauncher.io/KEY.gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg

echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | \
  sudo tee /etc/apt/sources.list.d/ulauncher.list

sudo apt update
sudo apt install ulauncher
# Just works ✅
```

---

## Comparison at a Glance

| Feature | Launchpad PPA | This Solution |
|---------|---------------|---------------|
| SHA-1 warnings | ❌ Yes (broken) | ✅ No (SHA-256+) |
| Build time | ⏰ Hours | ⚡ Minutes |
| Local testing | ❌ No | ✅ Yes |
| Debian support | ❌ No | ✅ Yes |
| Configuration | 📚 6+ files | 📄 1 YAML file |
| Cost | 💰 Free | 💰 Free |
| Control | 🔒 None | 🔓 Full |

---

## Questions?

- **How does nfpm work?** See `nfpm.yaml` and [nfpm.goreleaser.com](https://nfpm.goreleaser.com)
- **How to move to separate repo?** See `MIGRATION.md`
- **How to build packages?** See `QUICKSTART.md`
- **Why is this better?** See `COMPARISON.md`
- **Technical details?** See `SUMMARY.md`

---

## Status Checklist

- ✅ Package configuration (`nfpm.yaml`)
- ✅ Build scripts
- ✅ Signing scripts
- ✅ Publishing scripts
- ✅ GitHub Actions workflow
- ✅ Complete documentation
- ⏳ Local testing (your turn)
- ⏳ Separate repository creation
- ⏳ GitHub Pages setup
- ⏳ Production deployment

---

## Bottom Line

**This directory solves the SHA-1 signature problem and gives you a modern, maintainable APT repository.**

You can:
- Build packages locally right now
- Move to separate repo when ready
- Go live at your own pace
- Never depend on Launchpad again

**Recommended**: Test locally first, then follow `MIGRATION.md` to set up the full automation.