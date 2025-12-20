# Crypto Pump Alert Bot 🚀

A Telegram bot that monitors DexScreener for potential cryptocurrency pump signals across multiple blockchain networks (BSC, Ethereum, Solana, Base, and more).

## ⚠️ Important Disclaimer

**This bot provides informational signals only and is NOT financial advice.** The signals generated are based on simple heuristics and do not guarantee profitability. Cryptocurrency trading involves substantial risk of loss. Always:

- Do Your Own Research (DYOR)
- Never invest more than you can afford to lose
- Be aware of market manipulation and scams
- Understand the risks of trading volatile assets

**The authors and contributors are not responsible for any financial losses incurred through the use of this bot.**

## Features

- 🌐 **Multi-Network Support**: Monitor BSC, Ethereum, Solana, Base, and other networks
- 📊 **Heuristic Pump Detection**: Alerts based on price change, volume ratio, and liquidity thresholds
- 🔔 **Telegram Notifications**: Real-time alerts sent to your Telegram chat/channel/group
- 🛡️ **Anti-Spam**: Configurable cooldown period to prevent duplicate alerts
- 🐳 **Honeypot Check Hook**: Extensible structure for future honeypot detection integration
- 🔄 **Auto-Retry**: Graceful handling of API rate limits and network errors
- 📝 **Detailed Logging**: Comprehensive logging for debugging and monitoring

## How It Works

The bot polls the DexScreener public API at regular intervals to discover new token pairs. For each pair, it checks if the following criteria are met:

1. **Price Change (5m)** > threshold (default: 8%)
2. **Volume Ratio** > threshold (default: 3x) - compares current 5-minute volume to average 5-minute volume over the last 6 hours
3. **Liquidity (USD)** > threshold (default: $30,000)

When all criteria are met and the pair hasn't been alerted within the anti-spam window (default: 15 minutes), the bot sends a formatted alert to your configured Telegram chat.

## Requirements

- Python 3.11 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A Telegram Chat ID (your personal chat, group, or channel)

## Quick Start

### Option 1: Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kissismeowww19-droid/crypto_predictor.git
   cd crypto_predictor
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your bot token and chat ID
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **View logs**:
   ```bash
   docker-compose logs -f
   ```

5. **Stop the bot**:
   ```bash
   docker-compose down
   ```

### Option 2: Using Python Virtual Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kissismeowww19-droid/crypto_predictor.git
   cd crypto_predictor
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your bot token and chat ID
   ```

5. **Run the bot**:
   ```bash
   python src/bot.py
   ```

### Option 3: Using systemd (Production on Linux)

1. **Follow steps 1-4 from Option 2**

2. **Edit the systemd service file**:
   ```bash
   nano crypto-pump-alert.service
   ```
   
   Update the following placeholders:
   - `YOUR_USERNAME`: Your Linux username
   - `/path/to/crypto_predictor`: Absolute path to the repository

3. **Install the service**:
   ```bash
   sudo cp crypto-pump-alert.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable crypto-pump-alert
   sudo systemctl start crypto-pump-alert
   ```

4. **Check status**:
   ```bash
   sudo systemctl status crypto-pump-alert
   ```

5. **View logs**:
   ```bash
   sudo journalctl -u crypto-pump-alert -f
   ```

## Configuration

All configuration is done via environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Your Telegram bot token from @BotFather | *Required* |
| `CHAT_ID` | Your Telegram chat/group/channel ID | *Required* |
| `NETWORKS` | Comma-separated list of networks to monitor | `bsc,eth,solana,base` |
| `THRESH_PRICE` | Minimum price change % in last 5 minutes | `8.0` |
| `THRESH_VOL_RATIO` | Minimum volume ratio (5m vs 6h average) | `3.0` |
| `THRESH_LIQ_USD` | Minimum liquidity in USD | `30000` |
| `POLL_INTERVAL_SEC` | Seconds between scans (min: 30) | `45` |
| `ANTISPAM_SECONDS` | Cooldown period per pair (seconds) | `900` (15 min) |
| `HONEYPOT_CHECK_ENABLED` | Enable honeypot detection (if API available) | `false` |

### Getting Your Chat ID

1. Start a chat with your bot on Telegram
2. Send any message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id": YOUR_CHAT_ID}` in the JSON response

