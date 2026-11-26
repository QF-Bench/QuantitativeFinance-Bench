#!/usr/bin/env python3
"""Offline lexical inventory for reviewer navigation, not an attribution rule.

A detected formula, citation or schema does not establish correctness, adequate
specification or agent fault. Missing lexical matches do not establish ambiguity.
"""

from __future__ import annotations
import json
import argparse
from review_common import sha256
import re
from pathlib import Path
from collections import defaultdict

MONTH_NAMES = {
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept",
    "Oct", "Nov", "Dec",
}

# 1. Author-Year cites — accept "(Surname YYYY)" or "Surname (YYYY)" or
#    "Surname & Surname (YYYY)"; reject month-name surnames.
RE_AUTHOR_YEAR = re.compile(
    r"\b([A-Z][a-zA-Zöóáé\-]{2,})"
    r"(?:\s*(?:and|,|&|-|\s)\s*[A-Z][a-zA-Zöóáé\-]{2,})*"
    r"\s*\(?\s*((?:19|20)\d{2})\s*\)?",
)

RE_SECTION_REF = re.compile(
    r"\b(?:Vol(?:ume)?\.?\s*[IVX]+\s*§[\d\.]+|"
    r"Chapter\s+\d+|Ch\.\s*\d+|"
    r"§\s*\d+(?:\.\d+)*|"
    r"Section\s+\d+(?:\.\d+)*|"
    r"App(?:endix)?\.?\s*[A-Z]?(?:\.\d+)*|"
    r"Eq(?:uation)?\.?\s*\(?\d+(?:[\.\-]\d+)*\)?|"
    r"Problem(?:s)?\s+\d+(?:[\-,\s\d]+)?)\b"
)

RE_CROSS_FILE = re.compile(
    r"(?:see\s+|in\s+|from\s+|read\s+|load\s+|defined in\s+|provided in\s+|reference[sd]?\s+to?\s+)"
    r"`?[/\w\-]*?\.(?:md|json|csv|parquet|yaml|yml|toml|py|txt)`?",
    re.IGNORECASE,
)

RE_FILENAME_BARE = re.compile(
    r"`([\w\-]+\.(?:md|json|csv|parquet|yaml|yml|toml))`"
)

RE_TEX_INLINE = re.compile(r"\$[^\$\n]{2,200}\$")
RE_TEX_DISPLAY = re.compile(r"\$\$[\s\S]{2,500}?\$\$")
RE_TEX_BACKSLASH = re.compile(
    r"\\(?:Phi|Psi|frac|sqrt|sum|int|prod|alpha|beta|gamma|delta|epsilon|"
    r"lambda|mu|nu|rho|sigma|tau|chi|omega|theta|kappa|pi|hat|bar|tilde|"
    r"left|right|cdot|times|exp|log|ln|max|min|partial|nabla|infty)"
)

RE_LIB_KWARG = re.compile(
    r"\b(?:scipy|numpy|pandas|np|pd|sp|sm|statsmodels|sklearn|skl|"
    r"arch|filterpy|cvxpy|QuantLib|ql)\.\w+(?:\.\w+)*\([^\)]*=[^\)]*\)"
)

RE_KWARG_PIN = re.compile(
    r"\b(ddof|kind|keep|method|how|dtype|fill_method|errors|sort|"
    r"fill_value|axis|order|arg|p0|tol|atol|rtol|maxiter|x0|"
    r"floc|fscale|f0|loc|scale|biased|unbiased)\s*=\s*['\"]?[\w\.\-\+]+['\"]?"
)

RE_DAYCOUNT_STRONG = re.compile(
    r"\b(?:ACT/360|ACT/365(?:F)?|ACT/ACT|30/360|30E/360)\b"
)
RE_DAYCOUNT_WORD = re.compile(
    r"\b(?:day[- ]count|actual/360|actual/365)\b",
    re.IGNORECASE,
)

RE_PARAM_PIN = re.compile(
    r"\b(?:m|n|N|k|K|ν|nu|df|shape|scale|lambda|lag|window|alpha|"
    r"tol(?:erance)?|seed|kappa|theta|sigma|rho|halflife|bandwidth)\s*"
    r"[=≈]\s*\-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
)

