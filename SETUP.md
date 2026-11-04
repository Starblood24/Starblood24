# STARBLOOD.OS — Setup & maintenance

A custom, no-subscription GitHub profile README. It uses your own SVGs instead of third-party stats endpoints. **Nothing has been published by the local build.**

## What's inside

- `README.md`: the actual GitHub-profile README, containing relative image links.
- `assets/hero.svg`, `assets/featured_typr.svg`, `assets/stack.svg` (+ matching `_mobile.svg`): hand-built vector illustrations.
- `assets/avatar_ascii.svg`: **genuine colored Unicode character art** derived from `source/avatar_reference.jpg` (your Pompompurin GitHub photo), not an embedded bitmap.
- `assets/avatar_ascii_detailed.svg`: alternate, larger colored ASCII artwork from the previous design stage.
- `assets/pompompurin_idle.gif`: a gentle nine-frame blink in a four-second loop; `pompompurin_idle_poster.png` is the static version. Only the eye regions move. `source/idle_base.png` preserves the original rasterized character art for reproducible animation builds.
- `assets/stats.svg`, `assets/contributions.svg`, `assets/languages.svg` (plus mobile variants): automatically generated GitHub panels. They currently show **pending** states, not made-up values.
- `scripts/collect_stats.py`: fetches live GitHub data using a token; Python standard library only.
- `scripts/render_assets.py`: renders the GitHub panels; Python standard library only.
- `scripts/build_art.py`: rebuilds the static art and GIF from the original image; requires Pillow locally.
- `.github/workflows/update-profile.yml`: daily GitHub Actions automation + manual trigger.
- `preview/index.html`, `preview/preview.png`, `preview/mobile.png`: local HTML preview and browser screenshots at 1280px / 390px. The preview contains an explicit **DEMO DATA** fixture (`preview/demo`) so no sample metric is represented as your real number.
- `tests`: offline unit tests.

## 1. Check the local preview first

Open `preview/index.html` in a browser (you can double-click the file). The page is a themed local preview, not GitHub's Markdown renderer.

## 2. Create your profile repository (only when ready)

On GitHub, create a **public** repository named exactly `Starblood24` under account `Starblood24`. GitHub recognizes the special repository `Starblood24/Starblood24` and renders its root `README.md` on your profile. Do not create a README using the GitHub wizard if you intend to upload this one unchanged.

Upload the complete **contents** of this package to the repository root, preserving hidden `.github/workflows/`. Alternatively, clone your new empty repository and copy the files into it (not the outer `STARBLOOD.OS` folder). Commit and push only after reviewing the preview and graphics.

## 3. Enable the live refresh

Open the new repository on GitHub → **Actions** → **Refresh STARBLOOD.OS profile metrics** → **Run workflow**. The workflow uses GitHub's automatically available `GITHUB_TOKEN`; you do not need to put a personal access token in the repository or code.

The first upload to `main` also starts the workflow automatically. Later pushes run it only when the workflow, statistics generator, renderer or tests change. Daily generated data commits do not match these path filters.

**Repository Settings → Actions → General → Workflow permissions:** ensure **Read and write permissions** are allowed if your repository/org policy overrides the workflow's `contents: write` permission. The workflow commits only the generated SVG panels (desktop and mobile) and `data/stats.json` when something changes.

Scheduled workflows use UTC (`05:17` UTC configured), can be delayed, and GitHub may disable scheduled workflows after 60 days of public-repo inactivity. The manual `workflow_dispatch` trigger remains available. Don't treat the daily refresh as real-time streaming.

## 4. Refresh stats manually (optional)

With Python 3.11+ installed:

```bash
# Bash / macOS / Linux
export GITHUB_TOKEN='YOUR_TOKEN_HERE'    # locally only; never check it in
python scripts/collect_stats.py --username Starblood24 --output data/stats.json
python scripts/render_assets.py --data data/stats.json --out assets
```

Or in PowerShell:

