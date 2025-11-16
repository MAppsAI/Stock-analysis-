#!/usr/bin/env python3
"""
Quick test script to verify the new entry/exit combined strategies work correctly
"""

import sys
sys.path.append('/home/user/Stock-analysis-/backend')

def main():
    print("=" * 80)
    print("STRATEGY TESTING REPORT")
    print("=" * 80)

    # Import after adding to path
    from strategies import STRATEGY_MAP, ENTRY_CONDITIONS, EXIT_CONDITIONS, COMBINED_STRATEGIES, ORIGINAL_STRATEGIES

    # Count strategies
    original_count = len(ORIGINAL_STRATEGIES)
    combined_count = len(COMBINED_STRATEGIES)
    total_count = len(STRATEGY_MAP)

    print(f"\n📊 Strategy Counts:")
    print(f"  - Original strategies: {original_count}")
    print(f"  - Combined strategies: {combined_count}")
    print(f"  - Total strategies: {total_count}")
    print(f"  - Expected combinations: {len(ENTRY_CONDITIONS)} × {len(EXIT_CONDITIONS)} = {len(ENTRY_CONDITIONS) * len(EXIT_CONDITIONS)}")

    print(f"\n📈 Entry Conditions ({len(ENTRY_CONDITIONS)}):")
    for key, value in ENTRY_CONDITIONS.items():
        print(f"  - {key}: {value['name']}")

    print(f"\n📉 Exit Conditions ({len(EXIT_CONDITIONS)}):")
    for key, value in EXIT_CONDITIONS.items():
        print(f"  - {key}: {value['name']}")

    print(f"\n🔄 Sample Combined Strategies (first 10):")
    sample_count = 0
    for strategy_id, strategy_info in COMBINED_STRATEGIES.items():
        if sample_count < 10:
            print(f"  - {strategy_id}")
            print(f"    Name: {strategy_info['name']}")
            print(f"    Category: {strategy_info['category']}")
            sample_count += 1
        else:
            break

    print(f"\n✅ Verification:")
    print(f"  - All strategies have 'name': {all('name' in v for v in STRATEGY_MAP.values())}")
    print(f"  - All strategies have 'func': {all('func' in v for v in STRATEGY_MAP.values())}")
    print(f"  - All strategies have 'category': {all('category' in v for v in STRATEGY_MAP.values())}")
    print(f"  - No duplicate strategy IDs: {len(STRATEGY_MAP) == len(set(STRATEGY_MAP.keys()))}")

    # Categories breakdown
    from collections import Counter
    categories = Counter(s['category'] for s in STRATEGY_MAP.values())
    print(f"\n📋 Strategies by Category:")
    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
