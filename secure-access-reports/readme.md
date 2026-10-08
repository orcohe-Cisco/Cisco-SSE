# Installing the Secure Access Reports skill in Claude

This guide shows how to add the **secure-access-reports** skill to Claude so it can build executive security reports and workforce connectivity reports from your Cisco Secure Access data.

> [!NOTE]
> The skill reads your data through the **Cisco Secure Access MCP server**, which runs on your computer and connects to Claude Desktop. If you haven't set it up yet, follow the [server setup guide](https://github.com/orcohe-Cisco/Secure-Access-Reports/blob/main/docs/INSTALL.md#part-1--run-the-secure-access-mcp-server) first. The skill installs without it, but it can't produce reports until the server is running.

---

## Requirements

| Requirement | Details |
|---|---|
| Claude plan | Free, Pro, Max, Team or Enterprise. Skills and code execution must be enabled. |
| Claude app | **Claude Desktop** (macOS or Windows), so Claude can reach the MCP server on your computer |
| Skill file | `secure-access-reports.zip` from the [latest release](https://github.com/orcohe-Cisco/Secure-Access-Reports/releases/latest) |

---

## Step 1 – Download the skill

1. Open the [latest release]([https://github.com/orcohe-Cisco/Secure-Access-Reports/releases/latest](https://github.com/orcohe-Cisco/Cisco-SSE/blob/main/secure-access-reports/secure-access-reports.zip)).
2. Under **Assets**, download **`secure-access-reports.zip`**.
3. Keep it as a ZIP; don't unzip it.

> [!IMPORTANT]
> Download the asset named `secure-access-reports.zip`, **not** "Source code (zip)". The source-code archive has a different folder layout and Claude will reject it.

## Step 2 – Turn on code execution

The skill runs scripts to build the PDF and HTML reports, so code execution must be on.

1. In Claude, open **Settings → Capabilities**.
2. Turn on **Code execution and file creation**.

**Team and Enterprise plans:** if you don't see these options, an organization owner needs to enable code execution and Skills in **Organization settings → Plugins & skills → Policy**. On Team plans this is on by default; on Enterprise an owner must turn it on.

## Step 3 – Upload the skill

1. Open **Customize → Skills**.
2. Click **+**, then **+ Create skill**.
3. Choose **Upload a skill** and select `secure-access-reports.zip`.
4. The skill **secure-access-reports** appears in your list. Make sure its toggle is **on**.

## Step 4 – Check that it works

Make sure the Secure Access MCP server is running, then start a **new chat** in Claude Desktop and ask:

```
Create an executive security report for Contoso from Secure Access for the last 30 days.
```

Claude should recognize the request, ask once for anything missing (customer name, period, language, audience), collect the data and return a PDF and an HTML report.

More example requests:

```
Create an executive security report for Contoso, last 30 days, in Hebrew, for the CISO.
```

```
צור דוח אבטחה למנהלים עבור Contoso מ-Secure Access על 30 הימים האחרונים, בעברית.
```

```
Create a workforce connectivity report for the last 14 days. Here is our device-to-employee list.
```

For the workforce report, attach a `people.csv` that maps laptops and accounts to employees, and read the [data and privacy notes](https://github.com/orcohe-Cisco/Secure-Access-Reports/blob/main/docs/DATA-AND-PRIVACY.md) first.

---

## Install for your whole organization (Team / Enterprise owners)

Organization owners can provision the skill for every member, so nobody has to upload it individually:

1. Open **Organization settings → Plugins & skills**.
2. Upload `secure-access-reports.zip` there.
3. Members see the skill in **Customize → Skills** with a team indicator. On Enterprise it appears for all users automatically; members can toggle it on or off.

Each member still needs access to a running Secure Access MCP server on their own computer.

## Install in Claude Code

If you use Claude Code instead of the Claude app:

1. Unzip `secure-access-reports.zip`.
2. Copy the `secure-access-reports` folder to `~/.claude/skills/`. You should end up with `~/.claude/skills/secure-access-reports/SKILL.md`.
3. Add the MCP server:

   ```bash
   claude mcp add --transport http cisco-secure-access http://127.0.0.1:8000/mcp \
     --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
   ```

4. Start a new Claude Code session and make the same requests as above.

---

## Updating the skill

1. Download the new `secure-access-reports.zip` from the [latest release](https://github.com/orcohe-Cisco/Secure-Access-Reports/releases/latest).
2. In **Customize → Skills**, delete the existing **secure-access-reports** skill.
3. Upload the new ZIP as in Step 3.

## Removing the skill

In **Customize → Skills**, toggle the skill off to pause it, or delete it to remove it completely. This doesn't affect the MCP server or your Secure Access tenant.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Upload is rejected | You probably uploaded "Source code (zip)" or a folder you zipped yourself. Upload the release asset `secure-access-reports.zip`. |
| No **Skills** or **Code execution** option | Your organization hasn't enabled them. Ask an owner to turn them on in **Organization settings → Plugins & skills → Policy**. |
| Claude doesn't use the skill | Check that the toggle is on in **Customize → Skills**, start a new chat, and mention "Secure Access" and "report" in your request. |
| Claude says it can't reach Secure Access | The MCP server isn't running or isn't connected. Start it, then check **Settings → Developer** in Claude Desktop shows `cisco-secure-access` as running. See the [server troubleshooting table](https://github.com/orcohe-Cisco/Secure-Access-Reports/blob/main/docs/INSTALL.md#troubleshooting). |
| You get an HTML report but no PDF | The PDF engine wasn't available in that session. Open the HTML file and use **Print → Save as PDF**; the layout is print-ready. |

---

## Support

This is a community project, not an official Cisco product, and it isn't supported by Cisco TAC. Report problems or suggestions in [GitHub issues](https://github.com/orcohe-Cisco/Secure-Access-Reports/issues).

Official Claude documentation: [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude) · [Provision and manage skills for your organization](https://support.claude.com/en/articles/13119606-provision-and-manage-skills-for-your-organization)
