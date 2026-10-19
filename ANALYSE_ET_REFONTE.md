# Bot_crypto : analyse de l'existant et plan de refonte

Document rédigé le 19 octobre 2026 à partir d'une lecture complète du dépôt (483 commits, mai 2022 à avril 2024, 2 659 lignes Python).

Table des matières :

1. [Ce que fait le projet actuel](#1-ce-que-fait-le-projet-actuel)
2. [Pourquoi il ne peut pas redémarrer tel quel](#2-pourquoi-il-ne-peut-pas-redémarrer-tel-quel)
3. [État du code](#3-état-du-code)
4. [Architecture cible](#4-architecture-cible)
5. [Intégration d'un LLM : analyse des prédictions et des news](#5-intégration-dun-llm--analyse-des-prédictions-et-des-news)
6. [Nouvelles capacités](#6-nouvelles-capacités)
7. [Plan par phases](#7-plan-par-phases)
8. [Décisions à prendre](#8-décisions-à-prendre)
9. [Sources](#9-sources)

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

### 2.2 Binance a délisté les jetons à levier BTCUP et BTCDOWN

Binance a arrêté le trading de ses jetons à levier appariés USDT (BTCUP, BTCDOWN, ETHUP, ETHDOWN, BNBUP, BNBDOWN) puis les a délistés. Ces deux séries étaient les entrées de deux des trois modèles et des deux tiers de la règle de décision. **Le signal d'achat ne peut donc plus être calculé.**

### 2.3 Les jetons 3L/3S n'existent pas chez les exchanges agréés MiCA

L'équivalent fonctionnel (exposition long ou short avec levier) est le futures perpétuel ou le margin. Pour la France, les plateformes agréées MiCA qui proposent des perpétuels sont Coinbase, OKX EU, Kraken, Bitstamp, Backpack EU et Nexo (29 plateformes agréées au total au 16 octobre 2026).

### 2.4 Le code ne démarre pas en local

| Problème | Détail |
|---|---|
| Fichiers de poids | `main.py` charge `model.weights.h5` mais le dépôt contient `model.h5` |
| Version Keras | Modèles sauvés avec Keras 2.12 (`batch_input_shape` dans le JSON), requirements.txt vise TensorFlow 2.16 / Keras 3.2 |
| Python | Python 3.14 par défaut sur la machine, TensorFlow ne le supporte pas. Python 3.12 est disponible dans `~/.local/bin` |
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

### 4.1 Plateforme : ccxt + exchange agréé MiCA

La bibliothèque **ccxt** unifie plus de 100 exchanges derrière une seule API (données OHLCV, soldes, ordres, positions). Changer d'exchange devient un paramètre de configuration. Plus jamais de dépendance à un seul fournisseur.

Recommandation : **Kraken** en premier choix (agréé MiCA, API spot et futures robuste, paires EUR, historique long, bonne stabilité). Alternatives : Coinbase Advanced, OKX EU, Bitstamp.

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
│   ├── exchange.py         # adaptateur ccxt (fetch_ohlcv, pagination, retry)
│   ├── store.py            # cache Parquet local, multi-paires, multi-timeframes
│   └── news.py             # ingestion RSS / API news (voir section 5)
├── features/
│   └── indicators.py       # indicateurs vectorisés (pandas-ta ou TA-Lib), normalisés, longueur fixe
├── strategy/
│   ├── base.py             # interface Strategy.signal(df) -> Signal
│   ├── rules.py            # stratégie de référence par règles (étalon)
│   ├── ml.py               # modèle LightGBM / Keras
│   └── llm.py              # couche LLM (section 5)
├── risk/
│   └── manager.py          # taille de position, SL/TP natifs, perte max jour, kill switch
├── backtest/
│   ├── engine.py           # frais, slippage, walk-forward
│   └── metrics.py          # Sharpe, Sortino, max drawdown, win rate, profit factor
├── execution/
│   ├── broker.py           # interface Broker (place, cancel, positions)
│   ├── paper.py            # paper trading
│   └── live.py             # ccxt live
├── notify/
│   ├── discord.py
│   └── telegram.py
├── cli.py                  # typer : fetch, train, backtest, paper, live, news
└── tests/
```

Principes :

- **asyncio** remplace `Process` et `Thread`.
- **logging** standard (ou structlog) avec rotation, remplace les fichiers texte maison.
- **Ordres stop natifs** sur l'exchange, le bot ne surveille pas le prix en boucle.
- **État en SQLite via SQLAlchemy** (positions, ordres, signaux, décisions LLM) pour l'audit et la reprise.
- **Mode paper trading obligatoire** avant tout passage en réel.
- **Déploiement** : Docker Compose ou service systemd avec redémarrage automatique. Plus de `nohup` ni de `kill -9`.
- **Python 3.12** si TensorFlow est conservé, sinon 3.13+ avec LightGBM.

### 4.4 Partie ML revue

- Cible : classification de direction (hausse / baisse / neutre sur N jours) ou régression du rendement futur. Jamais le prix absolu.
- Features de longueur fixe, normalisées (z-score glissant ou rank), sans NaN tronqués.
- Validation **walk-forward** : entraînement sur [t0, t1], test sur [t1, t2], on avance, on recommence. Jamais de mélange aléatoire.
- Modèles candidats : LightGBM / XGBoost (dominent les MLP sur du tabulaire de cette taille), régression logistique comme baseline, Keras en option.
- Comparaison systématique à une stratégie de règles simple et au buy-and-hold.
- Le modèle ne passe en paper trading que s'il bat l'étalon net de frais sur le backtest walk-forward.

---

## 5. Intégration d'un LLM : analyse des prédictions et des news

Deux usages demandés : (a) analyser la sortie du modèle, (b) analyser les news en temps réel. Un troisième découle naturellement : (c) expliquer les décisions en langage clair dans Discord.

### 5.1 Principe directeur : le LLM conseille, il n'exécute jamais

Le LLM ne place aucun ordre. Il produit un avis structuré (JSON validé) qui entre dans le module de risque comme n'importe quelle autre feature. Le code reste maître de la décision finale. Raisons :

- Un LLM peut se tromper avec assurance, et ses sorties ne sont pas reproductibles à l'identique.
- Il faut pouvoir backtester la contribution du LLM comme celle d'une feature : sans trace structurée, impossible de mesurer s'il aide ou nuit.
- Si l'API est indisponible, le bot doit retomber sur un comportement par défaut (modèle seul, ou pas de trade) sans planter.

### 5.2 Usage A : second avis sur la prédiction du modèle

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

### 5.3 Usage B : analyse des news en temps réel

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

### 5.4 Piège majeur : le biais de connaissance en backtest

Un LLM connaît l'histoire jusqu'à sa date de coupure. Si on lui demande en 2026 de noter une news de mars 2023, il « sait » ce que le marché a fait ensuite. Le backtest d'une feature news produite par LLM est donc contaminé sur toute la période antérieure à la coupure du modèle.

Parades :

- Mesurer la contribution du LLM **en paper trading prospectif** (données qu'il n'a pas pu voir), sur plusieurs semaines au minimum.
- Pour le backtest historique, demander au LLM de noter l'article sans aucune référence à l'issue et comparer avec un étiquetage hors-LLM (lexique de sentiment classique) pour détecter une précision suspecte.
- Ne jamais utiliser le LLM pour prédire directement le prix sur des périodes historiques.

### 5.5 Garde-fous techniques

- **Plafond de coût** quotidien en tokens, suivi via `response.usage`, alerte Discord à 80 %.
- **Timeouts courts** (30 s) et repli : en cas d'erreur API, `facteur_taille_position = 1.0` (modèle seul) ou 0.0 (prudence), au choix dans la config.
- **Journalisation complète** de chaque appel (entrée, sortie, coût, latence) en base pour l'audit et le backtest.
- **Prompt caching** sur le prompt système pour diviser le coût d'entrée par 10 sur la partie stable.
- **Pas de secret dans le prompt** : jamais de clés, de soldes exacts non nécessaires, ni d'identifiants.
- **Fallback serveur** activé par défaut sur Opus 5.5 (`fallbacks: "default"` avec le bêta `server-side-fallback-2026-07-01`) pour qu'un refus de sécurité ne bloque pas la boucle.

### 5.6 Modèles et coût estimé

Modèle par défaut : **Claude Opus 5.5** (`claude-opus-5-5`), 4 $ / M tokens en entrée, 20 $ / M en sortie, réflexion adaptative toujours active, effort réglable (`medium` par défaut, à monter à `high` pour l'usage A). Pour le tri à haut volume des news (usage B, étape 2), Claude Haiku 5.5 (`claude-haiku-5-5`, 0,10 $ / 0,50 $ par M tokens) est une option 40 fois moins chère. Le choix revient à l'utilisateur, à valider par une comparaison de qualité sur un échantillon.

Estimation pour un bot journalier BTC, avant cache :

| Usage | Volume | Tokens entrée / sortie par appel | Coût / jour (Opus 5.5) |
|---|---|---|---|
| A. Avis sur la prédiction | 1 à 4 appels / jour | 4 000 / 500 | 0,02 à 0,10 $ |
| B. Scoring news | 200 articles / jour par lots de 20, soit 10 appels | 6 000 / 2 000 | 0,64 $ |
| C. Résumé Discord | 1 appel / jour | 8 000 / 800 | 0,05 $ |
| **Total** | | | **moins de 1 $ / jour**, moins de 0,10 $ avec Haiku pour B |

Le backfill historique de 20 000 articles en Batch API coûterait environ 50 $ sur Opus 5.5, environ 1,5 $ sur Haiku 5.5.

### 5.7 Ce que le LLM ne doit pas faire

- Prédire le prix lui-même. Ce n'est pas son point fort et c'est inévaluable.
- Décider seul d'un ordre.
- Tourner sur chaque bougie 1 minute : coût et latence inutiles pour un bot journalier.
- Recevoir des données en vrac (40 bougies brutes × 6 colonnes) sans résumé : préparer le contexte en Python coûte moins cher et donne de meilleurs résultats.

---

## 6. Nouvelles capacités

Classées par ordre de valeur pour le projet.

| Priorité | Capacité | Description |
|---|---|---|
| 1 | Backtester walk-forward | Frais, slippage, métriques, comparaison à l'étalon. Sans lui rien ne peut être validé |
| 1 | Paper trading | Même code que le live, broker simulé, obligatoire avant le réel |
| 1 | Ordres stop et take-profit natifs | Posés sur l'exchange, survivent au crash du bot |
| 2 | Multi-paires | BTC, ETH, SOL... la stratégie prend un symbole en paramètre |
| 2 | Multi-timeframes | 1h, 4h, 1d en features ; décision sur un timeframe, confirmation sur un autre |
| 2 | Couche LLM | Section 5 |
| 2 | Kill switch | Perte max journalière, perte max globale, arrêt automatique + alerte |
| 3 | Trailing stop | Suivi du stop à distance fixe ou ATR |
| 3 | DCA et grid | Stratégies alternatives sous la même interface Strategy |
| 3 | Dashboard web | Streamlit ou page légère : equity curve, positions, signaux, décisions LLM, coûts |
| 3 | Telegram | Second canal de notification et de commande |
| 4 | Futures perpétuels | Long/short avec levier isolé, une fois le spot validé |
| 4 | Portefeuille | Allocation entre plusieurs stratégies ou paires |

---

## 7. Plan par phases

Chaque phase produit un résultat vérifiable avant de passer à la suivante.

| Phase | Contenu | Résultat vérifiable |
|---|---|---|
| 1. Socle | pyproject, config .env, adaptateur ccxt, cache Parquet, indicateurs corrigés et normalisés, logging, tests unitaires | `bot fetch BTC/EUR 1d --since 2017` produit un Parquet propre, indicateurs validés par tests |
| 2. Backtest et étalon | Moteur walk-forward, métriques, stratégie de règles de référence, buy-and-hold | Rapport de backtest reproductible sur 5 ans avec frais |
| 3. ML revu | Cible direction/rendement, LightGBM, validation walk-forward, comparaison à l'étalon | Le modèle bat ou ne bat pas l'étalon : décision documentée |
| 4. Paper trading | Broker simulé, risk manager, Discord, état en base, reprise après redémarrage, Docker/systemd | Bot qui tourne 2 semaines sans intervention en paper |
| 5. Couche LLM | Usages A, B, C, journalisation, plafond de coût, évaluation prospective en paper | Mesure de la contribution du LLM sur 4 semaines de paper |
| 6. Live | Capital réduit, kill switch, supervision | Premier mois en réel |
| 7. Extensions | Multi-paires, futures, dashboard, Telegram | Selon résultats |

---

## 8. Décisions à prendre

| Décision | Recommandation | Impact |
|---|---|---|
| Exchange cible | Kraken | Adaptateur ccxt, paires EUR ou USD, API futures |
| Spot seul ou futures | Spot d'abord | Complexité du risk manager et du broker |
| Devise de cotation | EUR | Fiscalité et lisibilité, liquidité un peu moindre qu'USDT |
| Conserver TensorFlow/Keras | Non, LightGBM d'abord, Keras en option | Python 3.12 obligatoire si Keras conservé |
| Modèle LLM pour le tri des news | Opus 5.5 par défaut, Haiku 5.5 à évaluer | Coût ×40 entre les deux sur l'usage B |
| Sources news payantes | Aucune au départ (RSS + CryptoPanic gratuit) | Couverture et latence |
| Déploiement | Docker Compose sur le VPS existant | Reprend le rôle de start/stop/restart.py |

---

## 9. Sources

- KuCoin quitte la France : [Journal du Coin](https://journalducoin.com/exchanges/kucoin-arrete-ses-services-pour-les-utilisateurs-francais/), [Cryptoast](https://cryptoast.fr/plateforme-crypto-kucoin-quitte-france-explique-pourquoi/), [Cointribune](https://www.cointribune.com/kucoin-se-retire-de-france-apres-avoir-ete-blackliste-par-lamf/), [Cryptonews](https://cryptonews.com/fr/news/kucoin-quitte-france-mica/)
- Délisting des jetons à levier Binance : [Cointelegraph](https://cointelegraph.com/news/binance-leveraged-token-services-shutdown), [CoinAcademy](https://coinacademy.fr/actu/binance-met-fin-service-tokens-effet-levier-deliste-6-paires-trading/), [FinanceFeeds](https://financefeeds.com/binance-to-cease-support-for-bnb-btc-and-eth-leveraged-tokens/)
- Plateformes agréées MiCA pour la France : [DefiLlama MiCA France](https://defillama.com/mica/france), [Cryptoast](https://cryptoast.fr/plateforme-crypto-autorisee-france-mica/), [Selectra](https://selectra.info/finance/actualites/marche/bitcoin-plateformes-autorisees-france-mica-amf)
- ccxt : [PyPI](https://pypi.org/project/ccxt/), [dépôt GitHub](https://github.com/ccxt/ccxt)
- API Claude : [documentation](https://platform.claude.com/docs), [SDK Python](https://github.com/anthropics/anthropic-sdk-python)
