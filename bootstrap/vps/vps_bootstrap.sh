#!/bin/bash
# VPS Bootstrap -- shared setup script for Debian 12 (bookworm) instances.
# Provisions a fresh VPS: Docker, SSH hardening, firewall, fail2ban,
# unattended-upgrades.
# Idempotent -- delete /etc/.vps-setup-done to force re-run.
#
# Works on any provider (Vultr, Aliyun, Hetzner, etc.).
# Docker repo detection: probes the official repo first; if unreachable
# (e.g., from within China), falls back to domestic mirrors automatically.
#
# Usage -- provider startup script:
#   Paste into the "Startup Script" / "User Data" field when creating
#   a Debian 12 instance.
#
# Usage -- manual run (e.g., provider without startup-script support):
#   ssh root@<ip> 'bash -s' < vps_bootstrap.sh
#
# Environment detection is automatic: probes google.com reachability
# to decide between domestic and foreign configuration (Docker mirrors,
# etc.).  Override with DNS_MODE=domestic or DNS_MODE=foreign if needed.

set -euo pipefail

SENTINEL="/etc/.vps-setup-done"

if [[ -f "$SENTINEL" ]]; then
    echo "= Setup already completed ($(cat "$SENTINEL"))."
    echo "= Remove $SENTINEL to force re-run."
    exit 0
fi

echo "==> Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# ===========================================================================
# Environment detection -- probe once, used by all downstream sections.
# ===========================================================================
# Detect whether we're inside China (google.com unreachable).
# Sets DNS_MODE=domestic or DNS_MODE=foreign.
# Override with DNS_MODE=domestic or DNS_MODE=foreign if needed.
if [ -z "${DNS_MODE:-}" ]; then
    echo "==> Detecting environment..."
    if curl -fsSL --connect-timeout 3 --max-time 5 https://www.google.com >/dev/null 2>&1; then
        DNS_MODE=foreign
    else
        DNS_MODE=domestic
    fi
fi
echo "   Environment: $DNS_MODE"

# ===========================================================================
# User setup -- ensure linuxuser exists (Vultr creates it, Aliyun doesn't)
# ===========================================================================
echo "==> Ensuring linuxuser user..."
if id linuxuser &>/dev/null; then
    echo "   linuxuser already exists"
else
    useradd -m -s /bin/bash -G sudo linuxuser
    echo "   linuxuser created"

    # Sync SSH keys from root so the new user can log in.
    mkdir -p ~linuxuser/.ssh
    if [ -f ~root/.ssh/authorized_keys ]; then
        cp ~root/.ssh/authorized_keys ~linuxuser/.ssh/authorized_keys
        chmod 700 ~linuxuser/.ssh
        chmod 600 ~linuxuser/.ssh/authorized_keys
        chown -R linuxuser:linuxuser ~linuxuser/.ssh
        echo "   SSH keys synced from root"
    fi
fi
# Passwordless sudo -- always apply (may have been missing).
cat > /etc/sudoers.d/linuxuser <<'SUDOEOF'
linuxuser ALL=(ALL:ALL) NOPASSWD: ALL
SUDOEOF
chmod 440 /etc/sudoers.d/linuxuser

# ===========================================================================
# Docker Engine + Compose plugin
# ===========================================================================
echo "==> Installing Docker Engine..."
if ! command -v docker &>/dev/null; then
    apt-get install -y -qq ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings

    # Probe Docker mirrors -- try official first; if unreachable (e.g.,
    # GFW blocks download.docker.com), fall back to domestic mirrors.
    # The GPG key is a small, reliable canary for mirror reachability.
    MIRRORS=(
        "official|https://download.docker.com/linux/debian"
        "Tsinghua|https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/debian"
        "Aliyun|https://mirrors.aliyun.com/docker-ce/linux/debian"
    )
    DOCKER_BASE=""
    for entry in "${MIRRORS[@]}"; do
        label="${entry%%|*}"
        base="${entry#*|}"
        if curl -fsSL --connect-timeout 5 --max-time 10 "${base}/gpg" -o /dev/null 2>/dev/null; then
            DOCKER_BASE="$base"
            echo "   Using $label mirror"
            break
        fi
    done

    if [ -z "$DOCKER_BASE" ]; then
        echo "!! Cannot reach any Docker mirror (official or domestic)."
        exit 1
    fi

    curl -fsSL "${DOCKER_BASE}/gpg" -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] ${DOCKER_BASE} $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    fi