RE_ANNUALIZATION = re.compile(
    r"(?:×|\*)\s*(?:sqrt\s*\(\s*)?(?:252|365|260|250|12)\b"
    r"|/\s*(?:252|365|260|12)\b"
    r"|sqrt\s*\(\s*(?:252|365)\s*\)"
    r"|annuali[sz](?:ed?|ation)"
    r"|trading\s+days?\s+per\s+year",
    re.IGNORECASE,
)

RE_SOLVER = re.compile(
    r"\b(?:SLSQP|Nelder-Mead|L-BFGS-B|Powell|trust-constr|minimize_scalar|"
    r"brentq|newton|bisect|fsolve|root_scalar|differential_evolution|"
    r"basinhopping|fmin)\b"
)

EPONYM_LIST = [
    r"Newey[\- ]West", r"Acerbi[\- ]Tasche", r"Corrado",
    r"Black[\- ]Scholes(?:[\- ]Merton)?", r"Heston", r"Bates", r"Vasicek",
    r"Cox[\- ]Ingersoll[\- ]Ross|CIR\b", r"Hull[\- ]White", r"Dupire",
    r"Engle\b", r"DCC[\- ]GARCH", r"GARCH", r"EGARCH", r"GJR[\- ]GARCH",
    r"Barone[\- ]Adesi(?:[\- ]Whaley)?|BAW\b", r"Geske", r"Margrabe", r"Kirk",
    r"Levy[\- ]Curran", r"Crank[\- ]Nicolson", r"Rannacher",
    r"Black[\- ]Litterman", r"Baum[\- ]Welch",
    r"Hamilton(?:\s+regime[\- ]switching)?", r"Kalman",
    r"Fama[\- ]French", r"Carhart", r"Brinson",
    r"Sharpe", r"Jensen", r"Sortino", r"Treynor", r"Information ratio",
    r"Markowitz", r"CAPM", r"APT",
    r"Vasicek\s+ASRF|ASRF", r"Gordy", r"CreditMetrics", r"CreditRisk\+",
    r"Merton(?:\s+jump)?", r"Bachelier", r"Levenberg[\- ]Marquardt",
    r"Garman[\- ]Klass", r"Yang[\- ]Zhang", r"Parkinson", r"Rogers[\- ]Satchell",
    r"Bipower variation|BNS\b", r"Acerbi", r"Christoffersen", r"Kupiec",
    r"Smith\b", r"Cornish[\- ]Fisher", r"Box[\- ]Cox", r"Jamshidian",
    r"Brace[\- ]Gatarek[\- ]Musiela|BGM", r"Heath[\- ]Jarrow[\- ]Morton|HJM",
    r"LIBOR market model|LMM", r"Schmukler",
    r"Christensen[\- ]Diebold[\- ]Rudebusch", r"Nelson[\- ]Siegel(?:[\- ]Svensson)?",
    r"Diebold[\- ]Li", r"Andersen|HAR[\- ]RV", r"Bollinger",
]
RE_EPONYM = re.compile(r"\b(" + "|".join(EPONYM_LIST) + r")\b", re.IGNORECASE)

RE_DIST_PARAM = re.compile(
    r"\b(?:degrees?\s+of\s+freedom|df\s*=|nu\s*=|ν\s*=|"
    r"shape\s*=|scale\s*=|location\s*=|loc\s*=)\s*\-?\d+(?:\.\d+)?",
    re.IGNORECASE,
)

# NEW: code-fence pseudocode block detector
# Markdown ``` fences. Inside a fence, look for math operators or assignments.
RE_CODEFENCE = re.compile(r"```([a-zA-Z]*)\n([\s\S]*?)```", re.MULTILINE)
RE_PSEUDO_MATH = re.compile(
    r"(?:[a-zA-Z_][\w]*\s*=\s*[a-zA-Z(]"
    r"|Σ|∑|∫|sqrt\s*\("
    r"|max\s*\([^)]*,\s*[^)]*\)"
    r"|N\s*\(\s*d[12]"
    r"|exp\s*\(|ln\s*\(|log\s*\("
    r"|×|·"
    r"|\*\*\s*\d"
    r"|/\s*sqrt\("
    r"|abs\s*\(|min\s*\("
    r"|d[12]\s*=\s*\()"
)


def scan_codefences(text: str) -> tuple[int, int, list[str]]:
    """Return (n_fences, n_with_pseudo_math, sample_languages)."""
    fences = list(RE_CODEFENCE.finditer(text))
    n_pm = 0
    langs = []
    for m in fences:
        lang, body = m.group(1), m.group(2)
        langs.append(lang or "(none)")
        if RE_PSEUDO_MATH.search(body):
            n_pm += 1
    return len(fences), n_pm, sorted(set(langs))


