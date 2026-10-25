"""Build the README figures from the committed CSVs (and, where no CSV holds the number, from the
research log; those values are marked LOG below). Run from the repository root:

    python scripts/make_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "figures"
OUT.mkdir(exist_ok=True)

# Reference palette (light mode)
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, BLUE_LIGHT, GREY = "#2a78d6", "#86b6ef", "#c9c8c2"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK, "axes.edgecolor": GRID, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def csv(path):
    return pd.read_csv(DATA / path, dtype=str, keep_default_na=False)


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def hbar(ax, labels, values, colors, texts, xmax, text_at=None):
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=colors, height=0.6, edgecolor=SURFACE, linewidth=2)
    for yi, v, t, at in zip(y, values, texts, text_at or values):
        ax.text(at + xmax * 0.015, yi, t, va="center", fontsize=9, color=INK)
    ax.set_yticks(list(y), labels)
    ax.set_xlim(0, xmax * 1.35)
    style(ax)


# ---------------------------------------------------------------- 1. coverage vs precision by source
endole = csv("hmrc_checks/urma_endole_30.csv")
endole_own = endole[endole.categorie.isin(["confirmat", "incert"])]            # own VAT shown on Endole
cc1 = csv("results/cc_pas1_v3_toate.csv")
cc1_retry = csv("results/cc_pas1_v3_retry.csv")
cc1 = pd.concat([cc1[~cc1.company_number.isin(cc1_retry.company_number)], cc1_retry])
cc1_found = (cc1.tva_gasit_cc == "True").sum()
cc2 = csv("hmrc_checks/cc_pas2_rezultat_hmrc.csv")
fat = csv("results/cc_fat_rezultat_firme.csv")
fat_n = (fat.stare != "EROARE_INDEX").sum()
fat_hmrc = csv("hmrc_checks/hmrc_transcriere_fat.csv")
FAT_EXACT, FAT_GROUP = 3, 1          # LOG (Step 9): attribution by HMRC name, exact company vs group entity
REG_ROWS, FAT_SUPPLIERS = 11113 + 5669, 1480   # LOG (Steps 7, 8)

sources = ["Endole (aggregator)", "Common Crawl, from company\n(biased sample)", "Common Crawl, from number\n(WET files)",
           "Common Crawl, from company\n(Find a Tender sample)", "Public spending registers", "Find a Tender (OCDS)"]
cov = [len(endole_own) / len(endole), cc1_found / len(cc1), None, FAT_EXACT / fat_n, 0, 0]
cov_txt = [f"{len(endole_own)}/{len(endole)} companies", f"{cc1_found}/{len(cc1)} companies", "not measured",
           f"{FAT_EXACT}/{fat_n} exact company\n(+{FAT_GROUP} group entity = {FAT_EXACT + FAT_GROUP}/{fat_n})",
           f"0 in {REG_ROWS:,} rows", f"0 in {FAT_SUPPLIERS:,} supplier appearances"]
endole_valid = (endole_own.rezultat_hmrc == "Valid").sum()
cc2_valid = (cc2.hmrc_valid == "da").sum()
fat_valid = (fat_hmrc.hmrc_valid == "da").sum()
prec = [endole_valid / len(endole_own), 1.0, cc2_valid / len(cc2), fat_valid / len(fat_hmrc), None, None]
prec_txt = [f"{endole_valid}/{len(endole_own)} valid at HMRC", f"{cc1_found}/{cc1_found}, 0 false positives",
            f"{cc2_valid}/{len(cc2)} valid at HMRC", f"{fat_valid}/{len(fat_hmrc)} valid at HMRC\n({FAT_EXACT}/{len(fat_hmrc)} the company itself)",
            "no VAT numbers", "no VAT numbers"]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True, gridspec_kw={"wspace": 0.45})
for ax, vals, txt, title in ((a1, cov, cov_txt, "Coverage: VAT found for the company"),
                             (a2, prec, prec_txt, "Precision: numbers found that are valid")):
    v = [x * 100 if x is not None else 0 for x in vals]
    at = list(v)
    if ax is a1:
        at[3] = (FAT_EXACT + FAT_GROUP) / fat_n * 100          # label after the group-entity extension
    hbar(ax, sources, v, [BLUE if x is not None else GREY for x in vals], txt, 100, at)
    ax.set_xlim(0, 160)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_title(title, loc="left", fontsize=11, color=INK)
# group-entity extension on the Find a Tender coverage bar
a1.barh([2], [FAT_GROUP / fat_n * 100], left=[FAT_EXACT / fat_n * 100], color=BLUE_LIGHT, height=0.6,
        edgecolor=SURFACE, linewidth=2)
fig.suptitle("Coverage and precision by source", x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.text(0.01, 0.005, "Small samples (12–30 companies; 2–31 numbers checked): read as rough levels, not exact rates. Sources: data/ CSVs and docs/research_log.md.",
         fontsize=8, color=INK2)
fig.savefig(OUT / "coverage_precision_by_source.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- 2. funnel, Common Crawl Step 2
st = pd.read_csv(DATA / "results/cc_pas2_statistici.csv")
cand = csv("results/cc_pas2_candidati.csv")
ok = cand[cand.checksum_ok == "True"]
ver = csv("hmrc_checks/cc_pas2_verificare_hmrc.csv")
ATTRIBUTED = 30                         # LOG (Step 6): valid numbers attributed to one CH company via HMRC name
stages = ["Regex matches", "Pass mod-97 checksum", "Unique numbers", "Checked at HMRC\n(random 31 of 108)",
          "Valid at HMRC", "Attributed to one\nCompanies House company"]
vals = [len(cand), len(ok), ver.vat.nunique(), (ver.hmrc_valid != "").sum(), (ver.hmrc_valid == "da").sum(), ATTRIBUTED]
fig, ax = plt.subplots(figsize=(8.5, 4.2))
colors = [BLUE, BLUE, BLUE, BLUE_LIGHT, BLUE, BLUE]
hbar(ax, stages, vals, colors, [f"{v:,}" for v in vals], max(vals))
ax.set_title(f"Common Crawl Step 2: {int(st.pagini.sum()):,} pages in 3 random WET files (CC-MAIN-2026-39)",
             loc="left", fontsize=11)
fig.text(0.01, -0.02, "The HMRC check is a random sample (light bar), not a loss in the pipeline. "
         "Source: data/results, data/hmrc_checks; attribution from docs/research_log.md.", fontsize=8, color=INK2)
fig.savefig(OUT / "funnel_cc_step2.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- 3. funnel, Find a Tender sample
sample = csv("samples/fat_esantion_30_v3.csv")
dom = sample.domeniu_verificat_manual
stages = ["Find a Tender sample", "Domain checked: yes\nor not verifiable", "Run with a result\n(1 persistent index error)",
          "Domain in the crawl", "Company with a VAT number\nfound (5 numbers)", "VAT of the exact company"]
vals = [len(sample), dom.isin(["da", "neverificat"]).sum(), fat_n, (fat[fat.stare != "EROARE_INDEX"].stare != "ABSENT_DIN_CRAWL").sum(),
        (fat.stare == "GASIT").sum(), FAT_EXACT]
fig, ax = plt.subplots(figsize=(8.5, 4.2))
hbar(ax, stages, vals, [BLUE] * len(vals), [str(v) for v in vals], max(vals))
ax.set_title("Common Crawl coverage on the unbiased Find a Tender sample", loc="left", fontsize=11)
fig.text(0.01, -0.02, f"Domain check: {(dom == 'da').sum()} yes, {(dom == 'neverificat').sum()} not verifiable, "
         f"{(dom == 'grup').sum()} group site, {(dom == 'nu').sum()} wrong site. Exact company from docs/research_log.md.",
         fontsize=8, color=INK2)
fig.savefig(OUT / "funnel_fat_sample.png", dpi=150, bbox_inches="tight")
plt.close(fig)

print("figures written to", OUT)
