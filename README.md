# Polymarket Trading Bot

Automated trading bot for Polymarket's Bitcoin 15-minute Up/Down markets.

## Features

- **Automated Market Detection**: Finds active Bitcoin 15min Up/Down markets
- **Smart Entry Strategy**: 
  - Enters when price increases 5% from recent low
  - OR when price exceeds $0.60 (if 5% condition not met)
- **Dynamic Exit Strategy**: 
  - Exits when position drops 5% from its high
  - Automatically flips to inverse position (UP ↔ DOWN)
- **Position Tracking**: Maintains history and calculates P&L
- **Comprehensive Logging**: Detailed logs of all trading decisions

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Credentials

Edit `config.json` and add your Polymarket credentials:

```json
{
  "api_credentials": {
    "api_key": "YOUR_POLYMARKET_API_KEY",
    "private_key": "YOUR_PRIVATE_KEY",
    "wallet_address": "YOUR_WALLET_ADDRESS"
  }
}
```

### 3. Adjust Trading Parameters (Optional)

Modify trading parameters in `config.json`:

- `position_value_usdc`: Amount to trade per position (default: $10)
- `entry_threshold_percent`: Entry trigger percentage (default: 5%)
- `entry_price_threshold`: Absolute price entry threshold (default: $0.60)
- `exit_reversal_percent`: Exit trigger percentage (default: 5%)
- `check_interval_seconds`: Price check frequency (default: 1 second)

## Usage

### Run the Bot

```bash
python main.py
```

### Stop the Bot

Press `Ctrl+C` to gracefully shutdown the bot.

## File Structure

```
polymarket-trading-bot/
├── main.py                    # Main bot orchestration
├── polymarket_client.py       # Polymarket API wrapper
├── trading_strategy.py        # Trading logic and signals
├── position_tracker.py        # Position management and P&L tracking
├── logger_config.py           # Logging configuration
├── config.json                # Configuration file
├── requirements.txt           # Python dependencies
├── trading_bot.log           # Log file (created on first run)
└── position_history.json     # Position history (created on first trade)
```

## How It Works

### Entry Logic

The bot monitors UP and DOWN token prices and enters a position when:

1. **5% Increase from Low**: Price increases 5% from its recent low, OR
2. **Price Threshold**: Price exceeds $0.60 (only if condition 1 hasn't been met)

### Exit/Reversal Logic

Once in a position, the bot:

1. Tracks the position's high price
2. Exits when price drops 5% from the high
3. Immediately flips to the inverse position (e.g., close UP → open DOWN)

### Example Flow

```
1. UP price: $0.45 → $0.47 (4.4% increase) → No action
2. UP price: $0.47 → $0.50 (11% from low) → ENTER UP position
3. UP reaches high of $0.55
4. UP drops to $0.52 (5.4% from high) → EXIT UP, ENTER DOWN
5. DOWN reaches high of $0.58
6. DOWN drops to $0.55 (5.2% from high) → EXIT DOWN, ENTER UP
... continues ...
```

## Deployment on VPS

### Using systemd (Linux)

1. Create a service file `/etc/systemd/system/polymarket-bot.service`:

```ini
[Unit]
Description=Polymarket Trading Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/polymarket-trading-bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:

```bash
sudo systemctl enable polymarket-bot
sudo systemctl start polymarket-bot
```

3. Check status:

```bash
sudo systemctl status polymarket-bot
```

### Using screen (Linux/Mac)

```bash
screen -S polymarket-bot
python main.py
# Press Ctrl+A then D to detach
```

To reattach:
```bash
screen -r polymarket-bot
```

## Monitoring

### View Logs

```bash
tail -f trading_bot.log
```

### Check Position History

```bash
cat position_history.json
```

## Safety Features

- **Graceful Shutdown**: Handles SIGINT and SIGTERM signals
- **Error Recovery**: Continues running after API errors
- **Balance Checking**: Verifies sufficient USDC before starting
- **Comprehensive Logging**: All decisions logged for audit

## Risk Warnings

⚠️ **Important Considerations**:

- This bot trades with real money on real markets
- The reversal strategy can lead to frequent position flipping in volatile markets
- Always start with small position sizes for testing
- Monitor the bot regularly, especially in the first few hours
- Ensure you have adequate USDC balance for multiple position flips
- Past performance does not guarantee future results

## Troubleshooting

### Bot won't start

- Check API credentials in `config.json`
- Verify USDC balance is sufficient
- Check internet connection

### No trades executing

- Verify Bitcoin 15min market is active on Polymarket
- Check if entry conditions are too strict (adjust thresholds in config)
- Review logs for error messages

### Frequent position flipping

- This is expected in volatile markets
- Consider increasing `exit_reversal_percent` to reduce sensitivity
- Monitor P&L to ensure strategy is profitable

## License

MIT License - Use at your own risk