# Pattern #9 (added v3.2.2-pat9): Schema-key list in prose.
# Catches tasks like etf-overlap-redemption-pressure that enumerate required
# JSON keys / CSV columns inline. The earlier 8-pattern set missed these,
# leading to mis-classification as "no-matched-cues" regime → task_side. Pattern #9
# records schema wording for inspection; it does not route blame.
RE_SCHEMA_PROSE_TRIGGER = re.compile(
    r"(?:must contain (?:exactly )?(?:these |the following )?(?:keys|fields):|"
    r"must be (?:an )?objects? with scalar values for|"
    r"with (?:exactly |these )?(?:these |the following )?top[- ]level keys:|"
    r"JSON object with exactly|"
    r"keyed by\s+\w+\.?\s*Each\b|"
    r"Each (?:scenario|row|key|entry|block) (?:must|should) (?:contain|have))",
    re.IGNORECASE,
)
RE_NUMBERED_COLUMN_LIST = re.compile(
    r"(?:^|\n)\s*Columns:\s*\n(?:\s*\d+\.\s+`?\w[\w_]*`?\s*\n){3,}",
)
# Inline list of identifier-style names: ≥3 backticked keys after a key-list trigger
RE_INLINE_KEY_LIST = re.compile(
    r"(?:keys?|fields?|columns?):\s*"
    r"(?:`\w[\w_]*`(?:\s*,\s*|\s+and\s+)){2,}`\w[\w_]*`",
    re.IGNORECASE,
)


def scan_schema_keys(text: str) -> tuple[int, list[str]]:
    """Return (n_hits, sample_matches) for pattern #9.

    Hits when prose lists ≥3 schema keys/columns explicitly.
    Three sub-detectors:
      - prose trigger ("must contain these keys", "JSON object with exactly")
      - numbered Columns: list with ≥3 entries
      - inline backticked-key list of length ≥3 after a key/field/columns: trigger
    """
    hits = []
    hits += [m.group(0)[:100] for m in RE_SCHEMA_PROSE_TRIGGER.finditer(text)]
    hits += [m.group(0)[:100] for m in RE_NUMBERED_COLUMN_LIST.finditer(text)]
    hits += [m.group(0)[:100] for m in RE_INLINE_KEY_LIST.finditer(text)]
    return len(hits), hits[:5]


# ---------------------------------------------------------------------------

PATTERNS = [
    ("author_year",     RE_AUTHOR_YEAR),
    ("section_ref",     RE_SECTION_REF),
    ("cross_file",      RE_CROSS_FILE),
    ("filename_bare",   RE_FILENAME_BARE),
    ("tex_inline",      RE_TEX_INLINE),
    ("tex_display",     RE_TEX_DISPLAY),
    ("tex_backslash",   RE_TEX_BACKSLASH),
    ("lib_kwarg_call",  RE_LIB_KWARG),
    ("kwarg_pin",       RE_KWARG_PIN),
    ("daycount_strong", RE_DAYCOUNT_STRONG),
    ("daycount_word",   RE_DAYCOUNT_WORD),
    ("param_pin",       RE_PARAM_PIN),
    ("annualization",   RE_ANNUALIZATION),
    ("solver",          RE_SOLVER),
    ("eponym",          RE_EPONYM),
    ("dist_param",      RE_DIST_PARAM),
]


def is_date_phrase(matched: str) -> bool:
    parts = matched.split()
    if not parts:
        return False
    return any(p.rstrip(",") in MONTH_NAMES for p in parts)


