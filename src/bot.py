"""Telegram bot for crypto pump alerts."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from config import Config
from dex_monitor import DexMonitor
from alert_cache import AlertCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PumpAlertBot:
    """Main bot class for crypto pump alerts."""
    
    def __init__(self):
        """Initialize the pump alert bot."""
        # Validate configuration
        Config.validate()
        
        # Initialize bot and dispatcher
        self.bot = Bot(token=Config.BOT_TOKEN)
        self.dp = Dispatcher()
        
        # Initialize components
        self.monitor = DexMonitor(networks=Config.NETWORKS)
        self.cache = AlertCache(antispam_seconds=Config.ANTISPAM_SECONDS)
        
        # Register handlers
        self._register_handlers()
        
        # Monitoring state
        self.is_monitoring = False
    
    def _register_handlers(self) -> None:
        """Register bot command handlers."""
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_status, Command("status"))
        self.dp.message.register(self.cmd_help, Command("help"))
    
    async def cmd_start(self, message: Message) -> None:
        """Handle /start command."""
        await message.answer(
            "🚀 Crypto Pump Alert Bot Started!\n\n"
            f"Monitoring networks: {', '.join(Config.NETWORKS)}\n"
            f"Poll interval: {Config.POLL_INTERVAL_SEC}s\n"
            f"Price threshold: {Config.THRESH_PRICE}%\n"
            f"Volume ratio threshold: {Config.THRESH_VOL_RATIO}x\n"
            f"Liquidity threshold: ${Config.THRESH_LIQ_USD:,.0f}\n\n"
            "Use /status to check monitoring status.\n"
            "Use /help for more information."
        )
    
    async def cmd_status(self, message: Message) -> None:
        """Handle /status command."""
        status = "🟢 Active" if self.is_monitoring else "🔴 Inactive"
        cached = self.cache.get_cached_count()
        
        await message.answer(
            f"📊 Bot Status: {status}\n\n"
            f"Networks: {', '.join(Config.NETWORKS)}\n"
            f"Cached pairs: {cached}\n"
            f"Antispam window: {Config.ANTISPAM_SECONDS}s ({Config.ANTISPAM_SECONDS // 60} min)"
        )
    
    async def cmd_help(self, message: Message) -> None:
        """Handle /help command."""
        await message.answer(
            "🤖 Crypto Pump Alert Bot\n\n"
            "This bot monitors DexScreener for potential pump signals based on:\n"
            f"• Price change (5m) > {Config.THRESH_PRICE}%\n"
            f"• Volume ratio > {Config.THRESH_VOL_RATIO}x\n"
            f"• Liquidity > ${Config.THRESH_LIQ_USD:,.0f}\n\n"
            "Commands:\n"
            "/start - Start the bot\n"
            "/status - Check bot status\n"
            "/help - Show this help message\n\n"
            "⚠️ Disclaimer: Signals are informational only, not financial advice.\n"
            "Always do your own research before trading."
        )
    
    async def send_alert(self, signal: dict) -> None:
        """Send pump alert to configured chat.
        
        Args:
            signal: Signal data dictionary
        """
        try:
            message = (
                "🚨 <b>PUMP ALERT</b> 🚨\n\n"
                f"<b>Token:</b> {signal['base_token']}/{signal['quote_token']}\n"
                f"<b>Chain:</b> {signal['chain']}\n"
                f"<b>DEX:</b> {signal['dex']}\n\n"
                f"📈 <b>Price Change (5m):</b> {signal['price_change_m5']:.2f}%\n"
                f"💰 <b>Price:</b> ${signal['price_usd']}\n"
                f"📊 <b>Volume Ratio:</b> {signal['volume_ratio']:.2f}x\n"
                f"💧 <b>Liquidity:</b> ${signal['liquidity_usd']:,.0f}\n"
                f"💵 <b>Volume (5m):</b> ${signal['volume_m5']:,.0f}\n\n"
                f"🔗 <a href=\"{signal['url']}\">View on DexScreener</a>\n"
                f"📝 <code>{signal['pair_address']}</code>\n\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                "⚠️ <i>Not financial advice. DYOR!</i>"
            )
            
            await self.bot.send_message(
                chat_id=Config.CHAT_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"Alert sent for {signal['base_token']}/{signal['quote_token']}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def monitoring_loop(self) -> None:
        """Main monitoring loop to scan for pump signals."""
        logger.info("Starting monitoring loop...")
        self.is_monitoring = True
        
        try:
            while self.is_monitoring:
                try:
                    # Scan all networks
                    logger.info("Scanning networks for pump signals...")
                    pairs = await self.monitor.scan_all_networks()
                    
                    logger.info(f"Found {len(pairs)} pairs to analyze")
                    
                    # Check each pair for pump signals
                    signals_found = 0
                    for pair in pairs:
                        signal = self.monitor.check_pump_signal(
                            pair,
                            Config.THRESH_PRICE,
                            Config.THRESH_VOL_RATIO,
                            Config.THRESH_LIQ_USD,
                        )
                        
                        if signal:
                            pair_address = signal["pair_address"]
                            
                            # Check if we should alert (not in antispam window)
                            if self.cache.should_alert(pair_address):
                                # Optional honeypot check
                                if Config.HONEYPOT_CHECK_ENABLED:
                                    is_honeypot = await self.monitor.check_honeypot(
                                        pair_address, signal["chain"]
                                    )
                                    if is_honeypot:
                                        logger.warning(f"Honeypot detected: {pair_address}")
                                        continue
                                
                                # Send alert
                                await self.send_alert(signal)
                                signals_found += 1
                    
                    if signals_found > 0:
                        logger.info(f"Sent {signals_found} alerts")
                    
                    # Cleanup expired cache entries
                    self.cache.cleanup()
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop iteration: {e}")
                
                # Wait for next poll interval
                await asyncio.sleep(Config.POLL_INTERVAL_SEC)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            self.is_monitoring = False
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            self.is_monitoring = False
    
    async def start(self) -> None:
        """Start the bot and monitoring."""
        logger.info("Starting Crypto Pump Alert Bot...")
        logger.info(f"Monitoring networks: {Config.NETWORKS}")
        logger.info(f"Poll interval: {Config.POLL_INTERVAL_SEC}s")
        
        # Send startup notification
        try:
            await self.bot.send_message(
                chat_id=Config.CHAT_ID,
                text=(
                    "🤖 <b>Bot Started</b>\n\n"
                    f"Monitoring: {', '.join(Config.NETWORKS)}\n"
                    f"Poll interval: {Config.POLL_INTERVAL_SEC}s\n\n"
                    "⚠️ Signals are informational only, not financial advice."
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
        
        # Start monitoring in background
        monitoring_task = asyncio.create_task(self.monitoring_loop())
        
        try:
            # Start polling for commands
            await self.dp.start_polling(self.bot)
        finally:
            # Cleanup
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            await self.monitor.close()
            await self.bot.session.close()
    
    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping bot...")
        self.is_monitoring = False
        await self.monitor.close()
        await self.bot.session.close()


async def main():
    """Main entry point."""
    bot = PumpAlertBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