# Docker Hub is blocked domestically -- configure registry mirrors.
# Only applied when DNS_MODE=domestic (set by the early environment probe).
# Probe a list of known mirrors; only keep the ones that respond.
if [ "$DNS_MODE" = "domestic" ]; then
    echo "==> Probing Docker registry mirrors..."
    DOCKER_MIRRORS=(
        "https://docker.m.daocloud.io"
        "https://docker.1panel.live"
        "https://docker.1ms.run"
        "https://docker.xuanyuan.me"
        "https://hub.rat.dev"
        "https://dockerpull.org"
        "https://dockerhub.icu"
    )

    WORKING=()
    for mirror in "${DOCKER_MIRRORS[@]}"; do
        if curl -fsSL --connect-timeout 5 --max-time 10 "${mirror}/v2/" -o /dev/null 2>/dev/null; then
            WORKING+=("\"$mirror\"")
            echo "   + $mirror"
        else
            echo "   - $mirror (unreachable)"
        fi
    done

    if [ ${#WORKING[@]} -gt 0 ]; then
        # Build JSON array with comma separators
        MIRROR_LIST=$(IFS=,; echo "${WORKING[*]}")
        cat > /etc/docker/daemon.json <<DOCKEREOF
{
  "registry-mirrors": [${MIRROR_LIST}]
}
DOCKEREOF
        systemctl restart docker
        echo "   Configured ${#WORKING[@]} registry mirror(s)"
    else
        echo "   !! No working mirrors found -- Docker Hub may be unreachable"
    fi
else
    echo "==> Skipping Docker registry mirrors (foreign VPS)"
fi

# ===========================================================================
# SSH hardening --- port 9906, key-only, no password auth
# ===========================================================================
echo "==> Hardening SSH..."

# OpenSSH reads drop-in files in sorted order; first value wins for
# most directives.  Debian cloud images ship 50-cloud-init.conf which
# can set Port 22 and PasswordAuthentication yes.  We write a 00- prefixed
# drop-in so our settings take priority over everything else in that
# directory.
cat > /etc/ssh/sshd_config.d/00-hardening.conf <<'SSHEOF'
Port 9906
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
SSHEOF

# Remove any conflicting Port / PasswordAuthentication from the main
# config (usually commented out on Debian, but be safe).
sed -i '/^Port /d'                       /etc/ssh/sshd_config
sed -i '/^PasswordAuthentication /d'     /etc/ssh/sshd_config

# Re-validate auth state just in case a later drop-in overrode us
chmod 600 /etc/ssh/sshd_config.d/00-hardening.conf

if sshd -t; then
    systemctl restart sshd
    echo "   SSH now on port 9906 (key auth only)."
else
    echo "!! sshd config syntax error --- removing drop-in"
    rm -f /etc/ssh/sshd_config.d/00-hardening.conf
    systemctl restart sshd
    exit 1
fi

# ===========================================================================
# Tailscale --- mesh VPN for SSH and internal services
# ===========================================================================
echo "==> Installing Tailscale..."
if ! command -v tailscale &>/dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
    systemctl enable tailscaled
fi

# ===========================================================================
# Runtime dependencies for per-host scripts
# ===========================================================================
echo "==> Installing runtime dependencies..."
apt-get install -y -qq nodejs python3-yaml rsync

# ===========================================================================
# UFW firewall --- allow SSH (9906), HTTP, HTTPS
# ===========================================================================
echo "==> Configuring UFW firewall..."
apt-get install -y -qq ufw

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 9906/tcp comment 'SSH'
ufw allow 80/tcp   comment 'HTTP'
ufw allow 443/tcp  comment 'HTTPS'
ufw allow 443/udp  comment 'HTTP/3 QUIC'
ufw allow in on tailscale0 comment 'Tailscale mesh'
ufw allow 8443/tcp comment 'Tailscale DERP'
ufw allow 33478/udp comment 'Tailscale DERP STUN'
ufw --force enable

# ===========================================================================
# fail2ban --- brute-force protection for SSH
# ===========================================================================
echo "==> Installing fail2ban..."
apt-get install -y -qq fail2ban rsyslog

cat > /etc/fail2ban/jail.local <<'F2BEOF'
[DEFAULT]
bantime   = 1h
findtime  = 10m
maxretry  = 5

[sshd]
enabled   = true
port      = 9906
logpath   = /var/log/auth.log
F2BEOF

systemctl restart fail2ban

# ===========================================================================
# unattended-upgrades --- automatic security patches
# ===========================================================================
echo "==> Enabling unattended-upgrades..."
apt-get install -y -qq unattended-upgrades apt-listchanges

cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'UEOF'
Unattended-Upgrade::Origins-Pattern {
    "origin=Debian,codename=${distro_codename},label=Debian-Security";
    "origin=Debian,codename=${distro_codename}-security,label=Debian-Security";
};
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
UEOF

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'UEOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
UEOF

# ===========================================================================
# Done
# ===========================================================================
date > "$SENTINEL"
echo "==> VPS setup complete."
echo
echo "    +==========================================================+"
echo "    |  Set hostname so install.py activates the right config: |"
echo "    |                                                        |"
echo "    |  hostnamectl set-hostname conduit                       |"
echo "    |                                                        |"
echo "    |  Then clone and install:                                |"
echo "    |  git clone https://github.com/<you>/dotfiles.git        |"
echo "    |  cd dotfiles && cp per_host/conduit/.env.example \\      |"
echo "    |    per_host/conduit/.env   # then fill from Bitwarden   |"
echo "    |  python3 install.py                                     |"
echo "    +==========================================================+"