```powershell
$env:GITHUB_TOKEN = "YOUR_TOKEN_HERE"  # only in your current PowerShell process
python scripts/collect_stats.py --username Starblood24 --output data/stats.json
python scripts/render_assets.py --data data/stats.json --out assets
Remove-Item Env:GITHUB_TOKEN
```

The collector refuses to run without a token and **leaves existing stats files unchanged** on failure. GitHub's default workflow token usually provides public GraphQL access in a profile repository. On access errors, inspect the workflow logs and verify that your account/repository's permissions allow GraphQL queries and commits. Never print or commit tokens.

The workflow runs offline regression tests before collecting data, pins its existing action versions to verified commit hashes, and checks out the default branch even for manual runs. Write access is scoped to the generation job; its final commit stages only the seven generated data/SVG files. Keep the action pins maintained when reviewing future updates. No workflow was triggered as part of this local cleanup.

## 5. Rebuild the pixel-character art

```bash
python -m pip install Pillow
python scripts/build_art.py
```

The artwork source is `source/avatar_reference.jpg`. `config/theme.json` stores the intended palette. The header and GIF are generated locally; the daily workflow doesn't need Pillow.

The GIF is built from `source/idle_base.png`, preserving the original glyph rasterization. If you replace that portrait, recalibrate `EYE_BOXES` in `scripts/build_art.py`. To rebuild only the GIF, run `python -c "import sys; sys.path.insert(0, 'scripts'); import build_art; build_art.build_gif()"`.

To regenerate browser screenshots, use Node.js, Google Chrome and the optional Playwright package (`npm install --no-save playwright`), then run `node scripts/build_preview.cjs`. The script captures the actual HTML instead of maintaining a separate mock layout. It checks image loading, mobile source selection, reduced motion and horizontal overflow at 320, 390, 640 and 1280px. These tools are only for local preview capture; neither the daily workflow nor viewing `preview/index.html` needs them. CairoSVG is no longer required.

## 6. Run offline tests

```bash
python -m unittest discover -s tests -v
```

To regenerate the purely simulated preview panels without touching production stats:

```bash
python scripts/render_assets.py --data tests/fixtures/demo_stats.json --out preview/demo
```

## Decisions & constraints

- The API aggregates **owned public repositories**, stars/forks received, GraphQL annual contribution calendar, and languages of **non-fork, non-archived, public repositories** weighted by GitHub-reported bytes. It requests up to 100 languages per repository and rejects further language pages rather than silently reporting incomplete proportions.
- GraphQL's contribution totals may include private contribution counts depending on GitHub visibility settings, but **no private repository names** are read or displayed.
- No third-party hosted widget, tracker, website, paid service, or external font is required.
- GitHub README rendering sanitizes HTML/CSS/JS; animation is a GIF and graphs are SVG assets, not browser scripts.
- SVGs use normal text/fonts; colors and layout work in both GitHub themes. Some text positioning can vary slightly with system fallback fonts.
- The HTML preview and README use a `<picture>` source for `prefers-reduced-motion`, selecting the static poster. GitHub's own sanitizer/renderer has not been tested live; for guaranteed motion-free display, replace the GIF reference with `assets/pompompurin_idle_poster.png`.
- Pompompurin is a Sanrio character. This pack does not claim ownership of that character or grant third-party rights to the artwork. Review usage rights before public reuse, especially commercial reuse.

## Manual publishing checklist

- [ ] Review `preview/index.html` and `preview/preview.png`.
- [ ] Confirm your displayed name/intro in `README.md`.
- [ ] Confirm copyright/usage rights for your Pompompurin illustration.
- [ ] Create `Starblood24/Starblood24` (public).
- [ ] Push reviewed files to the new profile repo, including `.github`.
- [ ] Run the workflow manually and check stats are real rather than pending.
- [ ] Check the README on desktop/mobile and dark/light GitHub themes.

This local bundle **does not create, update, or publish any GitHub repository**.