**For channels**: Use the channel username with `@` prefix (e.g., `@mychannel`)  
**For groups**: Use the numeric group ID (can be negative, e.g., `-1001234567890`)

### Supported Networks

The bot supports any network available on DexScreener, including:
- `bsc` - Binance Smart Chain
- `eth` - Ethereum
- `solana` - Solana
- `base` - Base
- `polygon` - Polygon
- `arbitrum` - Arbitrum
- `optimism` - Optimism
- `avalanche` - Avalanche
- `fantom` - Fantom

See [DexScreener documentation](https://docs.dexscreener.com/) for a complete list.

## Bot Commands

Once the bot is running, you can interact with it via Telegram:

- `/start` - Display bot information and configuration
- `/status` - Check current monitoring status
- `/help` - Show help message with threshold information

## Architecture

```
src/
├── bot.py           # Main bot logic and Telegram handlers
├── config.py        # Configuration management from environment variables
├── dex_monitor.py   # DexScreener API integration and pump signal detection
└── alert_cache.py   # Anti-spam caching for alerted pairs
```

## API Rate Limits

The bot implements automatic retry with exponential backoff for network errors and respects DexScreener's rate limits:

- Automatic retry on timeout/network errors (up to 3 attempts)
- Respect `Retry-After` header on 429 responses
- Default polling interval: 45 seconds (configurable)

## Honeypot Detection

The bot includes a placeholder for honeypot detection. To integrate a honeypot detection service:

1. Implement the `check_honeypot()` method in `src/dex_monitor.py`
2. Add any required API keys to `.env`
3. Set `HONEYPOT_CHECK_ENABLED=true` in `.env`

Example free services (integration not included):
- honeypot.is
- tokensniffer.com

## Troubleshooting

### Bot doesn't start

- Check that `BOT_TOKEN` and `CHAT_ID` are correctly set in `.env`
- Verify the bot token with @BotFather
- Ensure Python 3.11+ is installed

### No alerts received

- Check logs for errors
- Verify network connectivity
- Lower thresholds temporarily to test (e.g., `THRESH_PRICE=1.0`)
- Ensure `CHAT_ID` is correct

### Rate limit errors

- Increase `POLL_INTERVAL_SEC` (e.g., to 60 or 90 seconds)
- Reduce number of monitored networks

## Security Considerations

- Never commit your `.env` file with real credentials
- Use read-only API keys where possible
- Run the bot with minimal system permissions (see systemd hardening options)
- Be cautious of honeypot tokens and rug pulls
- Always verify token contracts before trading

## Limitations

- **Heuristic-based**: Signals are based on simple price/volume metrics, not ML/AI
- **Public API**: Limited to DexScreener's public API endpoints
- **No guarantees**: Past performance does not indicate future results
- **Market risks**: Pump signals may be artificial or manipulated
- **API availability**: Dependent on DexScreener API uptime

## Development

### Running in Development Mode

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit .env
cp .env.example .env

# Run with debug logging
python src/bot.py
```

### Code Style

The code uses:
- Type hints where practical
- Async/await for I/O operations
- Structured logging
- Environment-based configuration

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:

1. Follow the existing code style
2. Add appropriate logging
3. Update documentation
4. Test your changes thoroughly

## Support

For issues and questions:

- Open an issue on GitHub
- Check existing issues for solutions
- Review logs for error messages

## Acknowledgments

- [DexScreener](https://dexscreener.com/) for providing public API access
- [aiogram](https://github.com/aiogram/aiogram) for the excellent Telegram Bot framework
- The cryptocurrency community for inspiration

---

**Remember: This is not financial advice. Trade responsibly and at your own risk!** 🚨