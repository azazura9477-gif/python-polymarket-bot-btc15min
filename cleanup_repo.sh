#!/bin/bash
# Script pour nettoyer le repo et garder uniquement les fichiers essentiels

echo "🧹 Nettoyage du repository..."

# Fichiers à supprimer (utilitaires/debug)
FILES_TO_DELETE=(
    "create_wallet.py"
    "test_balance.py"
    "test_balance_mock.py"
    "test_network.py"
    "scrape_condition_id.py"
    "get_tokens_from_condition.py"
    "market_finder.py"
    "debug_markets.py"
    "find_active_btc_market.py"
)

# Supprimer les fichiers
for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "  ❌ Suppression: $file"
        git rm "$file"
    fi
done

echo ""
echo "✅ Fichiers conservés (essentiels):"
echo "  📄 main.py - Point d'entrée du bot"
echo "  📄 polymarket_client.py - Client API Polymarket"
echo "  📄 trading_strategy.py - Logique de stratégie"
echo "  📄 position_tracker.py - Suivi des positions"
echo "  📄 logger_config.py - Configuration des logs"
echo "  📄 deposit_usdc.py - Configuration des allowances"
echo "  📄 config.example.json - Template de configuration"
echo "  📄 requirements.txt - Dépendances Python"
echo "  📄 README.md - Documentation"
echo ""
echo "Commit des changements..."
git commit -m "Cleanup: Suppression fichiers debug/utilitaires, conservation fichiers essentiels"

echo ""
echo "✅ Nettoyage terminé!"
echo ""
echo "Pour pousser les changements:"
echo "  git push origin main"
