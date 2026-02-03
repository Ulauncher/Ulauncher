# Packaging Approach Comparison

This document compares the old Launchpad PPA approach with the new self-hosted APT repository.

## Overview

| Aspect | Old (Launchpad PPA) | New (GitHub Pages APT) |
|--------|---------------------|------------------------|
| **Hosting** | Launchpad servers | GitHub Pages |
| **Signing** | Launchpad's key (SHA-1) | Our own key (SHA-256+) |
| **Control** | Limited | Full control |
| **Cost** | Free | Free |
| **Maintenance** | Complex | Simple |
| **Speed** | Slow builds | Fast builds |
| **Transparency** | Limited | Full (open source CI) |

## Detailed Comparison

### 1. Security & Compatibility

#### Old Approach ❌
- **SHA-1 signatures** - Deprecated since 2026-02-01
- **No control over signing key** - Launchpad owns the key
- **Users getting errors** - Modern Debian/Ubuntu reject SHA-1
- **No fix available** - Can't update Launchpad's infrastructure

#### New Approach ✅
- **SHA-256+ signatures** - Modern, secure hashing
- **Full control over keys** - We manage our own GPG key
- **Future-proof** - Can update as standards evolve
- **No user errors** - Compatible with all modern systems

### 2. Build Process

#### Old Approach ❌
```bash
# Complex debian/ directory structure needed
debian/
├── changelog
├── compat
├── control
├── copyright
├── rules
└── source/

# Requires:
- debhelper magic variables
- dpkg-buildpackage with complex args
- dput upload to Launchpad
- Wait for Launchpad to build (can take hours)
- Hope nothing breaks in Launchpad's build environment
```

#### New Approach ✅
```bash
# Simple YAML configuration
nfpm.yaml  # Single file with all package metadata

# Requires:
- One binary (nfpm)
- Simple build script
- Fast local builds (seconds, not hours)
- GitHub Actions for automation
- Immediate feedback
```

### 3. Configuration Complexity

#### Old Approach ❌
**debian/control:**
```
Source: ulauncher
Section: python
Priority: extra
Build-Depends: debhelper (>=9~),
 dh-python,
 python3-all,
 python3-setuptools
Maintainer: Aleksandr Gornostal <ulauncher.app@gmail.com>
Standards-Version: 4.1.4
X-Python3-Version: >= 3.8
Homepage: https://ulauncher.io/

Package: ulauncher
Architecture: all
Depends: ${misc:Depends},
 ${python3:Depends},
 libgtk-3-0 (>= 3.22),
 ...
```

**debian/rules:**
```makefile
#!/usr/bin/make -f
%:
	dh $@ --with python3 --buildsystem=pybuild
```

**debian/changelog:**
```
ulauncher (6.0.0-0ubuntu1ppa1~noble) noble; urgency=medium

  * New upstream release

 -- Maintainer <email@example.com>  Mon, 03 Feb 2025 12:00:00 +0000
```

Plus: `debian/compat`, `debian/copyright`, `debian/source/format`, etc.

#### New Approach ✅
**nfpm.yaml:**
```yaml
name: ulauncher
version: ${VERSION}
maintainer: Aleksandr Gornostal <ulauncher.app@gmail.com>
description: Application launcher for Linux
homepage: https://ulauncher.io/

depends:
  - python3 (>= 3.8)
  - libgtk-3-0 (>= 3.22)
  
contents:
  - src: ulauncher/**/*.py
    dst: /usr/lib/python3/dist-packages/ulauncher/
```

**That's it!** One file with clear, readable configuration.

### 4. Multi-Distribution Support

#### Old Approach ❌
```bash
# Build separately for each Ubuntu release
for DISTRO in noble jammy focal; do
    # Modify debian/changelog for each distro
    dch --distribution $DISTRO ...
    # Build source package
    dpkg-buildpackage --build=source ...
    # Upload and wait
    dput ppa:agornostal/ulauncher dist/*.changes
done
```

- Only supports Ubuntu (Launchpad limitation)
- No official Debian support
- Each distro requires separate upload
- Slow sequential builds

#### New Approach ✅
```bash
# One command builds for all distros
./scripts/build.sh

# Supports:
# - Ubuntu (multiple versions)
# - Debian (multiple versions)
# - Any other Debian-based distro
```

