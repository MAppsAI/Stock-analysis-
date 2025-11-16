#!/usr/bin/env python3
"""
Test script for combined strategy optimization
"""

import sys
sys.path.append('/home/user/Stock-analysis-/backend')

def test_combined_optimization():
    """Test the combined strategy optimization system"""
    print("=" * 80)
    print("COMBINED STRATEGY OPTIMIZATION TEST")
    print("=" * 80)

    from optimizer import (
        ENTRY_PARAMETERS, EXIT_PARAMETERS,
        optimize_combined_strategy, optimize_strategy
    )

    print(f"\n📊 Entry Parameters Defined: {len(ENTRY_PARAMETERS)}")
    for entry_key in ENTRY_PARAMETERS.keys():
        param_count = len(ENTRY_PARAMETERS[entry_key])
        print(f"  - {entry_key}: {param_count} parameters")

    print(f"\n📊 Exit Parameters Defined: {len(EXIT_PARAMETERS)}")
    for exit_key in EXIT_PARAMETERS.keys():
        param_count = len(EXIT_PARAMETERS[exit_key])
        print(f"  - {exit_key}: {param_count} parameters")

    # Calculate total possible combinations
    print(f"\n🔢 Total Combination Potential:")
    total_combos = 0
    for entry_key, entry_params in ENTRY_PARAMETERS.items():
        for exit_key, exit_params in EXIT_PARAMETERS.items():
            # Calculate number of param combinations for this entry/exit pair
            entry_combos = 1
            for param_values in entry_params.values():
                entry_combos *= len(param_values)

            exit_combos = 1
            for param_values in exit_params.values():
                exit_combos *= len(param_values)

            pair_combos = entry_combos * exit_combos
            total_combos += pair_combos

    print(f"  - Total optimizable combinations: {total_combos:,}")
    print(f"  - Entry/Exit pairs: {len(ENTRY_PARAMETERS)} × {len(EXIT_PARAMETERS)} = {len(ENTRY_PARAMETERS) * len(EXIT_PARAMETERS)}")

    # Test strategy ID parsing
    print(f"\n🧪 Testing Strategy ID Parsing:")
    test_ids = [
        'combo_sma_cross_entry_rsi_overbought_exit',
        'combo_rsi_oversold_entry_trailing_stop_exit',
        'combo_macd_cross_entry_take_profit_exit'
    ]

    for strategy_id in test_ids:
        if strategy_id.startswith('combo_'):
            parts = strategy_id.replace('combo_', '').split('_entry_')
            if len(parts) == 2:
                entry_type = parts[0]
                exit_type = parts[1].replace('_exit', '')
                print(f"  ✅ {strategy_id}")
                print(f"     Entry: {entry_type} | Exit: {exit_type}")

                # Check if parameters exist
                has_entry_params = entry_type in ENTRY_PARAMETERS
                has_exit_params = exit_type in EXIT_PARAMETERS
                print(f"     Has entry params: {has_entry_params} | Has exit params: {has_exit_params}")
            else:
                print(f"  ❌ Invalid format: {strategy_id}")

    print("\n" + "=" * 80)
    print("✅ OPTIMIZATION SYSTEM READY")
    print("=" * 80)

    print("\n💡 Example Usage:")
    print("  optimize_strategy('combo_rsi_oversold_entry_trailing_stop_exit', data)")
    print("  This will test combinations like:")
    print("    - RSI(14, threshold=25) Entry + Trailing Stop(5%) Exit")
    print("    - RSI(14, threshold=30) Entry + Trailing Stop(7%) Exit")
    print("    - RSI(20, threshold=25) Entry + Trailing Stop(3%) Exit")
    print("    - ... and many more!")

if __name__ == "__main__":
    test_combined_optimization()
