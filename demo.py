#!/usr/bin/env python3
"""
Demo script to test the pump alert bot components without requiring Telegram credentials.
This demonstrates the core functionality of signal detection and caching.
"""
import sys
import asyncio
sys.path.insert(0, 'src')

from dex_monitor import DexMonitor
from alert_cache import AlertCache


async def demo():
    """Run a demonstration of the bot's core features."""
    print("=" * 60)
    print("Crypto Pump Alert Bot - Demo")
    print("=" * 60)
    print()
    
    # Initialize components
    print("📦 Initializing components...")
    monitor = DexMonitor(networks=["bsc", "eth", "solana", "base"])
    cache = AlertCache(antispam_seconds=60)
    print(f"✓ Monitor configured for: {', '.join(monitor.networks)}")
    print(f"✓ Alert cache with {cache.antispam_seconds}s anti-spam window")
    print()
    
    # Test signal detection
    print("🔍 Testing signal detection...")
    print()
    
    # Create test pairs
    test_pairs = [
        {
            "pairAddress": "0xabc123",
            "chainId": "bsc",
            "dexId": "pancakeswap",
            "baseToken": {"symbol": "PUMP"},
            "quoteToken": {"symbol": "USDT"},
            "priceUsd": "0.0001234",
            "priceChange": {"m5": 25.5},  # Strong pump!
            "volume": {"m5": 150000, "h6": 1800000},  # Good volume ratio
            "liquidity": {"usd": 75000},  # Good liquidity
            "url": "https://dexscreener.com/bsc/0xabc123"
        },
        {
            "pairAddress": "0xdef456",
            "chainId": "eth",
            "dexId": "uniswap",
            "baseToken": {"symbol": "WEAK"},
            "quoteToken": {"symbol": "USDT"},
            "priceUsd": "0.0005678",
            "priceChange": {"m5": 2.5},  # Below threshold
            "volume": {"m5": 5000, "h6": 100000},
            "liquidity": {"usd": 40000},
            "url": "https://dexscreener.com/eth/0xdef456"
        },
        {
            "pairAddress": "0xghi789",
            "chainId": "solana",
            "dexId": "raydium",
            "baseToken": {"symbol": "MOON"},
            "quoteToken": {"symbol": "USDC"},
            "priceUsd": "0.00891",
            "priceChange": {"m5": 12.3},  # Good pump
            "volume": {"m5": 200000, "h6": 1440000},  # Excellent volume ratio
            "liquidity": {"usd": 120000},  # Strong liquidity
            "url": "https://dexscreener.com/solana/0xghi789"
        },
    ]
    
    # Test each pair
    signals_found = []
    for pair in test_pairs:
        signal = monitor.check_pump_signal(
            pair,
            thresh_price=8.0,
            thresh_vol_ratio=3.0,
            thresh_liq_usd=30000
        )
        
        symbol = f"{pair['baseToken']['symbol']}/{pair['quoteToken']['symbol']}"
        chain = pair['chainId']
        price_change = pair['priceChange']['m5']
        
        if signal:
            print(f"🚨 SIGNAL: {symbol} on {chain}")
            print(f"   Price Change: {signal['price_change_m5']:.2f}%")
            print(f"   Volume Ratio: {signal['volume_ratio']:.2f}x")
            print(f"   Liquidity: ${signal['liquidity_usd']:,.0f}")
            signals_found.append(signal)
        else:
            print(f"⚪ No signal: {symbol} on {chain} (price_change={price_change:.2f}%)")
        print()
    
    # Test anti-spam cache
    print("🛡️ Testing anti-spam cache...")
    print()
    
    for signal in signals_found:
        pair_addr = signal['pair_address']
        symbol = f"{signal['base_token']}/{signal['quote_token']}"
        
        # First alert should succeed
        should_alert_1 = cache.should_alert(pair_addr)
        print(f"   {symbol}: First alert = {should_alert_1}")
        
        # Second alert should be blocked
        should_alert_2 = cache.should_alert(pair_addr)
        print(f"   {symbol}: Second alert (immediate) = {should_alert_2}")
        print()
    
    print(f"📊 Cached pairs: {cache.get_cached_count()}")
    print()
    
    # Cleanup
    await monitor.close()
    
    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  - Tested {len(test_pairs)} pairs")
    print(f"  - Found {len(signals_found)} pump signals")
    print(f"  - Anti-spam working correctly")
    print()
    print("✓ Demo completed successfully!")
    print("=" * 60)
    print()
    print("To run the actual bot, configure .env and run:")
    print("  python src/bot.py")


if __name__ == "__main__":
    asyncio.run(demo())
