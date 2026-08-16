#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PULSE — dossier d'analyse factuelle (gratuit, via Yahoo Finance / yfinance).

Pour chaque valeur : valorisation, croissance, marges, dette, consensus des
analystes (objectifs de cours publiés), momentum 3/6/12 mois, volatilité,
liquidité, prochains résultats, drapeaux de risque factuels, et les 3 valeurs
de la liste avec lesquelles elle est le plus corrélée (1 an de cotations).

Aucune note, aucun classement, aucune recommandation : uniquement des faits.

Génère data/analysis.js. Usage :  python3 fetch_analysis.py
"""

import json, math, time, sys, datetime as dt
from pathlib import Path

import yfinance as yf
import pandas as pd

from fetch_stocks import PICKS, NON_US

HERE = Path(__file__).parent
OUT = HERE / "data" / "analysis.js"

TICKERS = []
for cands, name, date, pf in PICKS:
    if cands[0] not in TICKERS:
        TICKERS.append(cands[0])

# blocs thématiques (appartenance factuelle par activité ; la corrélation
# moyenne intra-bloc est ensuite CALCULÉE sur les cours, pas décrétée)
BLOCKS = {
    "Infrastructure IA / data centers": ["CLS","VRT","ANET","CRDO","FN","LITE","MU","STRL","POWL","ETN","FIX","APH","GLW","TTMI","ICHR","Q","SNDK","MXL","DY","CSCO","APP","DDOG","MSFT","META","AMZN","IOT","U","TTAN","VEEV","TOST","DOCS","KLAR","W","MELI","CPNG"],
    "Or, argent et métaux": ["B","NEM","KGC","SSRM","CDE","RGLD","NEXA","CSTM"],
    "Conso / restauration / voyage": ["EAT","TXRH","SBUX","BROS","CCL","ONON","NKE","CASY","SYY","UNFI","ATZ.TO","RACE","GM","BLBD"],
    "Santé": ["CNC","AZN","NBIX","KRYS","GEHC","OPCH","BTSG","INCY","ATGE"],
    "Finance / assurance": ["MS","SYF","ALL","MFC","CME","SNEX","BRK-B"],
    "Industrie / défense / énergie": ["HWM","MOG-A","HII","EMBJ","RKLB","AGX","BLD","STN","PRY.MI","TIGO","VISN","PARR","FPS","EZPW"],
}

def pct(a, b):
    return round((a / b - 1) * 100, 1) if (a and b) else None

def main():
    infos, closes = {}, {}
    for i, t in enumerate(TICKERS):
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="1y", interval="1d", auto_adjust=False)
            if h is None or h.empty:
                print(f"  ✗ {t}: pas d'historique", file=sys.stderr); continue
            closes[t] = h["Close"]
            try:
                infos[t] = tk.info or {}
            except Exception:
                infos[t] = {}
            # date des prochains résultats
            try:
                cal = tk.calendar
                ed = None
                if isinstance(cal, dict):
                    v = cal.get("Earnings Date") or cal.get("earningsDate")
                    if v: ed = str(v[0])[:10] if isinstance(v, (list, tuple)) else str(v)[:10]
                infos[t]["_earningsDate"] = ed
            except Exception:
                infos[t]["_earningsDate"] = None
            print(f"  ✓ {t} ({i+1}/{len(TICKERS)})")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ {t}: {e}", file=sys.stderr)

    # ── corrélations sur les rendements quotidiens (1 an)
    df = pd.DataFrame(closes)
    rets = df.pct_change().dropna(how="all")
    corr = rets.corr(min_periods=60)

    # ── médiane de PER par secteur (au sein de la liste : comparaison honnête)
    sector_pe = {}
    for t, inf in infos.items():
        s, pe = inf.get("sector"), inf.get("trailingPE")
        if s and pe and 0 < pe < 300:
            sector_pe.setdefault(s, []).append(pe)
    sector_pe_med = {s: round(sorted(v)[len(v)//2], 1) for s, v in sector_pe.items()}

    by = {}
    for t in TICKERS:
        inf = infos.get(t)
        if inf is None: continue
        c = closes.get(t)
        price = float(c.iloc[-1]) if c is not None and len(c) else None
        mom = {}
        if c is not None:
            for label, days in (("m3", 63), ("m6", 126), ("m12", 252)):
                if len(c) > days:
                    mom[label] = pct(float(c.iloc[-1]), float(c.iloc[-1-days]))
        vol_d = None
        if t in rets.columns:
            r = rets[t].dropna().tail(90)
            if len(r) > 30:
                vol_d = round(float(r.std()) * 100, 2)   # % par jour
        # top corrélations dans la liste
        top_corr = []
        if t in corr.columns:
            s = corr[t].drop(labels=[t], errors="ignore").dropna().sort_values(ascending=False)
            top_corr = [[o, round(float(v), 2)] for o, v in s.head(3).items() if v > 0.35]
        eps = inf.get("trailingEps")
        mcap = inf.get("marketCap")
        avg_vol = inf.get("averageVolume")
        dollar_vol = round(avg_vol * price / 1e6, 1) if (avg_vol and price) else None  # M$/jour
        debt, ebitda = inf.get("totalDebt"), inf.get("ebitda")
        cash = inf.get("totalCash")
        nd_ebitda = round((debt - (cash or 0)) / ebitda, 1) if (debt and ebitda and ebitda > 0) else None
        hi, lo = inf.get("fiftyTwoWeekHigh"), inf.get("fiftyTwoWeekLow")
        flags = []
        if eps is not None and eps < 0: flags.append("Non rentable (BPA négatif)")
        if vol_d and vol_d > 3: flags.append(f"Très volatile ({vol_d} %/jour)")
        if dollar_vol is not None and dollar_vol < 10: flags.append("Liquidité faible (<10 M$/j)")
        if mcap and mcap < 2e9: flags.append("Petite capitalisation (<2 Md$)")
        if nd_ebitda is not None and nd_ebitda > 3: flags.append(f"Endettement élevé ({nd_ebitda}× EBITDA)")
        if price and hi and price >= hi * 0.97: flags.append("Proche du plus haut 52 sem.")
        if price and lo and price <= lo * 1.1: flags.append("Proche du plus bas 52 sem.")
        by[t] = {
            "sector": inf.get("sector"), "industry": inf.get("industry"),
            "pe": inf.get("trailingPE"), "fwdPe": inf.get("forwardPE"),
            "sectorPeMed": sector_pe_med.get(inf.get("sector")),
            "ps": inf.get("priceToSalesTrailing12Months"),
            "revGrowth": inf.get("revenueGrowth"), "epsGrowth": inf.get("earningsGrowth"),
            "margin": inf.get("profitMargins"), "opMargin": inf.get("operatingMargins"),
            "roe": inf.get("returnOnEquity"),
            "ndEbitda": nd_ebitda,
            "beta": inf.get("beta"),
            "target": inf.get("targetMeanPrice"), "targetLow": inf.get("targetLowPrice"),
            "targetHigh": inf.get("targetHighPrice"), "nAnalysts": inf.get("numberOfAnalystOpinions"),
            "recoMean": inf.get("recommendationMean"),   # échelle publique 1 (achat fort) → 5 (vente)
            "mom": mom, "volDaily": vol_d,
            "dollarVolM": dollar_vol,
            "earningsDate": inf.get("_earningsDate"),
            "flags": flags,
            "topCorr": top_corr,
        }

    # ── blocs : corrélation moyenne intra-bloc calculée
    blocks_out = []
    for name, members in BLOCKS.items():
        m = [t for t in members if t in corr.columns]
        vals = []
        for i in range(len(m)):
            for j in range(i+1, len(m)):
                v = corr.at[m[i], m[j]]
                if pd.notna(v): vals.append(float(v))
        blocks_out.append({
            "name": name, "members": m,
            "avgCorr": round(sum(vals)/len(vals), 2) if vals else None,
        })

    payload = {
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "byTicker": by,
        "blocks": blocks_out,
        "note": "Données factuelles Yahoo Finance. Aucun classement ni recommandation. Les objectifs de cours sont ceux publiés par les analystes (consensus).",
    }
    OUT.write_text("window.PULSE_ANALYSIS = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"\n→ {OUT} écrit ({OUT.stat().st_size/1024:.0f} Ko) — {len(by)} valeurs analysées")

if __name__ == "__main__":
    main()
