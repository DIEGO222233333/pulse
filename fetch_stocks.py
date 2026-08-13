#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PULSE — collecte des données boursières (gratuit, via Yahoo Finance / yfinance).

Pour chaque recommandation : cours actuel, historique depuis la date du pick,
PER (trailing + forward), volumes, capitalisation, secteur, 52 semaines.
Génère data/stocks.js (chargé par kpitalist.html, fonctionne en double-clic file://).

Usage :  python3 fetch_stocks.py
"""

import json, time, sys, datetime as dt
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent
OUT = HERE / "data" / "stocks.js"

# ─── Les 72 recommandations (source : Excel de recommandations) ────────────────
# (ticker(s) candidats, nom affiché, date du pick, portefeuille)
# Tickers vérifiés/corrigés : DeVry→ATGE (Adtalem), Embraer→ERJ, StoneX→SNEX,
# Qnity→Q, Moog→MOG-A, Berkshire→BRK-B, Stantec→STN (NYSE), Prysmian→PRY.MI,
# Aritzia→ATZ.TO (fallback ATZAF), CommScope→VISN (fallback COMM).
PICKS = [
    (["EAT"], "Brinker International", "2024-04-01", "ALPHA PICK"),
    (["BLBD"], "Blue Bird Corporation", "2024-05-15", "ALPHA PICK"),
    (["BRK-B"], "Berkshire Hathaway", "2024-07-01", "ALPHA PICK"),
    (["ATGE", "CVSA"], "Adtalem (ex-DeVry)", "2024-07-15", "ALPHA PICK"),
    (["SYF"], "Synchrony Financial", "2024-09-03", "ALPHA PICK"),
    (["POWL"], "Powell Industries", "2024-10-01", "ALPHA PICK"),
    (["AGX"], "Argan", "2024-10-15", "ALPHA PICK"),
    (["CCL"], "Carnival Corporation", "2024-11-01", "ALPHA PICK"),
    (["CLS"], "Celestica", "2024-11-15", "ALPHA PICK"),
    (["ALL"], "Allstate", "2025-01-02", "ALPHA PICK"),
    (["HWM"], "Howmet Aerospace", "2025-01-26", "STOCK ADVISOR"),
    (["BLD"], "TopBuild", "2025-02-09", "STOCK ADVISOR"),
    (["GEHC"], "GE HealthCare", "2025-03-16", "STOCK ADVISOR"),
    (["EZPW"], "EZCORP", "2025-04-01", "ALPHA PICK"),
    (["APP"], "AppLovin", "2025-04-06", "STOCK ADVISOR"),
    (["MFC"], "Manuvie (Manulife)", "2025-05-01", "ALPHA PICK"),
    (["NKE"], "Nike", "2025-05-03", "STOCK ADVISOR"),
    (["UNFI"], "United Natural Foods", "2025-05-15", "ALPHA PICK"),
    (["CPNG"], "Coupang", "2025-05-18", "STOCK ADVISOR"),
    (["DOCS"], "Doximity", "2025-05-27", "STOCK ADVISOR"),
    (["SYY"], "Sysco", "2025-06-08", "STOCK ADVISOR"),
    (["SSRM"], "SSR Mining", "2025-06-16", "ALPHA PICK"),
    (["CME"], "CME Group", "2025-06-22", "STOCK ADVISOR"),
    (["SBUX"], "Starbucks", "2025-07-06", "STOCK ADVISOR"),
    (["RACE"], "Ferrari", "2025-07-20", "STOCK ADVISOR"),
    (["STRL"], "Sterling Infrastructure", "2025-08-01", "ALPHA PICK"),
    (["RKLB"], "Rocket Lab", "2025-08-10", "STOCK ADVISOR"),
    (["VISN", "COMM"], "Vistance Network (CommScope)", "2025-08-15", "ALPHA PICK"),
    (["ONON"], "On Holding", "2025-08-24", "STOCK ADVISOR"),
    (["KGC"], "Kinross Gold", "2025-09-02", "ALPHA PICK"),
    (["STRL"], "Sterling Infrastructure", "2025-09-07", "STOCK ADVISOR"),
    (["CDE"], "Cœur Mining", "2025-09-15", "ALPHA PICK"),
    (["TTAN"], "ServiceTitan", "2025-09-21", "STOCK ADVISOR"),
    (["TTMI"], "TTM Technologies", "2025-10-01", "ALPHA PICK"),
    (["KLAR"], "Klarna", "2025-10-05", "STOCK ADVISOR"),
    (["BROS"], "Dutch Bros Coffee", "2025-10-19", "STOCK ADVISOR"),
    (["MU"], "Micron Technology", "2025-10-19", "ALPHA PICK"),
    (["ATZ.TO", "ATZAF"], "Aritzia", "2025-11-09", "STOCK ADVISOR"),
    (["INCY"], "Incyte", "2025-11-09", "ALPHA PICK"),
    (["TOST"], "Toast", "2025-11-23", "STOCK ADVISOR"),
    (["PARR"], "Par Pacific Holdings", "2025-11-23", "ALPHA PICK"),
    (["FIX"], "Comfort Systems USA", "2025-12-07", "STOCK ADVISOR"),
    (["W"], "Wayfair", "2025-12-07", "ALPHA PICK"),
    (["TIGO"], "Millicom (Tigo)", "2025-12-15", "ALPHA PICK"),
    (["STN"], "Stantec", "2025-12-21", "STOCK ADVISOR"),
    (["U"], "Unity Technologies", "2026-01-04", "STOCK ADVISOR"),
    (["B"], "Barrick Mining", "2026-01-04", "ALPHA PICK"),
    (["CASY"], "Casey's General Stores", "2026-01-18", "STOCK ADVISOR"),
    (["NEM"], "Newmont", "2026-01-18", "ALPHA PICK"),
    (["DY"], "Dycom Industries", "2026-02-08", "ALPHA PICK"),
    (["DDOG"], "Datadog", "2026-02-22", "STOCK ADVISOR"),
    (["GM"], "General Motors", "2026-02-22", "ALPHA PICK"),
    (["FN"], "Fabrinet", "2026-03-08", "ALPHA PICK"),
    (["PRY.MI"], "Prysmian", "2026-03-15", "STOCK ADVISOR"),
    (["LITE"], "Lumentum Holdings", "2026-03-22", "ALPHA PICK"),
    (["AMZN"], "Amazon", "2026-03-29", "STOCK ADVISOR"),
    (["CSTM"], "Constellium", "2026-04-05", "ALPHA PICK"),
    (["EMBJ", "ERJ"], "Embraer", "2026-04-12", "STOCK ADVISOR"),
    (["NEXA"], "Nexa Resources", "2026-04-19", "ALPHA PICK"),
    (["MOG-A"], "Moog", "2026-04-26", "STOCK ADVISOR"),
    (["CRDO"], "Credo Technology", "2026-05-03", "ALPHA PICK"),
    (["KRYS"], "Krystal Biotech", "2026-05-10", "STOCK ADVISOR"),
    (["MXL"], "MaxLinear", "2026-05-17", "ALPHA PICK"),
    (["GLW"], "Corning", "2026-05-24", "STOCK ADVISOR"),
    (["APH"], "Amphenol", "2026-05-31", "VALUE LINE"),
    (["SNDK"], "Sandisk", "2026-06-07", "ALPHA PICK"),
    (["FPS"], "Forgent Power Solutions", "2026-06-07", "STOCK ADVISOR"),
    (["NBIX"], "Neurocrine Biosciences", "2026-06-14", "VALUE LINE"),
    (["SNEX"], "StoneX (Intl FC Stone)", "2026-06-21", "ALPHA PICK"),
    (["Q", "QNTY"], "Qnity Electronics", "2026-06-21", "STOCK ADVISOR"),
    (["STRL"], "Sterling Infrastructure", "2026-07-04", "STOCK ADVISOR"),
    (["ICHR"], "Ichor Holdings", "2026-07-04", "ALPHA PICK"),
]

# ─── Descriptions d'activité en français (rédigées à la main) ───────────────
DESC_FR = {
    "EAT": "Groupe de restauration américain, maison mère des chaînes Chili's Grill & Bar et Maggiano's Little Italy (plus de 1 600 restaurants).",
    "BLBD": "Constructeur américain de bus scolaires, leader des bus électriques et à carburants alternatifs pour le transport d'élèves.",
    "BRK-B": "Holding de Warren Buffett : assurance (GEICO), chemins de fer (BNSF), énergie, et participations majeures (Apple, Coca-Cola, American Express…).",
    "ATGE": "Groupe d'enseignement supérieur privé (ex-DeVry), spécialisé dans la formation médicale et infirmière aux États-Unis (Chamberlain, Ross, Walden).",
    "SYF": "Banque de crédit à la consommation, n°1 américain des cartes de crédit co-brandées pour enseignes (Amazon, Lowe's, PayPal…).",
    "POWL": "Fabricant américain d'équipements électriques (appareillage, salles électriques intégrées) pour data centers, pétrole-gaz et services publics.",
    "AGX": "Via sa filiale Gemma Power Systems, conçoit et construit des centrales électriques (gaz naturel, renouvelables) aux États-Unis.",
    "CCL": "Premier croisiériste mondial : Carnival, Princess, Costa, AIDA, Holland America… plus de 90 navires.",
    "CLS": "Groupe canadien de fabrication électronique (EMS) : serveurs et matériel réseau pour hyperscalers et data centers IA.",
    "ALL": "Un des plus grands assureurs américains : assurance auto, habitation et protection des particuliers.",
    "HWM": "Équipementier aérospatial : composants de moteurs à réaction, fixations et structures en titane pour Boeing, Airbus et la défense.",
    "BLD": "Leader américain de l'installation et de la distribution d'isolation et de produits du bâtiment pour la construction résidentielle.",
    "GEHC": "Spin-off de General Electric : imagerie médicale (IRM, scanners), ultrasons, diagnostics et solutions numériques pour hôpitaux.",
    "EZPW": "Chaîne de prêteurs sur gage aux États-Unis et en Amérique latine : prêts garantis et vente d'articles d'occasion.",
    "APP": "Plateforme logicielle de publicité mobile pilotée par IA (moteur Axon) qui monétise applis et jeux mobiles.",
    "MFC": "Groupe canadien d'assurance-vie et de gestion de patrimoine, très présent en Asie, au Canada et aux États-Unis (John Hancock).",
    "NKE": "N°1 mondial de l'équipement sportif : chaussures, textile et accessoires sous les marques Nike, Jordan et Converse.",
    "UNFI": "Premier distributeur en gros de produits alimentaires naturels et bio d'Amérique du Nord, fournisseur clé de Whole Foods.",
    "CPNG": "« L'Amazon sud-coréen » : e-commerce avec livraison ultra-rapide Rocket Delivery, streaming et livraison de repas.",
    "DOCS": "Réseau professionnel en ligne pour médecins américains (plus de 80 % y sont inscrits) : télémédecine, outils IA et publicité pharma.",
    "SYY": "Premier distributeur alimentaire mondial pour la restauration : livre restaurants, hôpitaux, écoles et hôtels.",
    "SSRM": "Producteur d'or et d'argent avec des mines aux États-Unis, au Canada, en Argentine et en Turquie.",
    "CME": "Premier marché mondial de produits dérivés : futures et options sur taux, indices, devises, énergie et métaux.",
    "SBUX": "Première chaîne de cafés au monde, plus de 40 000 salons de café dans 80 pays.",
    "RACE": "Constructeur italien de voitures de sport de luxe, marges parmi les plus élevées de l'automobile, écurie de F1 mythique.",
    "STRL": "Groupe américain d'infrastructures : terrassement de data centers (e-infrastructure), routes et fondations résidentielles.",
    "RKLB": "Société spatiale : lanceur Electron, futur lanceur Neutron, composants et satellites pour constellations.",
    "VISN": "Équipementier réseaux (ex-CommScope) : infrastructure haut débit, câble et connectivité pour opérateurs et data centers.",
    "COMM": "Équipementier réseaux : infrastructure haut débit, câble et connectivité pour opérateurs et data centers.",
    "ONON": "Marque suisse de running premium (chaussures On, technologie CloudTec), en forte croissance mondiale.",
    "KGC": "Producteur d'or canadien de premier plan : mines aux États-Unis, au Brésil, en Mauritanie et au Chili.",
    "CDE": "Producteur américain d'argent et d'or : mines au Nevada, en Alaska et au Mexique (Palmarejo, Rochester…).",
    "TTAN": "Éditeur du logiciel cloud de référence pour les artisans du bâtiment américains (plomberie, CVC, électricité) : devis, planning, paiement.",
    "TTMI": "Fabricant américain de circuits imprimés (PCB) de haute technologie pour l'aérospatiale, la défense et les data centers.",
    "KLAR": "Fintech suédoise du paiement fractionné (« buy now, pay later ») et néobanque, cotée à New York depuis 2025.",
    "BROS": "Chaîne de cafés drive-through en hypercroissance dans l'ouest américain, connue pour ses boissons énergisantes personnalisées.",
    "MU": "Un des trois géants mondiaux des puces mémoire (DRAM, NAND, HBM pour l'IA), basé dans l'Idaho.",
    "ATZ.TO": "Marque canadienne de mode féminine « luxe accessible », en pleine expansion aux États-Unis.",
    "ATZAF": "Marque canadienne de mode féminine « luxe accessible », en pleine expansion aux États-Unis.",
    "INCY": "Biotech américaine spécialisée en oncologie et dermatologie : médicaments Jakafi et Opzelura.",
    "TOST": "Plateforme cloud tout-en-un pour restaurants : caisse, commandes, paie et livraison — plus de 140 000 établissements.",
    "PARR": "Raffineur et distributeur de carburants centré sur Hawaï et le nord-ouest américain, stations-service et logistique.",
    "FIX": "Installateur américain de systèmes CVC (chauffage-ventilation-clim), mécaniques et électriques, porté par les data centers.",
    "W": "Un des plus grands e-commerçants de meubles et de décoration aux États-Unis et en Europe.",
    "TIGO": "Opérateur télécom (mobile, internet fixe, services financiers Tigo Money) leader en Amérique latine.",
    "STN": "Groupe canadien d'ingénierie et de conseil : eau, environnement, bâtiments et infrastructures dans le monde entier.",
    "U": "Moteur temps réel Unity pour jeux vidéo et 3D interactive, plus monétisation publicitaire des jeux mobiles.",
    "B": "Un des plus grands producteurs d'or au monde (ex-Barrick Gold), mines au Nevada, en Afrique et en Amérique latine, plus cuivre.",
    "CASY": "3e chaîne de supérettes des États-Unis : plus de 2 900 magasins-stations dans le Midwest, célèbre pour sa pizza.",
    "NEM": "Premier producteur d'or mondial, mines sur quatre continents, également cuivre, argent et zinc.",
    "DY": "Services d'ingénierie pour opérateurs télécoms américains : déploiement de la fibre optique et des réseaux.",
    "DDOG": "Plateforme cloud d'observabilité : surveillance des serveurs, applications et sécurité pour les équipes DevOps.",
    "GM": "Constructeur automobile américain : Chevrolet, GMC, Cadillac, Buick — offensive électrique (Ultium) et conduite autonome.",
    "FN": "Fabricant (Thaïlande) de composants optiques et photoniques de précision, fournisseur clé de Nvidia pour l'IA.",
    "PRY.MI": "Groupe italien n°1 mondial des câbles : énergie, télécoms et interconnexions sous-marines.",
    "LITE": "Spécialiste américain de la photonique : lasers et composants optiques pour data centers IA et télécoms.",
    "AMZN": "Géant mondial du e-commerce et n°1 du cloud (AWS), également publicité, streaming et IA.",
    "CSTM": "Groupe (racines françaises) de produits en aluminium à haute valeur ajoutée pour l'aéronautique, l'automobile et l'emballage.",
    "EMBJ": "3e avionneur mondial (Brésil) : jets régionaux, aviation d'affaires (Phenom, Praetor), défense et eVTOL (Eve).",
    "NEXA": "Producteur de zinc et de cuivre (groupe Votorantim), mines et fonderies au Pérou et au Brésil.",
    "MOG-A": "Équipementier américain de systèmes de contrôle de mouvement de précision pour l'aéronautique, l'espace et la défense.",
    "CRDO": "Concepteur de puces et câbles actifs (AEC) pour la connectivité très haut débit des data centers IA.",
    "KRYS": "Biotech de thérapie génique : Vyjuvek, premier traitement topique redosable pour l'épidermolyse bulleuse.",
    "MXL": "Concepteur américain de semi-conducteurs pour le haut débit, la connectivité et l'infrastructure réseau.",
    "GLW": "Inventeur du verre Gorilla Glass (smartphones) et leader de la fibre optique, écrans et sciences de la vie.",
    "APH": "Un des leaders mondiaux des connecteurs et câbles haute performance : IA/data centers, défense, automobile.",
    "SNDK": "Spécialiste de la mémoire flash NAND et du stockage (SSD, cartes), redevenu indépendant de Western Digital en 2025.",
    "FPS": "Forgent Power Solutions : société américaine de solutions d'alimentation électrique cotée au NYSE.",
    "NBIX": "Biotech spécialisée dans les maladies neurologiques et endocriniennes : Ingrezza (dyskinésie tardive), Crenessity.",
    "SNEX": "Groupe de services financiers (ex-INTL FCStone) : courtage, compensation et couverture sur matières premières et devises.",
    "Q": "Spin-off électronique de DuPont : matériaux et consommables pour la fabrication de semi-conducteurs.",
    "ICHR": "Fournisseur de systèmes de distribution de fluides et de gaz pour les équipementiers de semi-conducteurs.",
}

MAX_POINTS = 160  # points max par courbe (downsampling)


def downsample(dates, closes, max_points=MAX_POINTS):
    n = len(dates)
    if n <= max_points:
        return dates, closes
    step = n / max_points
    idx = sorted({min(n - 1, round(i * step)) for i in range(max_points)} | {0, n - 1})
    return [dates[i] for i in idx], [closes[i] for i in idx]


def fetch_ticker(symbol, earliest):
    """Retourne (info, history_df) ou None si introuvable."""
    t = yf.Ticker(symbol)
    hist = t.history(start=earliest, interval="1d", auto_adjust=False)
    if hist is None or hist.empty:
        return None
    try:
        info = t.info or {}
    except Exception:
        info = {}
    return info, hist


def main():
    # date la plus ancienne par ticker (un ticker peut avoir plusieurs picks)
    earliest = {}
    for cands, _, date, _ in PICKS:
        key = cands[0]
        earliest[key] = min(earliest.get(key, date), date)

    quotes, resolved, failed = {}, {}, []
    done = set()
    for cands, name, date, _ in PICKS:
        primary = cands[0]
        if primary in done:
            continue
        done.add(primary)
        start = (dt.date.fromisoformat(earliest[primary]) - dt.timedelta(days=7)).isoformat()
        result, used = None, None
        for sym in cands:
            try:
                result = fetch_ticker(sym, start)
            except Exception as e:
                print(f"  ! {sym}: {e}", file=sys.stderr)
                result = None
            if result:
                used = sym
                break
            time.sleep(0.6)
        if not result:
            print(f"  ✗ {name} ({'/'.join(cands)}) introuvable", file=sys.stderr)
            failed.append(primary)
            continue
        info, hist = result
        resolved[primary] = used
        closes = [round(float(c), 4) for c in hist["Close"].tolist()]
        vols = [int(v) if v == v else 0 for v in hist["Volume"].tolist()]
        dates = [d.strftime("%Y-%m-%d") for d in hist.index]
        d_ds, c_ds = downsample(dates, closes)
        price = closes[-1] if closes else None
        quotes[primary] = {
            "symbol": used,
            "price": price,
            "prevClose": closes[-2] if len(closes) > 1 else None,
            "currency": info.get("currency") or ("EUR" if used.endswith(".MI") else "CAD" if used.endswith(".TO") else "USD"),
            "pe": info.get("trailingPE"),
            "forwardPe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "volume": vols[-1] if vols else info.get("volume"),
            "avgVolume": info.get("averageVolume"),
            "marketCap": info.get("marketCap"),
            "high52": info.get("fiftyTwoWeekHigh"),
            "low52": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "exchange": info.get("fullExchangeName") or info.get("exchange"),
            "website": info.get("website"),
            "descFr": DESC_FR.get(primary) or DESC_FR.get(used),
            "descEn": (info.get("longBusinessSummary") or "")[:600],
            "history": {"dates": d_ds, "closes": [round(c, 3) for c in c_ds]},
            # série complète (dates ISO) gardée pour retrouver le cours au pick
            "_allDates": dates,
            "_allCloses": closes,
        }
        print(f"  ✓ {used:8s} {name:32s} {price}")
        time.sleep(0.35)

    picks_out = []
    for i, (cands, name, date, portfolio) in enumerate(PICKS):
        primary = cands[0]
        q = quotes.get(primary)
        price_at_pick = None
        if q:
            for d, c in zip(q["_allDates"], q["_allCloses"]):
                if d >= date:
                    price_at_pick = c
                    break
        picks_out.append({
            "id": i,
            "ticker": primary,
            "name": name,
            "date": date,
            "portfolio": portfolio,
            "priceAtPick": price_at_pick,
        })

    for q in quotes.values():
        q.pop("_allDates", None)
        q.pop("_allCloses", None)

    payload = {
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "picks": picks_out,
        "quotes": quotes,
        "failed": failed,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("window.PULSE_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"\n→ {OUT} écrit ({kb:.0f} Ko) — {len(quotes)} tickers, {len(failed)} échec(s): {failed}")


if __name__ == "__main__":
    main()
