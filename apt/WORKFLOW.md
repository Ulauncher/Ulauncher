# APT Repository Workflow

This document visualizes how the new APT repository system works from release to user installation.

## High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RELEASE PROCESS                              │
└─────────────────────────────────────────────────────────────────────┘

1. Developer creates release in Ulauncher/Ulauncher
   │
   ├─ Tag: v6.0.0
   ├─ Release notes
   └─ Triggers workflow
   
2. Workflow dispatches to APT repository
   │
   └─ Event: repository_dispatch (new-release)

3. APT repository workflow starts
   │
   ├─ Checkout Ulauncher source
   ├─ Checkout APT config
   └─ Set up build environment

4. Build packages for all distros
   │
   ├─ Ubuntu 24.04 (noble)
   ├─ Ubuntu 22.04 (jammy)
   ├─ Ubuntu 20.04 (focal)
   ├─ Debian 12 (bookworm)
   └─ Debian 11 (bullseye)

5. Sign packages with GPG (SHA-256+)
   │
   └─ Using APT_GPG_PRIVATE_KEY secret

6. Create/update APT repository
   │
   ├─ pool/ (packages)
   ├─ dists/ (metadata)
   └─ Sign Release file

7. Deploy to GitHub Pages
   │
   └─ Available at https://apt.ulauncher.io

8. Users update
   │
   └─ sudo apt update && sudo apt upgrade
```

## Detailed Build Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BUILD PACKAGE WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────┘

Input: Ulauncher source code at specific version
       ↓
┌──────────────────────────┐
│  scripts/build.sh        │
│                          │
│  1. Get version from     │
│     ulauncher.version    │
│                          │
│  2. Prepare build dir    │
│     - Copy source files  │
│     - Gzip manpage       │
│     - Clean artifacts    │
│                          │
│  3. For each distro:     │
│     ┌────────────────┐   │
│     │ nfpm package   │   │
│     │                │   │
│     │ Input:         │   │
│     │ - nfpm.yaml    │   │
│     │ - source files │   │
│     │                │   │
│     │ Output:        │   │
│     │ - .deb file    │   │
│     └────────────────┘   │
│                          │
└──────────────────────────┘
       ↓
Output: dist/*.deb files
```

## Repository Structure After Publishing

```
apt.ulauncher.io/
│
├── index.html                  # User-facing instructions
├── KEY.gpg                     # Public GPG key (binary)
├── KEY.asc                     # Public GPG key (ASCII)
│
├── pool/                       # All package files
│   ├── ulauncher_6.0.0~noble_all.deb
│   ├── ulauncher_6.0.0~jammy_all.deb
│   ├── ulauncher_6.0.0~focal_all.deb
│   ├── ulauncher_6.0.0~bookworm_all.deb
│   └── ulauncher_6.0.0~bullseye_all.deb
│
└── dists/
    └── ulauncher/              # Repository codename
        ├── Release             # Metadata with checksums
        ├── Release.gpg         # Detached GPG signature
        ├── InRelease           # Inline GPG signature
        └── main/
            └── binary-all/
                ├── Packages    # Package index
                └── Packages.gz # Compressed index
```

## User Installation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER INSTALLATION FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

User runs installation command
       ↓
1. Download GPG key
   curl https://apt.ulauncher.io/KEY.gpg
       ↓
2. Add to trusted keyrings
   /usr/share/keyrings/ulauncher.gpg
       ↓
3. Add repository to sources
   /etc/apt/sources.list.d/ulauncher.list
       ↓
4. APT update
   apt update
       │
       ├─ Downloads: dists/ulauncher/InRelease
       ├─ Verifies: GPG signature (SHA-256+)
       ├─ Downloads: dists/ulauncher/main/binary-all/Packages.gz
       └─ Updates: package cache
       ↓
5. APT install
   apt install ulauncher
       │
       ├─ Resolves: dependencies
       ├─ Downloads: pool/ulauncher_6.0.0~noble_all.deb
       ├─ Verifies: package signature
       └─ Installs: to system
       ↓
✅ Ulauncher installed and ready to use
```

## GitHub Actions Workflow Details

```
┌─────────────────────────────────────────────────────────────────────┐
│              GITHUB ACTIONS WORKFLOW STEPS                           │
└─────────────────────────────────────────────────────────────────────┘

Trigger: repository_dispatch, workflow_dispatch, or push
│
├─ Job 1: Build Packages
│  │
│  ├─ Step 1: Checkout repositories
│  │  ├─ Ulauncher/Ulauncher (source)
│  │  └─ Ulauncher/apt (config)
│  │
│  ├─ Step 2: Set up environment
│  │  ├─ Python 3.8+
│  │  ├─ nfpm binary
│  │  └─ Build tools (dpkg-dev, etc.)
│  │
│  ├─ Step 3: Get version
│  │  └─ python3 -c "import ulauncher; print(ulauncher.version)"
│  │
│  ├─ Step 4: Build packages
│  │  └─ ./scripts/build.sh
│  │
│  ├─ Step 5: Upload artifacts
│  │  └─ GitHub Actions artifacts (90 days)
│  │
│  └─ Step 6: Attach to release (optional)
│     └─ Add .deb files to GitHub release
│
└─ Job 2: Sign and Publish
   │
   ├─ Step 1: Download artifacts
   │  └─ Built .deb files from Job 1
   │
   ├─ Step 2: Import GPG key
   │  └─ From APT_GPG_PRIVATE_KEY secret
   │
   ├─ Step 3: Sign packages
   │  └─ ./scripts/sign.sh
   │
   ├─ Step 4: Publish repository
   │  └─ ./scripts/publish.sh
   │
   ├─ Step 5: Upload to Pages
   │  └─ apt/repo/ directory
   │
   └─ Step 6: Deploy to Pages
      └─ https://apt.ulauncher.io goes live
