#!/usr/bin/env python3
"""Generate docs/TASK_NAMES.md — a plain-language decoder for QF-Bench task identifiers.

Everything is read from the repo itself: the H1 of each tasks/<id>/instruction.md and the
metadata block of tasks/<id>/task.toml. No hand-written descriptions.
"""
import re, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent  # repo root
TASKS = ROOT / "tasks"

# Reading aid only: raw `category` values in task.toml are free-form and include near-duplicates
# (derivatives-pricing / derivatives / pricing / derivatives_pricing). We group them for navigation
# and always show the raw value alongside, so nothing is hidden or silently renamed.
GROUP = {
    "derivatives pricing": {"derivatives-pricing", "derivatives", "pricing", "derivatives_pricing",
                            "fx-pricing", "interest-rate-derivatives", "volatility-modeling",
                            "stochastic-processes"},
    "fixed income & rates": {"fixed-income", "cross-currency-rates", "fixed-income-nlp"},
    "risk management": {"risk-management", "risk-modeling", "extreme-value-theory"},
    "credit": {"credit-risk", "credit-analysis", "dependence-modeling"},
    "factor research": {"factor-research", "factor-models", "predictive-alpha-modeling",
                        "cross-sectional-strategies"},
    "systematic strategies & backtesting": {"backtesting", "strategy", "fx-strategy"},
    "execution & microstructure": {"execution"},
    "digital assets": {"crypto"},
    "portfolio & attribution": {"portfolio-analysis", "performance-attribution",
                                "cross-asset-analysis", "statistical-analysis"},
    "cross-domain & data engineering": {"cross-domain", "tool-using", "debug-migration",
                                        "event-driven-analysis, data-processing"},
}
LOOKUP = {v: k for k, vs in GROUP.items() for v in vs}

rows = []
for d in sorted(TASKS.iterdir()):
    if not d.is_dir():
        continue
    toml = (d / "task.toml").read_text() if (d / "task.toml").exists() else ""
    ins = (d / "instruction.md").read_text() if (d / "instruction.md").exists() else ""
    s = lambda k: (re.search(rf'{k}\s*=\s*"([^"]*)"', toml) or [None, None])[1]
    f = lambda k: (re.search(rf'{k}\s*=\s*([0-9.]+)', toml) or [None, None])[1]
    # first H1 that is not the canary banner (several files open with it)
    SECTION = {"objective","files","task","overview","background","deliverables",
               "input data","inputs","data","goal","task requirements","required cleaning",
               "conventions to respect","data cleaning and session construction"}
    def pick(hs, strict=False):
        for h in hs:
            h = re.sub(r"<!--.*?-->", "", h).strip()
            if not h or re.search(r"BENCHMARK DATA|canary|GUID", h, re.I):
                continue
            if h.lower().rstrip(":") in SECTION:
                continue
            if strict and (re.match(r"^[0-9]", h) or "`" in h or "/" in h):
                continue  # fallback pass only: skip numbered/file headings
            return re.sub(r"^Task:\s*", "", h).strip()
        return None
    title = pick(re.findall(r"^#\s+(.+)$", ins, re.M))          # H1 first
    if not title:
        title = d.name.replace("-", " ").title()                # last resort
    cat = s("category")
    rows.append(dict(task=d.name, title=title or "—", cat=cat or "—",
                     group=LOOKUP.get(cat or "", "uncategorised"),
                     diff=(s("difficulty") or "—").replace("_", " "),
                     exp=f("expert_time_estimate_min"), jun=f("junior_time_estimate_min")))

by_group = collections.defaultdict(list)
for r in rows:
    by_group[r["group"]].append(r)
order = [g for g in GROUP if g in by_group] + [g for g in sorted(by_group) if g not in GROUP]

out = [
    "# Task identifiers, decoded", "",
    "QF-Bench task IDs are compressed descriptions — `13f-amendment-aware-crowding`,",
    "`mtm-xccy-basis-desk`, `regime-riskparity-cvar`. They are readable to a practitioner and",
    "opaque to everyone else, which makes the per-task tables hard to navigate without a key.",
    "",
    f"This page lists all {len(rows)} tasks with the plain-language title each task's",
    "`instruction.md` already carries, grouped by domain so that readers can find the area they",
    "know. Times are the author-declared estimates in `task.toml` (`expert_time_estimate_min` /",
    "`junior_time_estimate_min`) — development-stage estimates, not measurements under exam",
    "conditions. Difficulty here is the author's a-priori label in `task.toml`; it is *not* the",
    "empirical difficulty tier used for reporting, which is derived from frontier-model pass rates.",
    "",
    "Generated from the repository (`instruction.md` H1 + `task.toml`); see `docs/` for how to",
    "regenerate. Domain grouping is a reading aid — the raw `category` value is shown for each task.",
    "",
]
for g in order:
    rs = sorted(by_group[g], key=lambda r: r["task"])
    out += [f"## {g.title()} ({len(rs)})", "",
            "| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |",
            "|---|---|---|---|---|"]
    for r in rs:
        fmt = lambda v: f"{float(v):g}"
        t = f"{fmt(r['exp'])} / {fmt(r['jun'])}" if r["exp"] and r["jun"] else "—"
        out.append(f"| `{r['task']}` | {r['title']} | {r['diff']} | {t} | `{r['cat']}` |")
    out.append("")

path = ROOT / "docs" / "TASK_NAMES.md"
path.write_text("\n".join(out))
print(f"wrote {path}  ({len(rows)} tasks, {len(by_group)} groups)")
print("uncategorised:", [r["task"] for r in rows if r["group"] == "uncategorised"])
