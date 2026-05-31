# Connectors

## How tool references work

Plugin files reference external tools **by category** using a `~~category` placeholder
(e.g. `~~database`, `~~hosting`). The framework is tool-agnostic: it describes the
orchestration workflow in terms of categories, and you map each category to the concrete
tool you actually use. Wire these up once when you install, in your app-profile.

## Connectors for this plugin

| Category | Placeholder | Options (pick one) |
|---|---|---|
| Executor (coding agent) | `~~executor` | Claude Code (headless / Desktop Commander), or another coding agent |
| Version control | `~~vcs` | GitHub, GitLab, Bitbucket |
| CI / build gate | `~~ci` | GitHub Actions, GitLab CI, CircleCI |
| Database / datastore | `~~database` | Supabase, Postgres, PlanetScale, MySQL |
| Hosting / deploy | `~~hosting` | Vercel, Netlify, Fly, Render |
| DNS / edge | `~~dns` | Cloudflare, Route 53 |
| Project tracker | `~~project-tracker` | Linear, Jira, Asana, GitHub Issues |
| Browser QA | `~~browser-qa` | Claude-in-Chrome, Playwright |

Not every category is required — only wire up the ones your app uses. At minimum the loop
needs `~~executor` (to hand work to), `~~vcs` (to commit/track), and `~~browser-qa` (to
validate UX). `~~ci` is what makes the constitution's invariants *enforced* rather than
aspirational (the architect-review skill leans on it). Database / hosting / DNS /
project-tracker are wired as your stack needs them.

## Where you declare your mappings

Record your concrete tools in your **app-profile** (your `CLAUDE.md` or equivalent), e.g.:

```
~~executor      = Claude Code (headless, via Desktop Commander)
~~vcs           = GitHub (org/repo)
~~database      = Supabase (project ref)
~~hosting       = Vercel (team/project)
~~browser-qa    = Claude-in-Chrome
```
