# Publishing & installing orchestrator-loop

This plugin is distributed straight from its **GitHub repo** — the repo *is* the marketplace
(`.claude-plugin/marketplace.json` at the root). There is no separate registry to submit to.
"Publishing" = making the repo installable by whoever you want to reach.

## How distribution works

- `/.claude-plugin/plugin.json` — the plugin manifest (name, version, description).
- `/.claude-plugin/marketplace.json` — a one-plugin marketplace pointing at `"source": "."`.
  This is what lets someone run "add marketplace `<owner>/<repo>`" and find the plugin inside.
- Installers point at `owner/repo`; Cowork/Claude Code read these two files and load the
  skills + the SessionStart guardrails hook.

So the only thing that gates who can install it is **repo visibility**:

| Repo visibility | Who can install | Use when |
|---|---|---|
| **Private** | only you (and collaborators), with your GitHub auth | testing; personal use |
| **Public** | anyone with the `owner/repo` string | sharing / "publishing" |

You can flip between them anytime; it's reversible and changes nothing in the plugin itself.

## Install (what an end user does)

**Cowork (desktop app):** Settings → Plugins → Add plugin → GitHub → enter `<owner>/orchestrator-loop`.
Plugins activate on the **next** session, not mid-session. (Or upload the `.plugin` file directly.)

**Claude Code (CLI):**
```
claude plugin marketplace add <owner>/orchestrator-loop
claude plugin install orchestrator-loop
```

Then copy `app-profile.template.md` into the target repo as `CLAUDE.md` and fill it in
(connectors, infra, domain rules, sanity bounds, constitution + roadmap pointers).

## Recommended path: test before you go public

1. **Keep the repo private.** You can already install your own private repo (your GitHub auth
   covers it) — you do **not** need it public to test.
2. **Run the clean-room test kit** (`test/`) in a fresh folder/session — the protocol is in
   `test/README.md`. The whole point is to confirm the plugin reproduces the behavior of your
   prior setup *before* anyone else can install it.
3. **Confirm guardrail delivery in Cowork.** Cowork doesn't reliably fire SessionStart hooks,
   so the guardrails ride on the app-profile's first line (the "Operating under
   orchestrator-loop…" pointer) + the skills' inline enforcement. In a fresh session, ask
   *"what do you do with a too-good-to-be-true result?"* — the answer must be, in substance,
   *distrust it, reproduce it, find the data bug.* If it isn't, the app-profile pointer isn't
   in place.
4. **Only then flip to public.** Either:
   - CLI/`gh`: `gh repo edit <owner>/orchestrator-loop --visibility public`
   - Browser: GitHub → repo → Settings → General → Danger Zone → Change visibility → Public.
5. **Smoke-test the public path:** from a different account (or ask a friend), add
   `<owner>/orchestrator-loop` and confirm it installs and the skills appear.

## Versioning when you change the plugin

Bump `version` in **both** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
(keep them in sync), commit, and push. Re-package the `.plugin` if you distribute the file
directly. Installers pick up the new version on their next add/update.

## Repackaging the `.plugin` file (optional, for direct upload)

```
cd <repo> && rm -f /tmp/orchestrator-loop.plugin \
  && zip -r -X /tmp/orchestrator-loop.plugin . -x '*/.git/*' '.git/*' '*.plugin' '*.DS_Store' \
  && echo "built /tmp/orchestrator-loop.plugin"
```
The repo is the source of truth; the `.plugin` is just a convenience artifact.
