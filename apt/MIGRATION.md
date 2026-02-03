# Migration Guide: Moving APT Repository to Separate Repo

This guide walks you through moving the `apt/` directory from the main Ulauncher repository to a separate `ulauncher/apt` repository.

## Why Migrate?

- **Separation of Concerns**: Keep packaging separate from application code
- **Independent Releases**: Update packaging without releasing new app versions
- **Cleaner Main Repo**: Remove build artifacts and packaging complexity
- **Focused Workflows**: Different CI/CD pipelines for app vs. packaging

## Prerequisites

- Admin access to `Ulauncher` GitHub organization
- Git installed locally
- GPG key for signing packages (see QUICKSTART.md)

## Step 1: Create New Repository

### On GitHub

1. Go to https://github.com/organizations/Ulauncher/repositories/new
2. Configure:
   - **Repository name:** `apt`
   - **Description:** "APT repository for Ulauncher packages"
   - **Visibility:** Public
   - **Initialize:** Don't initialize (we'll push existing code)

### Locally

```bash
# Clone the new empty repository
git clone git@github.com:Ulauncher/apt.git ulauncher-apt
cd ulauncher-apt

# Copy apt directory contents from main repo
cp -r /path/to/Ulauncher/apt/* .
cp /path/to/Ulauncher/apt/.gitignore .

# Initial commit
git add .
git commit -m "Initial commit: APT repository infrastructure

- nfpm-based package building
- Multi-distro support (Ubuntu + Debian)
- GitHub Actions automation
- SHA-256 GPG signing
"

# Push to GitHub
git push -u origin main
```

## Step 2: Configure GitHub Pages

### Enable Pages

1. Go to repository Settings → Pages
2. Configure:
   - **Source:** GitHub Actions
   - **Branch:** (will be set by Actions)

### Custom Domain (Optional)

If you want `apt.ulauncher.io` instead of `ulauncher.github.io/apt`:

1. In Settings → Pages → Custom domain
2. Enter: `apt.ulauncher.io`
3. Save

4. Add DNS records at your domain provider:
   ```
   Type: CNAME
   Name: apt
   Value: ulauncher.github.io
   ```

5. Wait for DNS propagation (can take minutes to hours)
6. Enable "Enforce HTTPS" once DNS is verified

## Step 3: Set Up GitHub Secrets

### Generate GPG Key (if you don't have one)

```bash
# Generate key
gpg --full-generate-key
# Choose RSA and RSA, 4096 bits, appropriate expiration
# Name: Ulauncher APT Repository
# Email: ulauncher.app@gmail.com

# Get key ID
gpg --list-secret-keys --keyid-format LONG

# Export for GitHub (base64 encoded)
gpg --armor --export-secret-keys YOUR_KEY_ID | base64 -w0 > gpg-key.txt
```

### Add Secrets to GitHub

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these secrets:

   **APT_GPG_PRIVATE_KEY:**
   - Paste content from `gpg-key.txt`

   **APT_GPG_PASSPHRASE:**
   - Enter your GPG key passphrase

4. Delete local `gpg-key.txt` securely:
   ```bash
   shred -u gpg-key.txt
   ```

## Step 4: Configure Cross-Repository Workflow

To automatically build packages when main repo has a new release:

### Option A: Repository Dispatch (Recommended)

In the **main Ulauncher repository**, update `.github/workflows/publish-release.yml`:

```yaml
name: Publish release

on:
  release:
    types: [published]

jobs:
  trigger-apt-build:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger APT repository build
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.APT_REPO_TOKEN }}
          repository: Ulauncher/apt
          event-type: new-release
          client-payload: |
            {
              "version": "${{ github.ref_name }}",
              "release_url": "${{ github.event.release.html_url }}"
            }
```

Then create a Personal Access Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Add as secret `APT_REPO_TOKEN` in main Ulauncher repository

### Option B: Webhook (Alternative)

Set up a webhook in main repository to notify APT repository on releases.

## Step 5: Update Main Repository

### Remove debian/ directory

```bash
cd /path/to/Ulauncher
git rm -r debian/
git commit -m "Remove debian/ directory (moved to apt repository)"
```

### Update README.md

Replace installation instructions:

```markdown
## Installation

### Debian/Ubuntu

```bash
# Add repository
curl -fsSL https://apt.ulauncher.io/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg
echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | sudo tee /etc/apt/sources.list.d/ulauncher.list

# Install
sudo apt update
sudo apt install ulauncher
```

For other installation methods, see [documentation](https://docs.ulauncher.io).
\```
```

### Update publish-release.yml

Remove Launchpad PPA upload section:

```yaml
# Delete this entire job or section:
- name: Publish to Launchpad
  env:
    LAUNCHPAD_SSH_TAR: ${{ secrets.LAUNCHPAD_SSH_TAR }}
    # ... etc
```