- Parallel builds
- Consistent across all distros
- Easy to add new distros (one line in config)

### 5. User Experience

#### Old Approach ❌
```bash
# Users add PPA
sudo add-apt-repository ppa:agornostal/ulauncher
sudo apt update
sudo apt install ulauncher

# But now they get:
# Warning: Policy will reject signature within a year
# Error: SHA1 is not considered secure
```

**Result:** Users can't install or update Ulauncher

#### New Approach ✅
```bash
# Users add our repository
curl -fsSL https://apt.ulauncher.io/KEY.gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg

echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | \
  sudo tee /etc/apt/sources.list.d/ulauncher.list

sudo apt update
sudo apt install ulauncher
```

**Result:** Clean install, no errors, works on all modern systems

### 6. Maintenance & Debugging

#### Old Approach ❌
- **Black box** - Can't see Launchpad's build process
- **Limited logs** - Hard to debug build failures
- **No local testing** - Can't reproduce Launchpad's environment
- **Slow iteration** - Each fix requires re-upload and waiting
- **Dependency on Launchpad** - Service could change or shut down

#### New Approach ✅
- **Transparent** - Full control over build process
- **Complete logs** - GitHub Actions shows everything
- **Local testing** - Build and test packages locally
- **Fast iteration** - Immediate feedback, quick fixes
- **Self-hosted** - No dependency on third-party build service

### 7. Packaging Files Location

#### Old Approach ❌
```
Ulauncher/
├── debian/           # Packaging in main repo
│   ├── changelog
│   ├── control
│   ├── rules
│   └── ...
├── ulauncher/        # Application code
├── tests/
└── ...
```

**Issues:**
- Packaging mixed with application code
- Every app change might need packaging updates
- Confuses contributors ("What's debian/ for?")

#### New Approach ✅
```
ulauncher/            # Main application repo
├── ulauncher/
├── tests/
└── ...

apt/                  # Separate packaging repo
├── nfpm.yaml
├── scripts/
└── .github/
```

**Benefits:**
- Clean separation of concerns
- Packaging maintainers work independently
- Contributors focus on app, not packaging

### 8. Release Process

#### Old Approach ❌
1. Create GitHub release
2. Manually trigger Launchpad upload workflow
3. Wait for Launchpad to build (hours)
4. Check if build succeeded
5. If failed, debug and repeat
6. Hope users don't get SHA-1 errors

#### New Approach ✅
1. Create GitHub release
2. Automation builds packages (minutes)
3. Packages automatically signed and published
4. APT repository automatically updated
5. Users get updates immediately
6. Everything works reliably

### 9. Cost Analysis

#### Old Approach
- **Hosting:** Free (Launchpad)
- **Time cost:** High (complex setup, slow builds)
- **Maintenance:** High (dealing with Launchpad quirks)
- **User support:** High (SHA-1 errors, compatibility issues)

#### New Approach
- **Hosting:** Free (GitHub Pages)
- **Time cost:** Low (simple setup, fast builds)
- **Maintenance:** Low (straightforward scripts)
- **User support:** Low (works everywhere)

## Migration Path

### For Maintainers

1. ✅ Set up new APT repository (this directory)
2. ✅ Test package builds locally
3. ✅ Create separate GitHub repository
4. ✅ Configure GitHub Pages
5. ✅ Set up automated builds
6. ✅ Announce migration to users
7. ❌ Keep Launchpad PPA for legacy users (optional)
8. ✅ Eventually deprecate Launchpad PPA

### For Users

**Old:**
```bash
sudo add-apt-repository --remove ppa:agornostal/ulauncher
```

**New:**
```bash
curl -fsSL https://apt.ulauncher.io/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg
echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | sudo tee /etc/apt/sources.list.d/ulauncher.list
sudo apt update
sudo apt upgrade
```

## Conclusion

The new approach solves the immediate SHA-1 signature problem while providing:

- ✅ Better security (SHA-256+)
- ✅ Simpler configuration (one YAML file)
- ✅ Faster builds (seconds vs hours)
- ✅ Full control (no Launchpad dependency)
- ✅ Better maintainability (clean separation)
- ✅ Wider support (Ubuntu + Debian)
- ✅ Future-proof (we control everything)

**The old approach is broken and can't be fixed. The new approach is better in every way.**