```

## Signing Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GPG SIGNING FLOW                                │
└─────────────────────────────────────────────────────────────────────┘

Package Signing (dpkg-sig):
│
├─ For each .deb file:
│  │
│  ├─ Read package metadata
│  ├─ Create signature with GPG key
│  │  └─ Algorithm: SHA-256
│  └─ Embed signature in .deb
│
Repository Signing (gpg):
│
├─ Create Release file
│  ├─ Package checksums (MD5, SHA1, SHA256, SHA512)
│  └─ Repository metadata
│
├─ Sign Release file
│  ├─ Detached signature → Release.gpg
│  └─ Inline signature → InRelease
│
└─ Export public key
   ├─ Binary format → KEY.gpg
   └─ ASCII format → KEY.asc
```

## Version Flow Example

```
┌─────────────────────────────────────────────────────────────────────┐
│                   VERSION HANDLING EXAMPLE                           │
└─────────────────────────────────────────────────────────────────────┘

Ulauncher version: 6.0.0
│
├─ Stable release
│  └─ Version string: "6.0.0"
│
├─ Pre-release (e.g., beta)
│  └─ Version string: "6.0.0-beta1"
│     └─ Converted to: "6.0.0~beta1" (Debian convention)
│
└─ Per-distro versions:
   ├─ Ubuntu 24.04: "6.0.0~noble"
   ├─ Ubuntu 22.04: "6.0.0~jammy"
   ├─ Ubuntu 20.04: "6.0.0~focal"
   ├─ Debian 12:    "6.0.0~bookworm"
   └─ Debian 11:    "6.0.0~bullseye"

Tilde (~) ensures:
- Pre-releases sort before stable (6.0.0~beta1 < 6.0.0)
- Distro-specific versions sort correctly
```

## Cross-Repository Communication

```
┌─────────────────────────────────────────────────────────────────────┐
│              REPOSITORY DISPATCH WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────┘

Ulauncher/Ulauncher (.github/workflows/publish-release.yml)
│
├─ On: release published
│
└─ Job: Trigger APT build
   │
   └─ Action: repository_dispatch
      │
      ├─ Target: Ulauncher/apt
      ├─ Event type: new-release
      └─ Payload:
         ├─ version: "6.0.0"
         └─ release_url: "https://github.com/..."
         
         ↓

Ulauncher/apt (.github/workflows/build-and-publish.yml)
│
├─ On: repository_dispatch (type: new-release)
│
└─ Job: Build and publish
   └─ Uses payload data for build
```

## Local Development Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│              LOCAL DEVELOPMENT WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────┘

Developer working on packaging:
│
├─ 1. Edit nfpm.yaml
│     (Change dependencies, files, etc.)
│
├─ 2. Build packages locally
│     ./scripts/build.sh
│     ↓
│     Output: apt/dist/*.deb
│
├─ 3. Test installation
│     sudo dpkg -i apt/dist/ulauncher_*_noble_all.deb
│     sudo apt-get install -f
│
├─ 4. Test functionality
│     ulauncher --version
│     ulauncher
│
├─ 5. Iterate if needed
│     (Repeat steps 1-4)
│
└─ 6. Commit and push
      ↓
      GitHub Actions runs automatically
```

## Comparison: Old vs New Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OLD (LAUNCHPAD) WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘

Release → Upload source to Launchpad → Wait (hours) → 
Build on Launchpad servers → Sign with Launchpad key (SHA-1) → 
Publish to PPA → Users get warnings/errors

Problems:
❌ Can't test locally
❌ Black box build process
❌ SHA-1 signatures (deprecated)
❌ Slow builds
❌ No Debian support


┌─────────────────────────────────────────────────────────────────────┐
│                    NEW (GITHUB PAGES) WORKFLOW                       │
└─────────────────────────────────────────────────────────────────────┘

Release → GitHub Actions builds → Sign with our key (SHA-256+) → 
Publish to GitHub Pages → Users install without issues

Benefits:
✅ Test locally first
✅ Transparent build process
✅ SHA-256+ signatures (modern)
✅ Fast builds (minutes)
✅ Ubuntu + Debian support
```

## Summary

This workflow provides:

1. **Automated builds** - Triggered by releases
2. **Multi-distro support** - One workflow builds for all
3. **Secure signing** - SHA-256+ instead of SHA-1
4. **Fast deployment** - Minutes instead of hours
5. **Full control** - We own the entire process
6. **Transparent** - Everything visible in GitHub Actions
7. **Testable** - Can build and test locally

The end result: Users can install Ulauncher reliably on any modern Debian or Ubuntu system without signature warnings.