def scan_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    results = {kind: [] for kind, _ in PATTERNS}
    for i, line in enumerate(lines, 1):
        for kind, regex in PATTERNS:
            for m in regex.finditer(line):
                snippet = m.group(0).strip()
                if kind == "author_year" and is_date_phrase(snippet):
                    continue
                if 0 < len(snippet) < 200:
                    results[kind].append((i, snippet))

    n_fences, n_pseudo_math, fence_langs = scan_codefences(text)
    n_schema_keys, schema_key_examples = scan_schema_keys(text)

    counts = {k: len(v) for k, v in results.items()}
    counts["code_fences"] = n_fences
    counts["fences_with_pseudo_math"] = n_pseudo_math
    counts["schema_key_list"] = n_schema_keys

    distinct = {
        "author_year": sorted({s for _, s in results["author_year"]}),
        "eponym":      sorted({s.lower() for _, s in results["eponym"]}),
        "filename_bare": sorted({s for _, s in results["filename_bare"]}),
        "daycount_strong": sorted({s.upper() for _, s in results["daycount_strong"]}),
        "solver":      sorted({s for _, s in results["solver"]}),
        "fence_langs": fence_langs,
    }
    return {
        "path": str(path),
        "sha256": sha256(path),
        "interpretation": "lexical navigation only; no correctness or attribution verdict",
        "n_lines": len(lines),
        "counts": counts,
        "distinct": distinct,
        "first_examples": {k: v[:3] for k, v in results.items() if v},
    }


def regime(scan: dict) -> tuple[str, list[str]]:
    """Return a lexical grouping and observed cue list, never a verdict."""
    c = scan["counts"]
    ev = []

    has_inline_math = (c["tex_inline"] + c["tex_display"]) > 0
    has_param_pin = (c["param_pin"] + c["kwarg_pin"] + c["lib_kwarg_call"]
                     + c["dist_param"]) > 0
    has_daycount_strong = c["daycount_strong"] > 0
    has_section_ref = c["section_ref"] > 0
    has_cross_file = (c["cross_file"] + c["filename_bare"]) > 0
    has_eponym = c["eponym"] > 0
    has_author = c["author_year"] > 0
    has_pseudocode = c["fences_with_pseudo_math"] > 0
    has_schema_keys = c.get("schema_key_list", 0) > 0   # pattern #9

    if has_inline_math: ev.append("inline-math")
    if has_param_pin: ev.append("param-pin")
    if has_daycount_strong: ev.append("daycount-strong")
    if has_section_ref: ev.append("section-ref")
    if has_cross_file: ev.append("cross-file")
    if has_eponym: ev.append("eponym")
    if has_author: ev.append("author-year")
    if has_pseudocode: ev.append("pseudocode-fence")
    if has_schema_keys: ev.append("schema-key-list")    # pattern #9

    # Strong-authoring score
    score = (
        2 * has_inline_math +
        2 * has_param_pin +
        2 * has_daycount_strong +
        3 * has_pseudocode +    # pseudocode is the strongest formula authoring
        2 * has_schema_keys +   # pattern #9: schema/output authoring
        1 * has_section_ref +
        1 * has_cross_file
    )
    if score >= 3:
        return "explicit-cues", ev
    if has_eponym or has_author or has_section_ref or has_cross_file:
        return "reference-cues", ev
    return "no-matched-cues", ev


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-root", required=True)
    parser.add_argument("--pr-instructions")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    tasks_dir = Path(args.tasks_root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for d in sorted(tasks_dir.iterdir()):
        if not d.is_dir():
            continue
        instr = d / "instruction.md"
        if not instr.exists():
            continue
        scan = scan_file(instr)
        scan["task"] = d.name
        scan["source"] = "canonical"
        scan["regime"], scan["evidence"] = regime(scan)
        rows.append(scan)

    for f in sorted((Path(args.pr_instructions).glob("*.md") if args.pr_instructions else [])):
        scan = scan_file(f)
        scan["task"] = f.stem
        scan["source"] = "pr"
        scan["regime"], scan["evidence"] = regime(scan)
        rows.append(scan)

    print(f"Scanned {len(rows)} tasks")

    regime_counts = defaultdict(int)
    pattern_totals = defaultdict(int)
    pattern_task_count = defaultdict(int)
    for r in rows:
        regime_counts[r["regime"]] += 1
        for k, v in r["counts"].items():
            pattern_totals[k] += v
            if v > 0:
                pattern_task_count[k] += 1

    summary = {
        "n_tasks": len(rows),
        "regime_counts": dict(regime_counts),
        "pattern_total_hits": dict(pattern_totals),
        "tasks_with_pattern": dict(pattern_task_count),
    }

    with open(out_dir / "scan_results_v2.json", "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=2)

    print(json.dumps(summary, indent=2))

    print("\n=== Per-task regime ===")
    for r in sorted(rows, key=lambda x: (x["regime"], x["task"])):
        ev_str = ",".join(r["evidence"])
        print(f"{r['regime']:18s} {r['task']:55s} {ev_str}")


if __name__ == "__main__":
    main()
