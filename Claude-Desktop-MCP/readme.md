# Cisco Secure Access MCP Server — End-to-End Setup Guide (macOS & Windows + Claude Desktop)

This guide takes you from zero to asking Claude Desktop questions about your Cisco Secure Access tenant in natural language ("Show me the top threats this week", "Is evil.com in any destination list?").

It uses the official community server from CiscoDevNet:
**https://github.com/CiscoDevNet/secure-access-mcp-community**

The steps are written to avoid the common pitfalls (broken `.env` files, port conflicts, missing `npx`, Claude Desktop not picking up the server). If something still goes wrong, see [Troubleshooting](#troubleshooting).

---

## Table of Contents

- [How it works](#how-it-works)
- [Before you start](#before-you-start)
- [macOS setup](#macos-setup)
- [Windows setup](#windows-setup)
- [Verify it works](#verify-it-works)
- [Daily use](#daily-use)
- [Example prompts](#example-prompts)
- [Troubleshooting](#troubleshooting)
- [Security notes](#security-notes)
- [Updating the server](#updating-the-server)

---

## How it works

```
Claude Desktop
   │  launches (stdio)
   ▼
mcp-remote  (small Node.js bridge, run via npx)
   │  HTTP + "Authorization: Bearer <MCP_AUTH_TOKEN>"
   ▼
Secure Access MCP server  (Python, http://127.0.0.1:8000/mcp)
   │  OAuth2 client credentials (API key + secret)
   ▼
Cisco Secure Access API
```

- The **MCP server** runs locally in a terminal window and holds your Cisco API credentials.
- **Claude Desktop** cannot point at a `localhost` URL as a connector, so it talks to the server through **`mcp-remote`**, a bridge that Claude Desktop starts automatically.
- The **`MCP_AUTH_TOKEN`** is a random secret that protects the local server. Only clients that send it can use your Cisco credentials.

---

## Before you start

You need:

| Item | Where to get it |
| --- | --- |
| Cisco Secure Access **API key + secret** | Secure Access dashboard → **Admin → API Keys** → Add. Grant the scopes you need: **Policies** (destination lists, rules), **Reports** (activity, summaries, top-N), **Investigate** (domain risk/categorization), **Deployments** (roaming computers, networks, tunnels). |
| **Claude Desktop** | https://claude.ai/download |
| Admin rights to install packages | Homebrew (macOS) or winget (Windows) |

> [!IMPORTANT]
> Copy the API secret when you create it. Secure Access shows it only once.

> [!TIP]
> Type or paste commands **exactly** as shown. The command blocks intentionally contain no `#` comments, because zsh rejects comments typed at the prompt (`zsh: command not found: #`).

---

## macOS setup

### 1. Install the tools (Homebrew, git, uv, Node.js)

If you don't have Homebrew yet:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the "Next steps" the installer prints (it adds `brew` to your PATH), then open a new terminal window.

Install the three dependencies:

```bash
brew install git uv node
```

Check them:

```bash
git --version && uv --version && node --version && npx --version
```

> [!NOTE]
> `uv` manages Python for you, including downloading Python 3.11 into the project. You do **not** need to install Python, use `pip`, or activate a virtual environment. This avoids the `externally-managed-environment`, `command not found: python`, and `No module named 'dotenv'` errors.

### 2. Clone the repository

```bash
cd ~
git clone https://github.com/CiscoDevNet/secure-access-mcp-community.git
cd ~/secure-access-mcp-community
```

> Any folder works; this guide uses `~/secure-access-mcp-community`. If you choose another location, adjust the paths below.

### 3. Create the Python environment and install dependencies

```bash
uv venv --python 3.11
uv pip install -r requirements.txt
```

### 4. Create the `.env` file

This writes a clean `.env` without leading or trailing spaces, quotes, or `export` keywords, which is what `python-dotenv` expects. You are prompted for the key and secret, so they never land in your shell history. The secret input is hidden.

```bash
cd ~/secure-access-mcp-community
read "KEY?API key: "
read -s "SECRET?API secret: "; echo
TOKEN=$(uv run python -c 'import secrets; print(secrets.token_urlsafe(32))')
printf 'SECURE_ACCESS_API_KEY=%s\nSECURE_ACCESS_API_SECRET=%s\nMCP_AUTH_TOKEN=%s\n' "${KEY// /}" "${SECRET// /}" "$TOKEN" > .env
chmod 600 .env
unset KEY SECRET TOKEN
```

Make sure no old values in your shell override the file. Variables exported in the shell **take priority over `.env`**:

```bash
unset SECURE_ACCESS_API_KEY SECURE_ACCESS_API_SECRET MCP_AUTH_TOKEN MCP_ALLOW_NO_AUTH
```

Sanity check that the file has 3 lines and no stray characters, without printing the secrets:

```bash
cut -d= -f1 .env
```

Expected output:

```
SECURE_ACCESS_API_KEY
SECURE_ACCESS_API_SECRET
MCP_AUTH_TOKEN
```

### 5. Free port 8000 (only if something is already using it)

```bash
lsof -ti tcp:8000 | xargs kill -9 2>/dev/null; lsof -i tcp:8000
```

The second command should print nothing.

### 6. Start the server

```bash
cd ~/secure-access-mcp-community
uv run python -m cisco_secure_access_mcp
```

Expected output (no `could not parse` warning, no errors):

```
{"level":"INFO", ... "message":"starting server","event":"startup"}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

> [!WARNING]
> **Leave this terminal window open.** Stop the server with **Ctrl+C** only. **Never press Ctrl+Z**: it suspends the process, which keeps holding port 8000 and causes `address already in use` on the next start.

### 7. Register the server in Claude Desktop

Open a **new terminal tab** (**Cmd+T**) and run the following. It backs up your existing Claude Desktop config, **merges** the new server into it (other servers and settings are kept), reads the token from `.env`, and uses the absolute path of `npx`, because Claude Desktop does not inherit your shell's PATH.

```bash
cd ~/secure-access-mcp-community
cp "$HOME/Library/Application Support/Claude/claude_desktop_config.json" "$HOME/Library/Application Support/Claude/claude_desktop_config.json.bak" 2>/dev/null
uv run python - <<'EOF'
import json, os, pathlib, shutil, sys
env = dict(l.split("=", 1) for l in pathlib.Path(".env").read_text(encoding="utf-8").splitlines() if "=" in l)
token = env["MCP_AUTH_TOKEN"].strip()
npx = shutil.which("npx") or next((p for p in ("/opt/homebrew/bin/npx", "/usr/local/bin/npx") if os.path.exists(p)), None)
if not npx:
    sys.exit("npx not found. Run: brew install node")
p = pathlib.Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
p.parent.mkdir(parents=True, exist_ok=True)
cfg = json.loads(p.read_text(encoding="utf-8")) if p.exists() and p.read_text(encoding="utf-8").strip() else {}
cfg.setdefault("mcpServers", {})["cisco-secure-access"] = {
    "command": npx,
    "args": ["-y", "mcp-remote", "http://127.0.0.1:8000/mcp", "--header", "Authorization:${AUTH_HEADER}"],
    "env": {"AUTH_HEADER": f"Bearer {token}", "PATH": f"{os.path.dirname(npx)}:/usr/bin:/bin"},
}
p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
print("Updated", p)
EOF
```

Expected: `Updated /Users/<you>/Library/Application Support/Claude/claude_desktop_config.json`

<details>
<summary>What the resulting config entry looks like</summary>

```json
{
  "mcpServers": {
    "cisco-secure-access": {
      "command": "/opt/homebrew/bin/npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://127.0.0.1:8000/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer <your MCP_AUTH_TOKEN>",
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin"
      }
    }
  }
}
```

The header is passed as `Authorization:${AUTH_HEADER}` (no space after the colon) with the value in `env`. This avoids argument-splitting problems with spaces.
</details>

### 8. Restart Claude Desktop

Quit it **completely** with **Cmd+Q** (closing the window is not enough), then open it again.

Continue with [Verify it works](#verify-it-works).

---

## Windows setup

All commands are for **PowerShell** (Start → type `PowerShell`). A regular, non-admin window is fine unless winget asks for elevation.

### 1. Install the tools (git, uv, Node.js)

```powershell
winget install --id Git.Git -e --source winget
winget install --id astral-sh.uv -e --source winget
winget install --id OpenJS.NodeJS.LTS -e --source winget
```

**Close PowerShell and open a new window** so the updated PATH is loaded, then check:

```powershell
git --version; uv --version; node --version; npx --version
```

> [!NOTE]
> If `winget` is unavailable, install uv with
> `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`,
> and get Git and Node.js LTS from https://git-scm.com and https://nodejs.org.

### 2. Clone the repository

```powershell
cd $HOME
git clone https://github.com/CiscoDevNet/secure-access-mcp-community.git
cd $HOME\secure-access-mcp-community
```

> Avoid cloning into a OneDrive-synced folder (often your Desktop or Documents). Sync can lock files and would upload your `.env`.

### 3. Create the Python environment and install dependencies

```powershell
uv venv --python 3.11
uv pip install -r requirements.txt
```

### 4. Create the `.env` file

This writes the file as **UTF-8 without BOM**. Windows PowerShell's default `Out-File` and `>` produce UTF-16 or BOM-prefixed files, which causes `python-dotenv could not parse statement starting at line 1`.

```powershell
cd $HOME\secure-access-mcp-community
$key = (Read-Host "API key").Trim()
$secSecret = Read-Host "API secret" -AsSecureString
$secret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secSecret)).Trim()
$token = (uv run python -c "import secrets; print(secrets.token_urlsafe(32))").Trim()
$content = "SECURE_ACCESS_API_KEY=$key`nSECURE_ACCESS_API_SECRET=$secret`nMCP_AUTH_TOKEN=$token`n"
[IO.File]::WriteAllText("$PWD\.env", $content, (New-Object System.Text.UTF8Encoding $false))
Remove-Variable key, secret, secSecret, token, content
```

Clear any old values from the current session, since they would override `.env`:

```powershell
Remove-Item Env:SECURE_ACCESS_API_KEY, Env:SECURE_ACCESS_API_SECRET, Env:MCP_AUTH_TOKEN, Env:MCP_ALLOW_NO_AUTH -ErrorAction SilentlyContinue
```

Sanity check without printing secrets:

```powershell
Get-Content .env | ForEach-Object { ($_ -split '=')[0] }
```

Expected: `SECURE_ACCESS_API_KEY`, `SECURE_ACCESS_API_SECRET`, `MCP_AUTH_TOKEN`.

### 5. Free port 8000 (only if something is already using it)

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### 6. Start the server

```powershell
cd $HOME\secure-access-mcp-community
uv run python -m cisco_secure_access_mcp
```

Expected: `Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

> [!WARNING]
> **Leave this window open.** Stop the server with **Ctrl+C**. If Windows Firewall prompts, you can deny external access, because the server only listens on `127.0.0.1`.

### 7. Register the server in Claude Desktop

Open a **second PowerShell window** and run the following. It finds the correct config file automatically, which matters because the **standard installer** and the **Microsoft Store** version store it in different places. It then backs up the config, merges the server entry, and launches `npx` through `cmd /c`, which is the reliable way for Claude Desktop on Windows to start `npx.cmd`.

```powershell
cd $HOME\secure-access-mcp-community
@'
import glob, json, os, pathlib, shutil
env = dict(l.split("=", 1) for l in pathlib.Path(".env").read_text(encoding="utf-8-sig").splitlines() if "=" in l)
token = env["MCP_AUTH_TOKEN"].strip()
store = glob.glob(os.path.join(os.environ["LOCALAPPDATA"], "Packages", "Claude_*", "LocalCache", "Roaming", "Claude"))
cfg_dir = pathlib.Path(store[0]) if store else pathlib.Path(os.environ["APPDATA"]) / "Claude"
cfg_dir.mkdir(parents=True, exist_ok=True)
p = cfg_dir / "claude_desktop_config.json"
if p.exists():
    shutil.copy(p, p.with_suffix(".json.bak"))
cfg = json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() and p.read_text(encoding="utf-8-sig").strip() else {}
cfg.setdefault("mcpServers", {})["cisco-secure-access"] = {
    "command": "cmd",
    "args": ["/c", "npx", "-y", "mcp-remote", "http://127.0.0.1:8000/mcp", "--header", "Authorization:${AUTH_HEADER}"],
    "env": {"AUTH_HEADER": f"Bearer {token}"},
}
p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
print("Updated", p)
'@ | uv run python -
```

Expected: `Updated C:\Users\<you>\AppData\...\Claude\claude_desktop_config.json`

<details>
<summary>What the resulting config entry looks like</summary>

```json
{
  "mcpServers": {
    "cisco-secure-access": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-remote",
        "http://127.0.0.1:8000/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer <your MCP_AUTH_TOKEN>"
      }
    }
  }
}
```
</details>

> [!TIP]
> To open the exact config file Claude Desktop is using, go to **Claude Desktop → Settings → Developer → Edit Config**.

### 8. Restart Claude Desktop

Closing the window only minimizes Claude Desktop to the system tray. **Right-click the Claude icon in the tray → Quit**, then open it again.

---

## Verify it works

1. **Server is reachable and enforcing auth.** From a new terminal:

   macOS:
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/mcp
   ```
   Windows:
   ```powershell
   curl.exe -s -o NUL -w "%{http_code}`n" http://127.0.0.1:8000/mcp
   ```
   `401` means the server is up and rejecting requests that carry no token, which is correct. `000` means the server isn't running.

2. **Claude Desktop sees the server.** Open **Settings → Developer**. `cisco-secure-access` should be listed as **running**.
   > The **Extensions** page stays empty. That is expected, because servers added through the config file appear under **Developer**.

3. **End-to-end test.** In a new chat, ask:
   > Show all destination lists

   Claude asks permission to use the tool the first time. The server terminal should log incoming `POST /mcp` requests.

---

## Daily use

1. Start the server (keep the window open):
   - macOS: `cd ~/secure-access-mcp-community && uv run python -m cisco_secure_access_mcp`
   - Windows: `cd $HOME\secure-access-mcp-community; uv run python -m cisco_secure_access_mcp`
2. Open Claude Desktop and chat.
3. When done, press **Ctrl+C** in the server window.

If Claude Desktop was opened **before** the server started, the tools fail to load. Restart Claude Desktop (Cmd+Q / tray → Quit) after starting the server.

---

## Example prompts

**Executive / health check**
- "Give me a security summary for the last 7 days: total, allowed vs. blocked."
- "What are the top 10 threats and threat types this week?"
- "Show requests by hour for the last 24 hours and point out spikes."
- "How much bandwidth did we use per day this week?"

**Threat hunting**
- "Investigate `suspicious-domain.xyz`: risk, categorization, and whether anyone accessed it."
- "Show blocked DNS events for malware/phishing in the last 24 hours, grouped by identity."
- "Which identities triggered the most security events this week?"
- "Show intrusion prevention activity and the top IPS rules that fired."
- "List AMP retrospective events and top files seen in proxy traffic."

**Policy & rules**
- "List all access rules and explain each one in plain language."
- "Which rules had zero hits in the last 30 days?"
- "Show firewall rule hit counts."
- "Create a block rule for the Gambling and Crypto Mining categories." *(write actions require confirmation)*

**Destination lists**
- "Show all destination lists with entry counts."
- "Is `example.com` in any destination list?"
- "Find destinations that appear in multiple lists."
- "Audit stale, empty, or low-count lists."
- "How close are we to the 250,000 destination limit?"
- "Create a block list 'IR-2026-10' and add these domains: …"

**ZTNA / private access**
- "Show ZTNA activity for the last 24 hours: who accessed which private apps?"
- "Top private resources by usage, and the count of unique resources accessed."

**Infrastructure**
- "List roaming computers, network tunnels, and internal networks."

**Multi-step**
- "Build a weekly security report: summary numbers, top threats, riskiest identities, top blocked categories, and 3 recommended actions."
- "Investigate user X over the last 7 days: activity, blocks, categories. Anything concerning?"
- "Check this IOC list against our traffic, then add the ones not yet blocked to a new block list."
- "Compare blocked traffic this week vs. last week by category."

**Multi-org (parent/MSP tenants)**
- "List child organizations and give me a threat summary per org."

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `zsh: command not found: python` | macOS ships `python3` only | Use `uv run python ...`. uv provides the right interpreter. |
| `error: externally-managed-environment` | `pip install` into Homebrew's system Python | Don't use system pip. Use `uv pip install -r requirements.txt` inside the project. |
| `ModuleNotFoundError: No module named 'dotenv'` | Server started with system `python3` outside the project venv | Start with `uv run python -m cisco_secure_access_mcp`. |
| `python-dotenv could not parse statement starting at line 1` | Malformed `.env`: `export` keyword, spaces around `=`, smart quotes, or (Windows) UTF-16/BOM encoding | Recreate `.env` with step 4 of your OS section. |
| `Error: No client authentication configured` | `MCP_AUTH_TOKEN` missing or `.env` not parsed | Recreate `.env` (step 4) and confirm with the sanity check. |
| `MCP_AUTH_TOKEN and MCP_ALLOW_NO_AUTH are both set` | Both variables present in the shell | `unset MCP_ALLOW_NO_AUTH` (macOS) / `Remove-Item Env:MCP_ALLOW_NO_AUTH` (Windows). |
| `[Errno 48] address already in use` (macOS) / `[WinError 10048]` (Windows) | An earlier server is still running, often suspended with **Ctrl+Z** | Run step 5 of your OS section. A suspended process ignores plain `kill`, so `-9` / `-Force` is required. |
| Server starts but tools return 401 from Cisco | Wrong key/secret, or a trailing space copied with it | Recreate `.env` (step 4 strips spaces). Also run `unset` for old exported values, since shell variables override `.env`. |
| Tools return 401/403 for some queries only | API key lacks a scope | Edit the key in Secure Access and add the Reports / Policies / Investigate / Deployments scope. |
| `zsh: command not found: #` | Comments pasted at the zsh prompt | Paste only the commands. |
| `vi ~/Library/Application Support/...` says "2 files to edit" | Unquoted path with a space | Quote the path: `"$HOME/Library/Application Support/Claude/claude_desktop_config.json"`. |
| `npx: command not found` | Node.js not installed | `brew install node` / `winget install OpenJS.NodeJS.LTS`, then open a new terminal. |
| Server not listed under Settings → Developer | Claude Desktop not fully restarted, or wrong config file | Quit fully (Cmd+Q / tray → Quit). On Windows, use **Settings → Developer → Edit Config** to confirm the file location. |
| Server listed as **failed** | Server not running, wrong token, or `npx` not found | Start the server first, then restart Claude Desktop. Check the log (below). |
| `claude: command not found` | Refers to the separate Claude Code CLI, which this setup doesn't need | Ignore. This guide uses Claude Desktop only. |

**Claude Desktop logs for this server:**

- macOS:
  ```bash
  tail -50 ~/Library/Logs/Claude/mcp-server-cisco-secure-access.log
  ```
- Windows:
  ```powershell
  Get-Content "$env:APPDATA\Claude\logs\mcp-server-cisco-secure-access.log" -Tail 50
  ```

---

## Security notes

- **Never paste the API key, secret, or MCP token into chats, tickets, or screenshots.** If that happens, revoke the key in **Admin → API Keys**, create a new one, and rerun step 4.
- `.env` holds live credentials. Keep it out of git and out of synced folders (OneDrive, iCloud Desktop/Documents). On macOS, `chmod 600 .env` restricts it to your user.
- Keep the server bound to `127.0.0.1` (the default). Don't use `HOST=0.0.0.0` unless you put it behind TLS and access controls.
- Don't use `MCP_ALLOW_NO_AUTH=true` outside short, isolated tests. Anything on your machine could then use your Cisco credentials.
- Destructive tools (deleting lists, removing destinations) use two-stage confirmation by default (`SECURE_ACCESS_REQUIRE_CONFIRMATION=true`). Keep it on.
- Optional: set `SECURE_ACCESS_REDACT_PII=true` in `.env` to mask identities, IPs, and emails in report output, which is useful for demos and screen sharing.

---

## Updating the server

macOS:

```bash
cd ~/secure-access-mcp-community
git pull
uv pip install -r requirements.txt
```

Windows:

```powershell
cd $HOME\secure-access-mcp-community
git pull
uv pip install -r requirements.txt
```

Then restart the server and Claude Desktop.

---

**Upstream project:** https://github.com/CiscoDevNet/secure-access-mcp-community · Licensed under Apache-2.0
