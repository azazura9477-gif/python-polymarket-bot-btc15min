# 🤖 Polymarket BTC 15min Trading Bot

Bot de trading automatique pour les marchés Polymarket "Bitcoin Up or Down - 15min".

## 📋 Fonctionnalités

- ✅ **Détection automatique** des marchés BTC 15min actifs via web scraping
- ✅ **Stratégie de trading** configurable (prix seuil, momentum)
- ✅ **Gestion des positions** avec suivi P&L
- ✅ **Logging détaillé** de toutes les opérations
- ✅ **Reconnexion automatique** aux nouveaux marchés (toutes les 15 minutes)

## 🚀 Installation

### Prérequis

- Python 3.10+
- Wallet Ethereum avec fonds sur Polygon
  - MATIC pour les frais de gas (~0.1 MATIC recommandé)
  - USDC pour trader (minimum 10 USDC recommandé)

### Installation des dépendances

```bash
# Cloner le repository
git clone https://github.com/azazura9477-gif/python-polymarket-bot-btc15min.git
cd python-polymarket-bot-btc15min

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Créer le fichier de configuration

```bash
cp config.example.json config.json
```

### 2. Éditer config.json

```json
{
  "api_credentials": {
    "api_key": "YOUR_POLYMARKET_API_KEY",
    "private_key": "0xVOTRE_CLE_PRIVEE",
    "wallet_address": "0xVOTRE_ADRESSE_WALLET"
  },
  "trading_parameters": {
    "position_value_usdc": 10,
    "entry_threshold_percent": 5.0,
    "entry_price_threshold": 0.60,
    "exit_reversal_percent": 5.0,
    "check_interval_seconds": 1
  },
  "market_settings": {
    "market_keywords": ["bitcoin", "btc", "15min", "15 min", "up", "down"],
    "manual_condition_id": null
  },
  "logging": {
    "log_file": "trading_bot.log",
    "log_level": "INFO"
  }
}
```

**Paramètres de trading :**
- `position_value_usdc`: Montant en USDC par position (min 2, recommandé 10+)
- `entry_threshold_percent`: % d'augmentation depuis le bas pour entrer (défaut: 5%)
- `entry_price_threshold`: Prix maximum pour acheter (défaut: 0.60 = sous-évalué)
- `exit_reversal_percent`: % de baisse depuis le haut pour sortir (défaut: 5%)

### 3. Configurer les allowances (OBLIGATOIRE avant de trader)

```bash
# Vérifier les allowances actuelles
python deposit_usdc.py --check

# Configurer les allowances (à faire UNE SEULE FOIS)
python deposit_usdc.py
```

Cette étape autorise les contrats Polymarket à utiliser vos USDC. Coût : ~0.01-0.05 MATIC en gas fees.

## 🎯 Utilisation

### Lancer le bot

```bash
python main.py
```

Le bot va :
1. 🔍 Chercher automatiquement le marché BTC 15min actif
2. 📊 Surveiller les prix en temps réel
3. 💰 Placer des ordres selon la stratégie configurée
4. 📈 Suivre les positions et calculer le P&L
5. 🔄 Se reconnecter au prochain marché automatiquement

### Arrêter le bot

Appuyez sur `Ctrl+C` pour arrêter proprement le bot.

## 📊 Stratégie de trading

### Conditions d'entrée

Le bot entre en position (achète UP ou DOWN) quand **l'une de ces conditions** est remplie :

1. **Momentum** : Le prix augmente de 5% depuis son plus bas récent
2. **Sous-évaluation** : Le prix est ≤ $0.60 (bon deal, market sous-évalue la probabilité)

### Condition de sortie

Le bot sort et **inverse** la position quand :
- Le prix baisse de 5% depuis son plus haut récent

**Exemple** :
- Marché actif : "Bitcoin Up or Down - 5:30PM-5:45PM ET"
- Prix UP : $0.55 → **ACHAT** (sous-évalué)
- Prix monte à $0.70 (nouveau plus haut)
- Prix baisse à $0.665 (5% de baisse) → **VENTE + ACHAT DOWN**

## 📁 Structure des fichiers

```
python-polymarket-bot-btc15min/
├── main.py                   # Point d'entrée du bot
├── polymarket_client.py      # Client API Polymarket
├── trading_strategy.py       # Logique de stratégie
├── position_tracker.py       # Suivi des positions
├── logger_config.py          # Configuration des logs
├── deposit_usdc.py           # Configuration des allowances
├── config.example.json       # Template de configuration
├── requirements.txt          # Dépendances Python
└── README.md                 # Ce fichier
```

## 🔧 Dépannage

### Le bot ne trouve pas de marché

```
No active BTC 15min market found
```

**Solution** : Les marchés BTC 15min sont créés uniquement pendant les heures de trading US (9h-17h ET / 14h-22h UTC). Attendez ces horaires.

### Erreur "insufficient allowance"

```
Error placing order: insufficient allowance
```

**Solution** : Exécutez `python deposit_usdc.py` pour configurer les allowances.

### Erreur "invalid amount for order"

```
invalid amount for a marketable BUY order, min size: $1
```

**Solution** : Augmentez `position_value_usdc` à au moins 2 dans `config.json`.

### Erreur de connexion RPC

```
Error connecting to Polygon RPC
```

**Solution** : Le bot utilise plusieurs RPC en fallback. Vérifiez votre connexion internet.

## 📝 Logs

Les logs sont sauvegardés dans `trading_bot.log` et affichés dans le terminal :

```
2026-01-02 22:31:39 - PolymarketBot - INFO - ✅ Found active market!
2026-01-02 22:31:39 - PolymarketBot - INFO - Question: Bitcoin Up or Down - January 2, 5:30PM-5:45PM ET
2026-01-02 22:31:40 - PolymarketBot - INFO - ✓ Order placed: BUY 10.1 shares at $0.99
2026-01-02 22:31:40 - PolymarketBot - INFO - Entered UP position at $0.9900
```

## ⚠️ Avertissements

- **Risque financier** : Ce bot trade de l'argent réel. Testez d'abord avec de petites sommes.
- **Pas de garantie** : Aucune garantie de profit. Vous pouvez perdre de l'argent.
- **Gas fees** : Chaque transaction coûte du MATIC (~$0.01-0.05).
- **Frais Polymarket** : Polymarket prélève des frais sur les gains.

## 🔐 Sécurité

- ⚠️ **NE JAMAIS** commiter `config.json` avec vos vraies clés
- ⚠️ Gardez votre `private_key` secrète
- ✅ Utilisez un wallet dédié au trading (pas votre wallet principal)
- ✅ Ne stockez que les fonds nécessaires sur ce wallet

## 📚 Ressources

- [Polymarket Docs](https://docs.polymarket.com/)
- [py-clob-client](https://github.com/Polymarket/py-clob-client)
- [Polygon Network](https://polygon.technology/)

## 📄 Licence

MIT License - Utilisez à vos propres risques.

## 🤝 Support

Pour toute question ou problème, ouvrez une issue sur GitHub.

---

**Disclaimer** : Ce bot est fourni "tel quel" sans garantie. L'utilisation de ce bot est à vos propres risques. Les auteurs ne sont pas responsables des pertes financières.
