# START HERE - APT Repository Infrastructure

**Welcome!** This directory contains a complete solution for distributing Ulauncher via APT (Debian/Ubuntu package manager).

---

## 🚀 What Is This?

A modern replacement for the broken Launchpad PPA that:

- ✅ **Fixes the SHA-1 signature problem** (Debian users can install again)
- ✅ **Uses modern SHA-256+ signatures** (future-proof)
- ✅ **Simplifies packaging** (one YAML file instead of complex `debian/` directory)
- ✅ **Supports Ubuntu AND Debian** (not just Ubuntu)
- ✅ **Fully automated** (GitHub Actions builds and publishes)
- ✅ **Self-hosted** (GitHub Pages, free and reliable)

---

## 📖 Which Document Should I Read?

### I want to... → Read this file:

| Goal | Document | Time Needed |
|------|----------|-------------|
| **Understand what we built** | `INDEX.md` | 5 minutes |
| **Build packages right now** | `QUICKSTART.md` | 10 minutes |
| **Move to separate repository** | `MIGRATION.md` | 30-60 minutes |
| **Understand why this is better** | `COMPARISON.md` | 10 minutes |
| **See how everything works** | `WORKFLOW.md` | 10 minutes |
| **Get technical details** | `SUMMARY.md` | 10 minutes |
| **Learn user-facing info** | `README.md` | 5 minutes |

### Quick Decision Tree

```
Are you ready to test this?
│
├─ YES → Go to QUICKSTART.md
│         (Build packages locally in ~10 minutes)
│
└─ NO, I want to understand it first
   │
   ├─ Show me the big picture → INDEX.md
   ├─ Convince me this is better → COMPARISON.md
   ├─ Show me how it works → WORKFLOW.md
   └─ I need all technical details → SUMMARY.md
```

---

## ⚡ Super Quick Start (For the Impatient)

If you just want to build a package right now:

```bash
# 1. Install nfpm (one-time setup)
go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest
# OR download from: https://github.com/goreleaser/nfpm/releases

# 2. Build packages
cd apt/scripts
./build.sh

# 3. Test installation
sudo dpkg -i ../dist/ulauncher_*_noble_all.deb
sudo apt-get install -f
```

**Done!** You now have working `.deb` packages.

For more details, see `QUICKSTART.md`.

---

## 📂 Directory Structure

```
apt/
├── START_HERE.md           ← You are here
├── INDEX.md                ← Executive summary
├── QUICKSTART.md           ← Build packages now
├── COMPARISON.md           ← Old vs new approach
├── MIGRATION.md            ← Move to separate repo
├── WORKFLOW.md             ← Visual workflow diagrams
├── SUMMARY.md              ← Technical deep dive
├── README.md               ← User-facing (for apt.ulauncher.io)
├── nfpm.yaml               ← Package configuration
├── scripts/
│   ├── build.sh           ← Build .deb packages
│   ├── sign.sh            ← Sign packages with GPG
│   └── publish.sh         ← Create APT repository
└── .github/
    └── workflows/
        └── build-and-publish.yml  ← GitHub Actions automation
```

---

## 🎯 The Problem We're Solving

**Before:** Debian/Ubuntu users trying to install Ulauncher got this error:

```
Warning: Policy will reject signature within a year
Audit: SHA1 is not considered secure since 2026-02-01T00:00:00Z
```

**Why:** Launchpad PPA uses deprecated SHA-1 signatures. We can't fix it because Launchpad controls the signing key.

**Solution:** This directory. Self-hosted APT repository with modern signatures.

---

## 🔑 Key Features

### 1. Simple Configuration
**Old way:** 6+ files in `debian/` directory with complex formats
**New way:** One `nfpm.yaml` file with clear, readable YAML

### 2. Fast Builds
**Old way:** Upload to Launchpad, wait hours, hope it works
**New way:** Build locally in seconds, or on GitHub Actions in minutes

### 3. Multi-Distribution
**Old way:** Ubuntu only (Launchpad limitation)
**New way:** Ubuntu 20.04/22.04/24.04 AND Debian 11/12

### 4. Full Control
**Old way:** Black box builds, Launchpad's infrastructure
**New way:** Transparent builds, we control everything

### 5. Modern Security
**Old way:** SHA-1 signatures (deprecated, broken)
**New way:** SHA-256+ signatures (modern, secure)

---

## 🗺️ Recommended Path

### Path 1: Quick Test (Today)
1. Read `QUICKSTART.md`
2. Build packages locally
3. Install and test
4. Decide if you like it

**Time:** 30 minutes

### Path 2: Full Setup (This Week)
1. Read `INDEX.md` (overview)
2. Read `MIGRATION.md` (setup guide)
3. Create separate `ulauncher/apt` repository
4. Configure GitHub Pages and secrets
5. Test automated builds
6. Go live

**Time:** 2-3 hours spread over a few days

### Path 3: Deep Dive (For Contributors)
1. Read all documentation
2. Understand the workflow (`WORKFLOW.md`)
3. Review technical details (`SUMMARY.md`)
4. Test locally
5. Contribute improvements

**Time:** As much as you want

---

## ❓ FAQ

**Q: Can I test this without moving to a separate repo?**
A: Yes! Just run `./scripts/build.sh` from this directory.

**Q: Do I need to remove the debian/ directory from main repo?**
A: Not immediately. Test this first, then remove debian/ when you're ready.

**Q: Will this work with GitHub Pages?**
A: Yes! GitHub Pages is perfect for hosting APT repositories. It's free, fast, and reliable.

**Q: What about the existing Launchpad PPA?**
A: You can keep it running alongside this for a transition period, then deprecate it.

**Q: Do I need a GPG key?**
A: For signing packages, yes. See `QUICKSTART.md` for how to create one.

**Q: Is this production-ready?**
A: The approach is proven and used by many projects. Test it thoroughly before going live.

---

## 📊 Status

- ✅ Package configuration complete
- ✅ Build scripts working
- ✅ Signing scripts ready
- ✅ Publishing scripts ready
- ✅ GitHub Actions workflow configured
- ✅ Documentation complete
- ⏳ **Your turn:** Test locally
- ⏳ **Your turn:** Move to separate repo (optional)
- ⏳ **Your turn:** Set up automation
- ⏳ **Your turn:** Go live

---

## 🎬 Next Step

**→ Go to `INDEX.md` for a 5-minute overview**

**→ Or go to `QUICKSTART.md` to build packages now**

Your choice! Both are good starting points.

---

## 💡 Bottom Line

This directory gives you everything needed to:
1. Fix the SHA-1 signature problem
2. Simplify Ulauncher's packaging
3. Support more distributions
4. Control your own APT repository

**No more Launchpad dependency. No more SHA-1 errors. Just working packages.**

Ready? Pick a document above and dive in! 🚀