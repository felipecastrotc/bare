# 🗓️ Scheduled Backup Setup (Linux & macOS)


This guide explains how to schedule automated backups using the `bare backup` CLI tool managed via a Python wrapper script. The script handles Tailscale, state tracking, and logs, and is run daily via:

* `systemd` on **Linux**
* `launchd` on **macOS**

---

## 📁 Files Required

You must have the following before proceeding:

* The `bare` package installed in your system.
* Network reachability to your backup server
* Tailscale (optional, if your server requires it)

---

NOTE: NOT TESTED
TODO: improve and review the step by step

## ⚙️ Setup on Linux (with systemd)

### 1. ✅ Install Dependencies

Ensure the following tools are installed:

```bash
sudo apt install systemd
```

Make sure you have:

* Python 3
* pip or pipx

---

### 2. 🧾 Create systemd Unit Files

#### a. Create the **Service Unit**

Save the following to:

```bash
~/.config/systemd/user/bare-backup.service
```

```ini
[Unit]
Description=Automated Bare Backup
After=network-online.target

[Service]
Type=simple
ExecStart=/home/youruser/bare/bare_runner
Environment=BARE_BIN=/home/youruser/bare/bare
Environment=BACKUP_SERVER_HOST=your-backup-host
Environment=BACKUP_SERVER_PORT=8000

[Install]
WantedBy=default.target
```

> ✅ Replace `/home/youruser/...` paths and hostnames with your actual values.

---

#### b. Create the **Timer Unit**

Save this as:

```bash
~/.config/systemd/user/bare-backup.timer
```

```ini
[Unit]
Description=Run Bare Backup Daily

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

### 3. 🔄 Enable & Start

```bash
# Reload systemd units
systemctl --user daemon-reexec
systemctl --user daemon-reload

# Enable both service and timer
systemctl --user enable --now bare-backup.service
systemctl --user enable --now bare-backup.timer
```

---

### 4. ✅ Verify Status

```bash
systemctl --user status bare-backup.service
systemctl --user list-timers
```

---

## 🍏 Setup on macOS (with launchd)

### 1. ✅ Prepare Your Environment

Ensure:

* Python 3 is installed (use Homebrew or pyenv)
* micromamba is installed
* The `bare` CLI tool is working inside your micromamba env

---

### 2. 🧾 Create `launchd` Plist

Create the file:

```bash
~/Library/LaunchAgents/com.user.barebackup.plist
```

With contents:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.barebackup</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOURUSER/.local/bin/bare_runner</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>BARE_BIN</key>
        <string>/Users/YOURUSER/.local/bin/bare</string>
        <key>BACKUP_SERVER_HOST</key>
        <string>your-backup-host</string>
        <key>BACKUP_SERVER_PORT</key>
        <string>8000</string>
    </dict>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/barebackup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/barebackup.err</string>
</dict>
</plist>
```

> ✅ Replace paths and variables with your actual values.


---

### 🧠 Alternative: `StartInterval` Configuration for Laptops

If you’re using a **laptop or a device that frequently sleeps/wakes**, consider using the following `launchd` configuration instead. It ensures:

* The task runs **every 24 hours** from the last run.
* It **resumes** on wake if missed.
* It **avoids overlapping** executions.
* It runs in **low priority** background mode.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>

  <key>Label</key>
  <string>com.user.resticbackup</string>

  <key>ProgramArguments</key>
  <array>
      <string>/Users/YOURUSER/.local/bin/bare_runner</string>
  </array>

  <!-- Runs every 24h from last successful execution.
       On sleep, runs at next opportunity. Ideal for laptops. -->
  <key>StartInterval</key>
  <integer>86400</integer>

  <!-- Triggers when network becomes available -->
  <key>KeepAlive</key>
  <dict>
    <key>NetworkState</key>
    <true/>
  </dict>

  <!-- Also triggers when user logs in (e.g., on boot or wake) -->
  <key>RunAtLoad</key>
  <true/>

  <!-- Prevents multiple overlapping runs -->
  <key>AbandonProcessGroup</key>
  <true/>

  <!-- Run in low-priority background mode -->
  <key>ProcessType</key>
  <string>Background</string>
  <key>Nice</key>
  <integer>10</integer>

  <!-- Logging -->
  <key>StandardOutPath</key>
  <string>/Users/YOUR_USERNAME/Library/Logs/restic-backup.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOUR_USERNAME/Library/Logs/restic-backup.err</string>

</dict>
</plist>
```

> 💡 **Why this is ideal for laptops:**
>
> * Doesn’t require the system to be awake at a fixed time.
> * Automatically adjusts to missed runs.
> * Wakes up on network availability or user login.
> * Never runs multiple times in parallel.


---

### 3. 🔄 Load and Start the Job

```bash
launchctl load ~/Library/LaunchAgents/com.user.barebackup.plist
launchctl start com.user.barebackup
```

To automatically run on boot:

```bash
launchctl enable gui/$(id -u)/com.user.barebackup
```

---

### 4. ✅ Check Logs

```bash
cat /tmp/barebackup.log
cat /tmp/barebackup.err
```

---

## 🔁 Optional: Manual Run / Test

You can manually test the backup script with:

```bash
bare_runner --dry-run
```

Or:

```bash
bare backup
```

---

## 📍 Environment Variables Reference

| Variable             | Purpose                              |
| -------------------- | ------------------------------------ |
| `BARE_BIN`           | Path to the bare script.             |
| `BACKUP_SERVER_HOST` | Hostname or IP of backup server      |
| `BACKUP_SERVER_PORT` | TCP port for backup server           |
| `TAILSCALE_BIN`      | Optional: path to `tailscale` binary |

---

## 🧪 Troubleshooting

* Use `--dry-run` to safely test
* Review logs in:

  * Linux: `~/.local/share/logs/bare-backup.log`
  * macOS: `/tmp/barebackup.log`
* Ensure `bare` works correctly inside the micromamba env

### MacOS useful commands

Force start:
* `launchctl kickstart -k gui/$(id -u)/com.user.barebackup`

Check MacOS logs:
* `log show --predicate 'process == "launchd"' --info --last 5m | grep bare`
* `cat /tmp/barebackup.log`