Add APT repository trigger (see Step 4).

## Step 6: Test the Setup

### Manual Workflow Test

1. Go to APT repository → Actions
2. Click "Build and Publish APT Repository"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

Monitor the workflow execution. It should:
- ✅ Checkout repositories
- ✅ Build .deb packages for all distros
- ✅ Sign packages with GPG
- ✅ Publish to repository
- ✅ Deploy to GitHub Pages

### Test Installation

Once workflow completes:

```bash
# On a clean Ubuntu/Debian VM or container
docker run -it --rm ubuntu:24.04 bash

# Inside container:
apt update
apt install -y curl gnupg

# Add repository
curl -fsSL https://apt.ulauncher.io/KEY.gpg | gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg
echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" > /etc/apt/sources.list.d/ulauncher.list

# Install
apt update
apt install ulauncher

# Verify
ulauncher --version
```

### Test Automatic Build

Create a test release in main repository and verify APT repository builds automatically.

## Step 7: Announce Migration

### Create Announcement

Post in:
- GitHub Discussions
- Reddit (r/linux, r/ulauncher if exists)
- Twitter/Mastodon
- Documentation site

**Example announcement:**

```markdown
# New APT Repository Available

We've migrated from Launchpad PPA to a self-hosted APT repository to fix SHA-1 signature issues.

## For Existing Users

If you're using the old PPA:

```bash
# Remove old PPA
sudo add-apt-repository --remove ppa:agornostal/ulauncher

# Add new repository
curl -fsSL https://apt.ulauncher.io/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/ulauncher.gpg
echo "deb [signed-by=/usr/share/keyrings/ulauncher.gpg] https://apt.ulauncher.io/ /" | sudo tee /etc/apt/sources.list.d/ulauncher.list

# Update
sudo apt update
sudo apt upgrade
```

## Benefits

- ✅ No more SHA-1 signature warnings
- ✅ Support for Debian (not just Ubuntu)
- ✅ Faster updates
- ✅ More reliable builds

See https://apt.ulauncher.io for details.
\```
```

### Update Documentation

- Installation page
- FAQ section
- Troubleshooting guide

## Step 8: Deprecate Launchpad PPA

### Option A: Keep for Legacy Users (6-12 months)

- Continue uploading to Launchpad for old Ubuntu versions
- Add deprecation notice to PPA description
- Gradually phase out

### Option B: Immediate Shutdown

- Stop uploading to Launchpad
- Update PPA description with migration instructions
- Remove Launchpad workflow from main repository

## Rollback Plan

If something goes wrong:

### Quick Fix

1. Re-enable Launchpad PPA uploads in main repository
2. Announce temporary issue with new repository
3. Fix issues in APT repository
4. Test thoroughly
5. Re-announce migration

### Files to Keep

Keep these files backed up before migration:
- `Ulauncher/debian/` directory
- `.github/workflows/publish-release.yml` (old version)
- Launchpad SSH keys and GPG keys

## Maintenance After Migration

### Regular Tasks

- **Monitor GitHub Actions**: Check for build failures
- **Update distro support**: Add new Ubuntu/Debian releases
- **Renew GPG key**: Before expiration (if set)
- **Update dependencies**: Keep nfpm and tools updated

### Monitoring

Set up alerts for:
- Failed workflow runs
- GitHub Pages downtime
- Package signature issues

## Troubleshooting

### Workflow Fails to Build

Check:
- Main repository is accessible
- Version can be detected from `ulauncher.version`
- All source files exist

### Packages Not Signed

Check:
- `APT_GPG_PRIVATE_KEY` secret is set correctly
- `APT_GPG_PASSPHRASE` is correct
- GPG key hasn't expired

### GitHub Pages Not Updating

Check:
- Pages is enabled in settings
- Workflow has `pages: write` permission
- DNS is configured correctly (if using custom domain)

### Users Can't Install

Check:
- Repository is publicly accessible
- `KEY.gpg` is accessible at `https://apt.ulauncher.io/KEY.gpg`
- `dists/` and `pool/` directories are published
- No CORS or caching issues

## Success Criteria

Migration is successful when:

- ✅ New repository builds packages automatically
- ✅ Packages are signed with SHA-256+
- ✅ GitHub Pages serves repository correctly
- ✅ Users can install without errors
- ✅ All distros work (Ubuntu 20.04, 22.04, 24.04, Debian 11, 12)
- ✅ Main repository no longer has `debian/` directory
- ✅ Documentation is updated
- ✅ Users are informed

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [nfpm Documentation](https://nfpm.goreleaser.com/)
- [Debian Repository Format](https://wiki.debian.org/DebianRepository/Format)

## Questions?

Open an issue in the APT repository or discuss in GitHub Discussions.