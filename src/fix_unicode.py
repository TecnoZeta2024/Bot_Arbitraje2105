"""
Fix Unicode Issues - Bot_Arbitraje2105
Removes emojis from production_server.py for Windows compatibility
"""

import re

def fix_unicode_in_file():
    """Replace emojis with ASCII characters in production_server.py"""
    
    # Read the file
    with open('production_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define replacements
    replacements = {
        '🚀': '[LAUNCH]',
        '✅': '[OK]',
        '❌': '[ERROR]',
        '📡': '[API]',
        '🌐': '[WEB]',
        '✨': '[INFO]',
        '📊': '[STATS]',
        '⚠️': '[WARNING]',
        '💰': '$',
        '📈': '[CHART]',
        '⏱️': '[TIME]',
        '💸': '[FEE]',
        '🔧': '[CONFIG]',
        '•': '*'
    }
    
    # Replace emojis
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    # Write back
    with open('production_server_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed file created: production_server_fixed.py")
    
    # Also update the specific logging lines
    lines_to_update = {
        748: '    print("[LAUNCH] BOT ARBITRAJE PRODUCTION SERVER v3.0")',
        750: '    print(f"[API] API Server: http://{host}:{port}")',
        751: '    print(f"[WEB] WebSocket: ws://{host}:{port}/ws")',
        753: '    print("[INFO] Features:")',
        754: '    print("   * Real-time Binance market data")',
        755: '    print("   * WebSocket with automatic heartbeat")',
        756: '    print("   * Robust reconnection handling")',
        757: '    print("   * Trading state management")',
        758: '    print("   * Paper trading simulation")',
        759: '    print("   * AI-powered signal generation")',
        760: '    print("   * Real-time portfolio tracking")',
        761: '    print("   * Comprehensive logging system")',
        763: '    print("[STATS] Monitoring:")',
        764: '    print(f"   * Logs: logs/production_server.log")',
        765: '    print(f"   * Health: http://{host}:{port}/api/health")'
    }
    
    # Create a cleaner version
    lines = content.splitlines()
    for line_num, new_content in lines_to_update.items():
        if line_num <= len(lines):
            lines[line_num - 1] = new_content
    
    # Check startup event for more emojis
    for i, line in enumerate(lines):
        if '🚀' in line:
            lines[i] = line.replace('🚀', '[LAUNCH]')
        if '✅' in line:
            lines[i] = line.replace('✅', '[OK]')
        if '❌' in line:
            lines[i] = line.replace('❌', '[ERROR]')
        if '⚠️' in line:
            lines[i] = line.replace('⚠️', '[WARNING]')
    
    # Write the cleaned version
    with open('production_server_clean.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("Clean file created: production_server_clean.py")

if __name__ == "__main__":
    fix_unicode_in_file()
