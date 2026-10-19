# Bot_crypto : analyse de l'existant et plan de refonte

Document rédigé le 19 octobre 2026 à partir d'une lecture complète du dépôt (483 commits, mai 2022 à avril 2024, 2 659 lignes Python).

**Objectif de la refonte** : reprendre les idées du projet (indicateurs techniques, modèle prédictif, pilotage et notifications Discord, bot autonome sur VPS), le moderniser, le fiabiliser, le mettre à jour et le réécrire.

**Périmètre technique** : table rase. On ne conserve du dépôt actuel que les idées et les enseignements ; aucun fichier n'est repris tel quel. Stack neuve (section 5), Python 3.14, Docker, outillage moderne.

**Contrainte structurante** : pouvoir changer de plateforme sans difficulté, aussi bien pour l'exécution des ordres que pour la récupération des données. Le tri opéré par MiCA en 2025-2026 (section 2.2) montre qu'un exchange peut disparaître du jour au lendemain pour un résident français. Le code métier ne doit donc jamais dépendre d'une plateforme précise (section 4.1).

Table des matières :

1. [Ce que fait le projet actuel](#1-ce-que-fait-le-projet-actuel)
2. [Pourquoi il ne peut pas redémarrer tel quel](#2-pourquoi-il-ne-peut-pas-redémarrer-tel-quel)
3. [État du code](#3-état-du-code)
4. [Architecture cible](#4-architecture-cible)
5. [Stack technique : table rase](#5-stack-technique--table-rase)
6. [Intégration d'un LLM : analyse des prédictions et des news](#6-intégration-dun-llm--analyse-des-prédictions-et-des-news)
7. [Nouvelles capacités](#7-nouvelles-capacités)
8. [Plan par phases](#8-plan-par-phases)
9. [Décisions à prendre](#9-décisions-à-prendre)
10. [Sources](#10-sources)

---

## 1. Ce que fait le projet actuel

Bot de trading journalier sur BTC, organisé en trois couches.

### 1.1 Données et IA

| Élément | Détail |
|---|---|
| Source de données | API publique Binance, bougies 1 jour, 40 dernières bougies |
| Actifs suivis | BTC, BTCUP, BTCDOWN (jetons à levier Binance) |
| Features | 23 indicateurs TA-Lib (SMA, EMA, ADX, KAMA, T3, TRIMA, PPO, Ultimate Oscillator, MACD, StochRSI, Bollinger sur 40 bougies ; RSI, VWAP, CMF, CCI, MFI, régression linéaire, TSF, Aroon, Williams %R, ROC, OBV, MOM sur 15 bougies) aplatis en un vecteur de 298 valeurs |
| Modèles | 3 réseaux Keras Sequential Dense/ReLU (un par actif) qui régressent le prix de clôture suivant. BTC : 21/21 neurones, BTCUP : 253/253, BTCDOWN : 21/21 |
| Entraînement | `database.py` stocke les features dans SQLite (listes Python sérialisées en texte), `main.py` entraîne avec `train_test_split` aléatoire, MSLE, Adam, 50 epochs. Variante keras-tuner RandomSearch |
| Stockage modèles | `Model_1d/<actif>/model.json` + `model.h5` |

### 1.2 Décision et exécution

Boucle `bot.py`, une itération par 24 h :

1. Récupère les 40 bougies des trois actifs (3 processus parallèles).
2. Calcule les trois prédictions.
3. Signal d'achat si `prix < pred` ET `prix_up < pred_up` ET `prix_down > pred_down` (achat BTC3L sur KuCoin), ou l'inverse (achat BTC3S).
4. Vend l'éventuelle position opposée, achète au marché avec **tout le solde USDT**, place un ordre limite de vente à +1,5 %.
5. Lance un thread de stop-loss manuel (polling toutes les 10 s du prix spot BTC, seuil ±2,5 %).
6. Chaque jour sans exécution : baisse l'ordre limite de 0,25 %. Si le gain cible tombe à 0, vente au marché.
7. Persiste l'état (date, symbole, prix stop) dans `state_bot_BTC.txt` pour reprendre après redémarrage.

### 1.3 Exploitation

- `bot_discord.py` : bot Discord avec commandes `!start`, `!stop`, `!vente`, `!montant`, `!prix`, `!statut`, `!estimation`, `!restart`, `!analyse`, `!del`. Lance `bot.py` dans un `multiprocessing.Process`.
- `message_discord.py` : trois webhooks (général, état du bot, prises de position), envoi des erreurs avec traceback.
- `start.py`, `stop.py`, `restart.py` : `git pull` + `nohup`, arrêt par `ps aux | grep` + `kill -9`.
- `recovery_error_files.py` : rapatrie les logs du VPS par SFTP (paramiko) puis les vide.
- Logs : fichiers texte maison dans `log_files/`, analyse périodique des réponses KuCoin dont le code n'est pas 200000.
- `SharedMemoryDict` pour partager un état entre le bot Discord et le bot de trading (vente manuelle, prix estimé).

Le README indique que le projet a été abandonné faute de fiabilité des modèles.

---

## 2. Pourquoi il ne peut pas redémarrer tel quel

Les deux fondations externes ont disparu, pas seulement la plateforme d'exécution.

### 2.1 KuCoin n'est plus accessible depuis la France

KuCoin figurait sur la liste noire de l'AMF depuis le 15 avril 2024. Le 28 juillet 2025, l'exchange a annoncé la fin de ses services pour les résidents français : blocage des dépôts et inscriptions le 4 août 2025, liquidation des comptes le 25 août 2025. KuCoin n'a pas obtenu d'agrément MiCA. Depuis le 1er juillet 2026, une plateforme sans agrément MiCA ne peut plus servir les résidents français.

Pourquoi la liste noire : l'AMF n'a publié aucun motif. Le fondement juridique est l'absence d'enregistrement PSAN (Prestataire de Services sur Actifs Numériques). Le déclencheur probable est l'inculpation de KuCoin et de deux de ses fondateurs par la justice américaine le 26 mars 2024 pour activité de transfert d'argent sans licence et défaut de contrôles anti-blanchiment.

### 2.2 MiCA a fait le tri, Binance comprise

La période transitoire française s'est achevée le 1er juillet 2026. Seuls les prestataires agréés CASP (Crypto-Asset Service Provider) peuvent désormais servir des résidents français ; les autres ont été radiés automatiquement le 2 juillet 2026. Une centaine de PSAN ont laissé place à 31 prestataires agréés.

| Plateforme | Statut pour un résident français (octobre 2026) |
|---|---|
| Binance | Sortie. Pas d'agrément avant l'échéance, demande en Grèce retirée face à un refus annoncé, services en Europe réduits aux retraits depuis septembre 2026. Discussions avec l'AMF pour un dossier en France, rien d'accordé |
| KuCoin | Sortie en août 2025 |
| Bitget, MEXC | Pas d'agrément selon la presse spécialisée |
| Coinbase, Kraken, Bitstamp, OKX EU, Bitpanda, Coinhouse | Agréées |
| Perpétuels sous agrément | Coinbase, OKX EU, Kraken, Bitstamp, Backpack EU, Nexo |

Leçon pour le projet : un exchange, même le premier mondial, peut devenir inaccessible en quelques mois. L'architecture doit permettre d'en changer par configuration, pour l'exécution comme pour les données.

### 2.3 Binance a délisté les jetons à levier BTCUP et BTCDOWN

Binance a arrêté le trading de ses jetons à levier appariés USDT (BTCUP, BTCDOWN, ETHUP, ETHDOWN, BNBUP, BNBDOWN) puis les a délistés. Ces deux séries étaient les entrées de deux des trois modèles et des deux tiers de la règle de décision. **Le signal d'achat ne peut donc plus être calculé.**

### 2.4 Les jetons 3L/3S n'existent pas chez les exchanges agréés MiCA

L'équivalent fonctionnel (exposition long ou short avec levier) est le futures perpétuel ou le margin. Pour la France, les plateformes agréées MiCA qui proposent des perpétuels sont Coinbase, OKX EU, Kraken, Bitstamp, Backpack EU et Nexo (29 plateformes agréées au total au 16 octobre 2026).

### 2.5 Le code ne démarre pas en local

| Problème | Détail |
|---|---|
| Fichiers de poids | `main.py` charge `model.weights.h5` mais le dépôt contient `model.h5` |
| Version Keras | Modèles sauvés avec Keras 2.12 (`batch_input_shape` dans le JSON), requirements.txt vise TensorFlow 2.16 / Keras 3.2 |
| Python | TensorFlow 2.16 ne supporte pas Python 3.14 ; faire tourner l'ancien code exigerait un Python 3.12 ou antérieur |
| TA-Lib | Nécessite la bibliothèque C système |
| Locale | `locale.setlocale(fr_FR.UTF-8)` plante si la locale n'est pas installée |
| Chemin | `/home/Bot_crypto/log_files` codé en dur dans `server_data.py` |

---

## 3. État du code

Le code est lisible, commenté en français, et le découpage en fichiers est cohérent. Il porte néanmoins une dette importante.

### 3.1 Méthode ML (le vrai point faible d'origine)

- **Fuite de données.** `train_test_split` mélange aléatoirement des fenêtres glissantes de 40 jours qui se chevauchent à 97,5 %. Le jeu de test contient presque les mêmes données que le jeu d'entraînement. Les scores R² étaient donc gonflés et ne prédisaient rien de la performance réelle.
- **Pas de normalisation.** Des prix à 30 000 côtoient un RSI entre 0 et 100 et un OBV en millions dans le même vecteur d'entrée.
- **Cible mal posée.** Régression du prix brut avec une sortie ReLU et une perte MSLE. Prédire le prix absolu revient surtout à recopier le dernier prix. La bonne cible est le rendement ou la direction.
- **Surapprentissage structurel.** Environ 500 échantillons pour 298 entrées, et jusqu'à 253 neurones par couche.
- **Aucun backtest.** Pas de simulation avec frais, slippage, ni métriques (Sharpe, drawdown, taux de réussite). Pas de validation glissante dans le temps (walk-forward).
- **Features opaques.** Les listes d'indicateurs sont tronquées des NaN avant aplatissement, donc la longueur et la position de chaque valeur dans le vecteur de 298 dépendent du nombre de NaN produit par TA-Lib. Fragile.

### 3.2 Gestion du risque

- Tout le solde engagé à chaque trade.
- Ordres au marché, stop-loss par polling Python toutes les 10 s au lieu d'un ordre stop natif sur l'exchange. Si le processus meurt, plus de stop.
- Aucune limite de perte quotidienne ou globale, aucun dimensionnement de position.
- Le stop-loss est évalué sur le prix spot BTC alors que la position est sur un jeton ×3 : le seuil réel sur la position est ±7,5 %.

### 3.3 Bugs identifiés

| Fichier | Ligne | Bug |
|---|---|---|
| `technical_indicators.py` | 217 | OBV calculé avec la colonne `low` au lieu de `volume` |
| `technical_indicators.py` | 20-21 | `moyenne()` renvoie 5 quand la liste est vide, valeur arbitraire injectée dans les features |
| `bot.py` | 193 | Branche `elif time_last_position >= 2` inatteignable, la condition `>= 1` capture tout |
| `bot.py` | 134 | Clés `not result_purchase` (booléen) sur des dicts à clés entières, fonctionne par égalité de hash mais fragile |
| `database.py` | 189-194 | Indicateurs stockés en texte puis relus par `ast.literal_eval`, lent et fragile |
| `server_data.py` | 848-856 | Threads qui se relancent récursivement sur erreur, la pile croît à chaque incident |
| `server_data.py` | 384 | `fichier_content[1:-1]` saute le premier caractère du log |
| `main.py` | 171 | Annotation `Union[Any, Any, Any]` pour un tuple |
| `main.py` | 162-167 | Sélection du modèle par `True / False / None`, illisible |

### 3.4 Architecture et exploitation

- Imports en étoile en chaîne (`bot.py` → `main.py` → `database.py` → `technical_indicators.py` + `server_data.py`), état global, couplage fort.
- `multiprocessing` + `Manager` pour trois requêtes HTTP, et pour parser la base SQLite. Surdimensionné.
- Clés API en dur dans le code (placeholders aujourd'hui, mais le schéma reste mauvais).
- Dates persistées en texte français (`%A %d %B %Y`) et reparsées, dépendant de la locale.
- `os.system("echo > ...")`, `kill -9` par grep, `nohup`. Aucun superviseur.
- `priceIncrement.txt` statique copié de KuCoin : obsolète dès qu'un marché change.
- Aucun test automatisé, pas de CI, pas de conteneur, pas de `pyproject.toml`.
- Identifiants de canaux Discord codés en dur.

---

## 4. Architecture cible

Réécriture structurée plutôt que rafistolage. On conserve les idées (indicateurs, Discord, modèle prédictif) sur des bases saines.

### 4.1 Indépendance vis-à-vis des plateformes : données et exécution découplées

Deux interfaces distinctes, parce que les deux besoins peuvent être servis par des plateformes différentes et changer indépendamment :

```python
class MarketDataProvider(Protocol):
    async def fetch_ohlcv(self, symbol: str, timeframe: str, since: datetime, until: datetime) -> pd.DataFrame
    async def fetch_ticker(self, symbol: str) -> Ticker
    def list_symbols(self) -> list[str]

class Broker(Protocol):
    async def balances(self) -> dict[str, Decimal]
    async def positions(self) -> list[Position]
    async def place_order(self, order: OrderRequest) -> Order     # market, limit, stop, take-profit
    async def cancel_order(self, order_id: str) -> None
    async def open_orders(self, symbol: str | None = None) -> list[Order]
    def market_rules(self, symbol: str) -> MarketRules             # tick size, lot size, minimum notionnel
```

Règles :

- **Le code métier (features, stratégie, risque, backtest) n'importe jamais ccxt ni un SDK d'exchange.** Il ne connaît que ces deux interfaces et des types internes (`Candle`, `Order`, `Position`).
- **Symboles unifiés** au format `BASE/QUOTE` (`BTC/USDC`). La conversion vers le format propre à chaque plateforme (`XBTEUR` chez Kraken, `BTC-EUR` chez Coinbase) est confinée dans l'adaptateur.
- **Règles de marché lues dynamiquement** (tick size, lot size, minimum) au démarrage, plus jamais un `priceIncrement.txt` statique.
- **Sélection par configuration** : `DATA_PROVIDER=ccxt:kraken`, `BROKER=ccxt:kraken` ou `BROKER=paper`. Changer de plateforme revient à changer ces deux valeurs.
- **Suite de tests de conformité commune** : tout adaptateur doit passer les mêmes tests (pagination OHLCV, bougies sans trou, arrondis d'ordre, erreurs réseau). On valide un nouvel adaptateur en quelques heures au lieu de le découvrir en production.
- **Jeu de données local indépendant** : tout ce qui est téléchargé est archivé en Parquet avec la source et la date de récupération. Le backtest et l'entraînement tournent sur l'archive, jamais en direct. Si une plateforme disparaît, l'historique reste.

Implémentations prévues :

| Adaptateur | Rôle | Remarque |
|---|---|---|
| `ccxt` (données et exécution) | Implémentation par défaut des deux interfaces | Plus de 100 exchanges, un seul adaptateur générique paramétré par le nom de l'exchange. Couvre Kraken, Coinbase, Bitstamp, OKX |
| `paper` (exécution) | Broker simulé alimenté par le MarketDataProvider | Même code que le live, frais et slippage configurables |
| `parquet` (données) | Lecture de l'archive locale | Backtest, entraînement, mode hors ligne |
| `csv` (données) | Import d'archives tierces (CryptoDataDownload, dumps publics) | Pour reconstituer l'historique profond si l'exchange cible en manque |
| Fallback de données | Second MarketDataProvider utilisé si le premier échoue ou s'arrête | Par exemple `ccxt:kraken` en principal, `ccxt:coinbase` en secours |

Recommandation initiale : **Kraken** pour les deux rôles, via ccxt. Agréé MiCA, API spot et futures robuste, paires USDC et EUR, historique long. Coinbase Advanced, OKX EU et Bitstamp sont les alternatives directement supportées par le même adaptateur. Prendre les données chez l'exchange d'exécution évite les écarts de prix entre source et marché réel ; un second exchange sert de secours.

### 4.2 Remplacement des jetons à levier

| Option | Avantages | Inconvénients |
|---|---|---|
| **Spot uniquement** (long BTC ou cash) | Simple, pas de liquidation, pas de frais de financement, idéal pour valider la stratégie | Pas de short, pas de levier |
| **Futures perpétuels** (long/short, levier isolé) | Équivalent réel de 3L/3S, short possible | Liquidation, frais de financement, gestion du risque critique, API plus complexe |

Recommandation : spot d'abord, futures en option une fois la stratégie validée.

### 4.3 Structure du paquet

```
bot_crypto/
├── pyproject.toml          # uv, ruff, pytest, mypy
├── .env.example            # clés API, webhooks, jamais commité
├── config/
│   └── settings.py         # pydantic-settings
├── data/
│   ├── provider.py         # interface MarketDataProvider + types Candle, Ticker
│   ├── providers/
│   │   ├── ccxt.py         # adaptateur générique ccxt (fetch_ohlcv, pagination, retry)
│   │   ├── parquet.py      # lecture de l'archive locale
│   │   ├── csv.py          # import d'archives tierces
│   │   └── fallback.py     # enchaîne un provider principal et un secours
│   ├── store.py            # archive Parquet locale, multi-paires, multi-timeframes
│   └── news.py             # ingestion RSS / API news (voir section 6)
├── features/
│   └── indicators.py       # indicateurs vectorisés (pandas-ta ou TA-Lib), normalisés, longueur fixe
├── strategy/
│   ├── base.py             # interface Strategy.signal(df) -> Signal
│   ├── rules.py            # stratégie de référence par règles (étalon)
│   ├── ml.py               # modèle LightGBM / Keras
│   └── llm.py              # couche LLM (section 6)
├── risk/
│   └── manager.py          # taille de position, SL/TP natifs, perte max jour, kill switch
├── backtest/
│   ├── engine.py           # frais, slippage, walk-forward
│   └── metrics.py          # Sharpe, Sortino, max drawdown, win rate, profit factor
├── execution/
│   ├── broker.py           # interface Broker + types Order, Position, MarketRules
│   └── brokers/
│       ├── ccxt.py         # adaptateur générique ccxt (live)
│       └── paper.py        # broker simulé, mêmes règles de marché que le live
├── notify/
│   ├── discord.py
│   └── telegram.py
├── cli.py                  # typer : fetch, train, backtest, paper, live, news
└── tests/
    ├── conformance/        # mêmes tests pour tout adaptateur données ou broker
    └── unit/
```

Principes :

- **asyncio** remplace `Process` et `Thread`.
- **logging** standard (ou structlog) avec rotation, remplace les fichiers texte maison.
- **Ordres stop natifs** sur l'exchange, le bot ne surveille pas le prix en boucle.
- **État en SQLite via SQLAlchemy** (positions, ordres, signaux, décisions LLM) pour l'audit et la reprise.
- **Mode paper trading obligatoire** avant tout passage en réel.
- **Déploiement** : Docker Compose ou service systemd avec redémarrage automatique. Plus de `nohup` ni de `kill -9`.
- **Python 3.14**, voir section 5.

### 4.4 Partie ML revue

- Cible : classification de direction (hausse / baisse / neutre sur N jours) ou régression du rendement futur. Jamais le prix absolu.
- Features de longueur fixe, normalisées (z-score glissant ou rank), sans NaN tronqués.
- Validation **walk-forward** : entraînement sur [t0, t1], test sur [t1, t2], on avance, on recommence. Jamais de mélange aléatoire.
- Modèles candidats : LightGBM / XGBoost (dominent les MLP sur du tabulaire de cette taille), régression logistique comme baseline, Keras en option.
- Comparaison systématique à une stratégie de règles simple et au buy-and-hold.
- Le modèle ne passe en paper trading que s'il bat l'étalon net de frais sur le backtest walk-forward.

---

### 4.5 Fiscalité et choix de la devise de cotation

Hors conseil fiscal ; références : article 150 VH bis du CGI et BOFiP. À faire confirmer par un professionnel pour des montants significatifs.

- **Crypto contre crypto n'est pas imposable** pour un particulier, stablecoins inclus. Le fait générateur est la conversion vers une monnaie ayant cours légal ou l'achat d'un bien ou service. La plus-value se calcule alors sur l'ensemble du portefeuille, au prorata de la part cédée. Les gains accumulés en crypto/stablecoin sont donc taxés au retrait, pas à chaque trade.
- **Conséquence pour un bot** : une paire BTC/EUR crée un fait générateur à chaque vente, donc des centaines de cessions à déclarer par an (formulaire 2086). Une paire BTC/stablecoin n'en crée qu'au retrait en euros.
- **USDT est indisponible sur les exchanges agréés MiCA** (Tether n'a pas le statut de jeton de monnaie électronique) : retiré par Coinbase en décembre 2024, Kraken en mars 2025, Binance en mars 2025 pour l'Espace économique européen. **USDC** (Circle, licence d'établissement de monnaie électronique dans l'Union) et EURC sont les stablecoins conformes.
- **Taux** : prélèvement forfaitaire unique de 30 % (12,8 % + 17,2 %), annoncé à 31,4 % à partir de 2026 selon plusieurs sources, à confirmer. Exonération si le total des cessions fiat de l'année est inférieur à 305 euros.
- **Requalification en activité professionnelle** (bénéfices non commerciaux) possible si l'activité est exercée dans des conditions analogues à celles d'un professionnel. Un bot automatisé est un indice que l'administration peut retenir. Rescrit ou expert-comptable recommandé au-delà de montants modestes.
- **Comptes à l'étranger** (Kraken en Irlande, Coinbase au Luxembourg) : formulaire 3916-bis chaque année, 750 euros d'amende par compte omis. **DAC8** : depuis le 1er janvier 2026 les exchanges transmettent automatiquement les opérations au fisc.
- **Exigence pour le bot** : conserver un historique complet et exportable de tous les trades (date, paire, quantité, prix, frais) pour reconstituer le prix d'acquisition global. Export CSV compatible avec les outils de déclaration (Waltio, Koinly).

Décision : cotation en **USDC** plutôt qu'en EUR. Le backtest mesurera la performance en euros, exposition EUR/USD incluse.

## 5. Stack technique : table rase

Aucune contrainte héritée : ni la version de Python, ni TensorFlow, ni les scripts VPS. On choisit l'outillage le plus simple et le plus rapide à faire tourner et à maintenir.

### 5.1 Langage et outillage

| Élément | Choix | Pourquoi |
|---|---|---|
| Python | **3.14** | Version stable depuis un an, écosystème complet (numpy, pandas 3, pyarrow, scipy, pydantic 2, SQLAlchemy 2, typer, ccxt, lightgbm, anthropic). Python 3.15 vient de sortir et expose au risque de paquets sans wheel pendant quelques mois pour un gain négligeable ; passage à 3.15 envisageable plus tard en changeant une ligne du pyproject et du Dockerfile. TensorFlow n'est pas disponible sur 3.14, ce qui confirme l'abandon de Keras |
| Gestionnaire de projet | **uv** | Résolution et installation très rapides, lockfile reproductible, gestion des versions de Python intégrée, remplace pip, venv, pip-tools et pyenv |
| Configuration projet | `pyproject.toml` unique | Dépendances, scripts, ruff, mypy, pytest au même endroit |
| Lint et format | **ruff** | Remplace flake8, isort, black, pyupgrade en un outil |
| Typage | **mypy** en mode strict (ou pyright) | Les interfaces de la section 4.1 n'ont de valeur que si elles sont vérifiées |
| Tests | **pytest** + pytest-asyncio + hypothesis | Tests unitaires, tests de conformité des adaptateurs, tests par propriétés sur les indicateurs |
| Hooks | pre-commit | ruff, mypy, détection de secrets avant chaque commit |
| CI | GitHub Actions | lint, typage, tests, build de l'image Docker à chaque push |

### 5.2 Bibliothèques

| Domaine | Bibliothèque | Remarque |
|---|---|---|
| Exchanges | ccxt (async) | Un seul adaptateur pour tous les exchanges |
| Données | pandas 3, numpy, pyarrow | Parquet pour l'archive. Polars en option si les volumes multi-paires multi-timeframes deviennent lourds |
| Indicateurs | pandas-ta ou TA-Lib | TA-Lib exige la bibliothèque C, ce que Docker rend indolore. pandas-ta est pur Python et suffit pour la plupart des indicateurs |
| ML | lightgbm, scikit-learn | Walk-forward, calibration, métriques. Keras abandonné |
| Modèles de données et config | pydantic 2, pydantic-settings | Validation des types internes, des sorties LLM et de la configuration .env |
| Persistance | SQLAlchemy 2 + aiosqlite | Positions, ordres, signaux, décisions LLM, news. PostgreSQL possible plus tard sans changer le code |
| HTTP et flux | httpx, feedparser | Ingestion news, appels REST hors ccxt |
| LLM | anthropic (SDK officiel) | Sorties structurées, cache de prompt, Batch API |
| Notifications | discord.py ou webhooks, python-telegram-bot | Commandes et alertes |
| CLI | typer + rich | `bot fetch`, `bot backtest`, `bot paper`, `bot live` |
| Logs | structlog | JSON en production, lisible en développement |
| Planification | asyncio natif | Une boucle, des tâches ; pas de cron, pas de threads |
| Dashboard (option) | Streamlit ou FastAPI + page statique | Equity curve, positions, décisions LLM, coûts |

### 5.3 Conteneurisation et déploiement

- **Image Docker multi-étapes** : étape de build avec uv et compilation de TA-Lib, étape finale minimale sans outils de build, utilisateur non root, base `python:3.14-slim`.
- **docker compose** avec trois services : `bot` (boucle de trading), `news` (ingestion et scoring, indépendant pour ne jamais bloquer le trading), `dashboard` (optionnel). Volumes persistants pour l'archive Parquet et la base SQLite. `restart: unless-stopped`, healthcheck sur chaque service.
- **Secrets** par fichier `.env` monté, jamais dans l'image ni dans le dépôt.
- **Un seul chemin de déploiement** : `docker compose pull && docker compose up -d`. Remplace start.py, stop.py, restart.py et recovery_error_files.py.
- **Mêmes images en local et sur le VPS** : le paper trading en local et le live sur le serveur tournent sur le même artefact.
- **Logs** collectés par Docker, consultables par `docker compose logs`, plus de rapatriement SFTP.

### 5.4 Performance

Le bot d'origine lançait des processus pour trois requêtes HTTP et parsait des listes sérialisées en texte. La nouvelle base est rapide par construction :

- Indicateurs **vectorisés** sur des colonnes entières, jamais de boucle Python ligne par ligne ni de recalcul fenêtre par fenêtre. Un backtest de 10 ans en bougies journalières se calcule en moins d'une seconde ; en bougies horaires, en quelques secondes.
- **asyncio** pour tout ce qui attend le réseau : les requêtes vers plusieurs exchanges ou plusieurs paires partent en parallèle sans processus ni threads.
- **Parquet** en colonnes : lecture de plusieurs années d'historique en millisecondes.
- **LightGBM** s'entraîne en secondes sur ce volume de données, contre des minutes pour les réseaux Keras d'origine, et sans GPU.
- Le LLM est hors du chemin critique : appelé une à quelques fois par jour, en tâche séparée, avec timeout.

## 6. Intégration d'un LLM : analyse des prédictions et des news

Deux usages demandés : (a) analyser la sortie du modèle, (b) analyser les news en temps réel. Un troisième découle naturellement : (c) expliquer les décisions en langage clair dans Discord.

### 6.1 Principe directeur : le LLM conseille, il n'exécute jamais

Le LLM ne place aucun ordre. Il produit un avis structuré (JSON validé) qui entre dans le module de risque comme n'importe quelle autre feature. Le code reste maître de la décision finale. Raisons :

- Un LLM peut se tromper avec assurance, et ses sorties ne sont pas reproductibles à l'identique.
- Il faut pouvoir backtester la contribution du LLM comme celle d'une feature : sans trace structurée, impossible de mesurer s'il aide ou nuit.
- Si l'API est indisponible, le bot doit retomber sur un comportement par défaut (modèle seul, ou pas de trade) sans planter.

### 6.2 Usage A : second avis sur la prédiction du modèle

À chaque signal du modèle, on envoie au LLM un contexte structuré :

- La prédiction (direction, probabilité ou rendement attendu).
- Les 40 dernières bougies résumées et les indicateurs clés (RSI, ADX, position par rapport aux Bollinger, volume relatif).
- Les statistiques du modèle en backtest (précision récente, drawdown en cours).
- La position actuelle, le solde, les limites de risque.
- Le résumé des news récentes (usage B).

Le LLM renvoie un verdict structuré :

```python
from pydantic import BaseModel
from typing import Literal

class AvisLLM(BaseModel):
    accord_avec_modele: bool
    confiance: Literal["faible", "moyenne", "forte"]
    facteur_taille_position: float      # 0.0 à 1.0, multiplie la taille calculée par le risk manager
    signaux_de_risque: list[str]        # ex. ["FOMC dans 24h", "volume anormalement bas"]
    justification: str                  # 3 phrases max, affichées dans Discord
```

Le risk manager applique `facteur_taille_position` et peut passer la taille à 0 (veto). La règle d'agrégation (veto strict, pondération, seuil de confiance) est un paramètre à backtester.

Appel avec le SDK Python officiel et sortie structurée validée :

```python
import anthropic

client = anthropic.Anthropic()  # clé lue depuis ANTHROPIC_API_KEY

response = client.messages.parse(
    model="claude-opus-5-5",
    max_tokens=2048,
    system=[{"type": "text", "text": SYSTEM_ANALYSTE, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": contexte_json}],
    output_format=AvisLLM,
)
avis: AvisLLM = response.parsed_output
```

Le prompt système (rôle, règles, format, rappel que la sortie est un avis) est stable et mis en cache. Le contexte variable vient après.

### 6.3 Usage B : analyse des news en temps réel

Pipeline en quatre étapes.

**1. Ingestion (asyncio, toutes les 5 à 15 min)**

| Source | Type | Coût | Remarque |
|---|---|---|---|
| Flux RSS CoinDesk, CoinTelegraph, The Block, Decrypt | RSS | Gratuit | Base solide, latence de quelques minutes |
| CryptoPanic | API REST | Gratuit avec limite, payant au-delà | Agrège des centaines de sources, votes de la communauté |
| Annonces officielles de l'exchange (statut, listings, maintenance) | RSS ou API | Gratuit | Indispensable pour le risque opérationnel |
| Calendrier macro (FOMC, CPI, NFP) | API ou fichier | Gratuit | Événements planifiés, pas des news |
| X/Twitter | API | Payant, cher | À écarter dans un premier temps |
| Reddit r/Bitcoin, r/CryptoCurrency | API | Gratuit avec limite | Bruyant, utile pour le sentiment retail |

Dédoublonnage par hash du titre normalisé, stockage en SQLite avec horodatage de **réception** (pas de publication), pour un backtest honnête.

**2. Scoring par le LLM**

Chaque lot d'articles est envoyé au LLM qui renvoie, par article, un objet structuré :

```python
class ScoreNews(BaseModel):
    pertinence_btc: Literal["nulle", "faible", "moyenne", "forte"]
    sentiment: float                     # -1.0 (très négatif) à +1.0
    impact_attendu: Literal["aucun", "faible", "moyen", "fort"]
    horizon: Literal["heures", "jours", "semaines"]
    categorie: Literal["reglementation", "macro", "hack_securite", "adoption", "marche", "autre"]
    resume: str                          # une phrase
```

Les articles sont envoyés par lots de 10 à 20 pour amortir le prompt système. Pour le traitement de l'historique (étiquetage de milliers d'articles pour le backtest), on utilise l'**API Batch** qui coûte 50 % du tarif standard.

**3. Agrégation en signal**

Un « score news » glissant sur 24 h et 7 jours : moyenne pondérée du sentiment par la pertinence et l'impact. Ce score devient :

- Une **feature** du modèle ML (à condition d'avoir l'historique pour l'entraîner).
- Et/ou un **filtre** : par exemple, pas d'ouverture de position dans les 12 h suivant une news d'impact fort de catégorie hack ou réglementation, ou dans les 24 h précédant un FOMC.

**4. Restitution**

- Un résumé quotidien dans Discord : les 5 news les plus pertinentes, le score, les risques identifiés.
- Une alerte immédiate si une news d'impact fort arrive (hack d'exchange, décision réglementaire majeure).
- Une commande Discord `!news` qui déclenche une recherche à la demande via l'outil **web search** côté serveur de l'API Claude (`web_search_20260209`) pour répondre à « que se passe-t-il sur BTC en ce moment ».

### 6.4 Piège majeur : le biais de connaissance en backtest

Un LLM connaît l'histoire jusqu'à sa date de coupure. Si on lui demande en 2026 de noter une news de mars 2023, il « sait » ce que le marché a fait ensuite. Le backtest d'une feature news produite par LLM est donc contaminé sur toute la période antérieure à la coupure du modèle.

Parades :

- Mesurer la contribution du LLM **en paper trading prospectif** (données qu'il n'a pas pu voir), sur plusieurs semaines au minimum.
- Pour le backtest historique, demander au LLM de noter l'article sans aucune référence à l'issue et comparer avec un étiquetage hors-LLM (lexique de sentiment classique) pour détecter une précision suspecte.
- Ne jamais utiliser le LLM pour prédire directement le prix sur des périodes historiques.

### 6.5 Garde-fous techniques

- **Plafond de coût** quotidien en tokens, suivi via `response.usage`, alerte Discord à 80 %.
- **Timeouts courts** (30 s) et repli : en cas d'erreur API, `facteur_taille_position = 1.0` (modèle seul) ou 0.0 (prudence), au choix dans la config.
- **Journalisation complète** de chaque appel (entrée, sortie, coût, latence) en base pour l'audit et le backtest.
- **Prompt caching** sur le prompt système pour diviser le coût d'entrée par 10 sur la partie stable.
- **Pas de secret dans le prompt** : jamais de clés, de soldes exacts non nécessaires, ni d'identifiants.
- **Fallback serveur** activé par défaut sur Opus 5.5 (`fallbacks: "default"` avec le bêta `server-side-fallback-2026-07-01`) pour qu'un refus de sécurité ne bloque pas la boucle.

### 6.6 Modèles et coût estimé

Modèle par défaut : **Claude Opus 5.5** (`claude-opus-5-5`), 4 $ / M tokens en entrée, 20 $ / M en sortie, réflexion adaptative toujours active, effort réglable (`medium` par défaut, à monter à `high` pour l'usage A). Pour le tri à haut volume des news (usage B, étape 2), Claude Haiku 5.5 (`claude-haiku-5-5`, 0,10 $ / 0,50 $ par M tokens) est une option 40 fois moins chère. Le choix revient à l'utilisateur, à valider par une comparaison de qualité sur un échantillon.

Estimation pour un bot journalier BTC, avant cache :

| Usage | Volume | Tokens entrée / sortie par appel | Coût / jour (Opus 5.5) |
|---|---|---|---|
| A. Avis sur la prédiction | 1 à 4 appels / jour | 4 000 / 500 | 0,02 à 0,10 $ |
| B. Scoring news | 200 articles / jour par lots de 20, soit 10 appels | 6 000 / 2 000 | 0,64 $ |
| C. Résumé Discord | 1 appel / jour | 8 000 / 800 | 0,05 $ |
| **Total** | | | **moins de 1 $ / jour**, moins de 0,10 $ avec Haiku pour B |

Le backfill historique de 20 000 articles en Batch API coûterait environ 50 $ sur Opus 5.5, environ 1,5 $ sur Haiku 5.5.

### 6.7 Ce que le LLM ne doit pas faire

- Prédire le prix lui-même. Ce n'est pas son point fort et c'est inévaluable.
- Décider seul d'un ordre.
- Tourner sur chaque bougie 1 minute : coût et latence inutiles pour un bot journalier.
- Recevoir des données en vrac (40 bougies brutes × 6 colonnes) sans résumé : préparer le contexte en Python coûte moins cher et donne de meilleurs résultats.

---

## 7. Nouvelles capacités

Classées par ordre de valeur pour le projet.

| Priorité | Capacité | Description |
|---|---|---|
| 1 | Backtester walk-forward | Frais, slippage, métriques, comparaison à l'étalon. Sans lui rien ne peut être validé |
| 1 | Paper trading | Même code que le live, broker simulé, obligatoire avant le réel |
| 1 | Ordres stop et take-profit natifs | Posés sur l'exchange, survivent au crash du bot |
| 2 | Multi-paires | BTC, ETH, SOL... la stratégie prend un symbole en paramètre |
| 2 | Multi-timeframes | 1h, 4h, 1d en features ; décision sur un timeframe, confirmation sur un autre |
| 2 | Couche LLM | Section 6 |
| 2 | Kill switch | Perte max journalière, perte max globale, arrêt automatique + alerte |
| 3 | Trailing stop | Suivi du stop à distance fixe ou ATR |
| 3 | DCA et grid | Stratégies alternatives sous la même interface Strategy |
| 3 | Dashboard web | Streamlit ou page légère : equity curve, positions, signaux, décisions LLM, coûts |
| 3 | Telegram | Second canal de notification et de commande |
| 4 | Futures perpétuels | Long/short avec levier isolé, une fois le spot validé |
| 4 | Portefeuille | Allocation entre plusieurs stratégies ou paires |

---

## 8. Plan par phases

Principe : **mesurer avant de construire**. Le premier projet a échoué parce que le signal n'existait pas, pas à cause de l'outillage. On obtient donc des données propres et un backtest honnête avant d'investir dans l'infrastructure d'exploitation. Chaque phase produit un résultat vérifiable avant de passer à la suivante.

| Phase | Contenu | Résultat vérifiable |
|---|---|---|
| 1. Données et outillage minimal | pyproject + uv + ruff + mypy + pytest, config .env, interfaces MarketDataProvider et Broker, adaptateurs ccxt et parquet, tests de conformité, archive Parquet, indicateurs vectorisés et normalisés. Pas de Docker, pas de Discord, pas de LLM à ce stade | `bot fetch BTC/USDC 1d --since 2019` produit un Parquet propre quel que soit l'exchange configuré ; indicateurs validés par tests, y compris par propriétés |
| 2. Backtest et étalons | Moteur walk-forward avec frais et slippage, métriques (Sharpe, Sortino, drawdown max, profit factor, taux de réussite), buy-and-hold, puis stratégies simples documentées : suivi de tendance, momentum, croisements de moyennes avec filtre de volatilité | Rapport de backtest reproductible sur 5 ans minimum. On sait ce qu'une stratégie simple rapporte net de frais sur ce marché |
| 3. ML | Cible direction ou rendement, LightGBM, validation walk-forward, comparaison aux étalons de la phase 2 | Verdict documenté : le modèle bat ou ne bat pas le meilleur étalon net de frais. **Point de décision** (voir critère d'arrêt) |
| 4. Infrastructure d'exploitation | Docker et compose, broker paper, risk manager, ordres stop natifs, Discord, état en base, reprise après redémarrage, export fiscal des trades | Bot en paper trading 2 semaines sans intervention, avec la ou les stratégies retenues |
| 5. Couche LLM (option) | Usages opérationnels d'abord : résumé des news, explication des décisions, blocage avant événement macro. Second avis sur la prédiction seulement si mesurable en prospectif | Mesure de la contribution sur 4 semaines de paper. On garde ce qui aide, on retire le reste |
| 6. Live | Capital réduit, kill switch, supervision | Premier mois en réel |
| 7. Extensions | Multi-paires, futures, dashboard, Telegram | Selon résultats |

### Critère d'arrêt

Décidé avant de commencer, pour ne pas le décider sous l'émotion d'un backtest décevant :

> Si, à l'issue de la phase 3, aucune stratégie (règles ou ML) ne bat le buy-and-hold net de frais sur au moins 5 ans en walk-forward, avec un drawdown maximum inférieur à celui du buy-and-hold, alors le projet devient un framework de trading et un outil de suivi de marché (données, backtest, news, notifications), et n'engage pas de capital. Les phases 4 à 7 sont alors réduites à ce périmètre.

Ce critère est révisable, mais par écrit et avant la phase 3, jamais après.

### Ce qu'on attend réellement du LLM

Sa valeur la plus probable est opérationnelle, pas prédictive : résumer, expliquer chaque décision en clair, signaler un événement de risque, bloquer un trade avant une annonce macro. L'idée qu'il améliore la prédiction est une hypothèse à tester avec scepticisme, difficile à mesurer en backtest à cause du biais de connaissance (section 6.4). Il reste une option, pas une promesse.

## 9. Décisions à prendre

| Décision | Recommandation | Impact |
|---|---|---|
| Exchange cible (exécution) | Kraken | Adaptateur ccxt, paires USDC, API futures |
| Fournisseur de données | Le même exchange via ccxt, Coinbase en secours, archive Parquet locale | Cohérence prix / exécution, résilience si une plateforme ferme |
| Spot seul ou futures | Spot d'abord | Complexité du risk manager et du broker |
| Devise de cotation | USDC | Un seul fait générateur fiscal au retrait, disponible sur les plateformes agréées ; USDT indisponible en Europe, EUR imposable à chaque vente (section 4.5) |
| Version de Python | 3.14 | Stable et complet ; 3.15 trop récent pour les wheels. TensorFlow indisponible, donc Keras abandonné |
| Conserver TensorFlow/Keras | Non, LightGBM et scikit-learn | Simplifie l'image Docker et l'entraînement |
| Modèle LLM pour le tri des news | Opus 5.5 par défaut, Haiku 5.5 à évaluer | Coût ×40 entre les deux sur l'usage B |
| Sources news payantes | Aucune au départ (RSS + CryptoPanic gratuit) | Couverture et latence |
| Déploiement | Docker Compose, mêmes images en local et sur le VPS | Reprend le rôle de start/stop/restart.py et de recovery_error_files.py |

---

## 10. Sources

- KuCoin quitte la France : [Journal du Coin](https://journalducoin.com/exchanges/kucoin-arrete-ses-services-pour-les-utilisateurs-francais/), [Cryptoast](https://cryptoast.fr/plateforme-crypto-kucoin-quitte-france-explique-pourquoi/), [Cointribune](https://www.cointribune.com/kucoin-se-retire-de-france-apres-avoir-ete-blackliste-par-lamf/), [Cryptonews](https://cryptonews.com/fr/news/kucoin-quitte-france-mica/)
- Délisting des jetons à levier Binance : [Cointelegraph](https://cointelegraph.com/news/binance-leveraged-token-services-shutdown), [CoinAcademy](https://coinacademy.fr/actu/binance-met-fin-service-tokens-effet-levier-deliste-6-paires-trading/), [FinanceFeeds](https://financefeeds.com/binance-to-cease-support-for-bnb-btc-and-eth-leveraged-tokens/)
- Plateformes agréées MiCA pour la France : [DefiLlama MiCA France](https://defillama.com/mica/france), [Cryptoast](https://cryptoast.fr/plateforme-crypto-autorisee-france-mica/), [Selectra](https://selectra.info/finance/actualites/marche/bitcoin-plateformes-autorisees-france-mica-amf)
- Tri MiCA et Binance : [iPhoneSoft](https://iphonesoft.fr/2026/06/24/binance-bannie-europe-1er-juillet-2026), [Cryptoast, Binance et la Grèce](https://cryptoast.fr/apres-lalerte-de-la-france-binance-cherche-a-obtenir-une-licence-mica-en-grece/), [The Big Whale](https://www.thebigwhale.io/article/mica-france-binances-last-resort-in-europe), [AMF, fin de la période transitoire](https://www.amf-france.org/fr/actualites-publications/actualites/lamf-rappelle-que-la-periode-transitoire-pour-les-psan-pour-continuer-de-fournir-des-services-sur), [Mind Fintech n°401](https://www.mind.eu.com/wp-content/uploads/sites/2/2026/08/mind-fintech-n401.pdf)
- KuCoin et l'AMF : [Cryptoast, liste noire](https://cryptoast.fr/france-kucoin-discretement-ajoute-liste-noire-autorite-marches-financiers-amf/), [Cryptoast, poursuites américaines](https://cryptoast.fr/?p=139288)
- Python 3.14 et 3.15 : [python.org](https://www.python.org/downloads/), [compatibilité des 1 000 paquets PyPI les plus utilisés avec 3.15](https://python.plainenglish.io/93-6-of-the-top-1-000-pypi-packages-are-python-3-15-ready-64-of-the-140-that-compile-are-not-3a54d8ae0534)
- Fiscalité : [CoinAcademy, guide 2026](https://coinacademy.fr/academie/guide-fiscalite-crypto-2025-declarer-comment), [Finalib, stablecoins et fiscalité](https://finalib.fr/blog/fiscalite/stablecoins-fiscalite-france-2026-usdt-usdc), [Cryptoactu, déclaration](https://cryptoactu.com/fiscalite-cryptomonnaies-declaration-impot/)
- USDT et MiCA : [Cryptoast](https://cryptoast.fr/binance-kraken-deliste-usdt-tether-europe-pressions-reglementaires/), [Journal du Coin](https://journalducoin.com/exchanges/tether-vs-mica-binance-met-fin-trading-stablecoin-usdt-europe/), [DL News, Kraken](https://dlnews.com/articles/markets/kraken-delists-tether-usdt-in-europe-as-mica-rules-take-hold/), [Glenbrook](https://glenbrook.com/payments_news/stablecoin-shakedown-binance-coinbase-and-kraken-restrict-usdt-in-europe-ahead-of-mica-deadline/)
- ccxt : [PyPI](https://pypi.org/project/ccxt/), [dépôt GitHub](https://github.com/ccxt/ccxt)
- API Claude : [documentation](https://platform.claude.com/docs), [SDK Python](https://github.com/anthropics/anthropic-sdk-python)
