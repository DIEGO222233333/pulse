# PULSE — Suivi des recommandations

Dashboard de suivi des actions recommandées par les portefeuilles **Alpha Pick**,
**Stock Advisor** et **Value Line** (source : Excel de recommandations, hors dépôt).

## Utilisation

1. **Rafraîchir les données** (cours, PER, volumes, historiques — via Yahoo Finance, gratuit) :

   ```bash
   python3 fetch_stocks.py
   ```

2. **Ouvrir l'app** : double-cliquer sur `index.html` (aucun serveur nécessaire,
   les données sont chargées depuis `data/stocks.js`).

## Rafraîchissement automatique

- **GitHub Action** (`.github/workflows/refresh.yml`) : relance la collecte toutes les
  30 min pendant les heures de Wall Street + un passage complet chaque matin, et commit
  `data/stocks.js`. L'app est servie par **GitHub Pages**.
- **Mode live dans l'app** : avec une clé API [Finnhub](https://finnhub.io) (gratuite),
  la page rafraîchit les cours US en continu tant qu'elle est ouverte (~1 valeur/seconde,
  tour complet du portefeuille ≈ 1 min). La clé se colle via le bouton ⚙︎ (stockée en
  localStorage) ou, en local, dans `data/live_config.js` (exclu de git — **ne jamais
  committer de clé, le dépôt est public**).

## Fichiers

- `index.html` — l'application (HTML/CSS/JS vanilla, zéro dépendance).
- `fetch_stocks.py` — collecte des données. C'est aussi **là que vivent la liste des picks**
  (tableau `PICKS`) et les descriptions françaises (`DESC_FR`). Pour ajouter une reco :
  ajouter une ligne dans `PICKS` (+ une description), puis relancer le script.
- `data/stocks.js` — données générées (ne pas éditer à la main).

## Notes sur les tickers

Corrigés par rapport à l'Excel : DeVry → `ATGE` (Adtalem), Embraer → `EMBJ`,
StoneX → `SNEX`, Qnity → `Q`, Forgent → `FPS`, Moog → `MOG-A`, Berkshire → `BRK-B`,
Stantec → `STN` (NYSE, USD), Prysmian → `PRY.MI` (EUR), Aritzia → `ATZ.TO` (CAD).
