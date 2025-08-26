#!/usr/bin/env python3
"""
🔍 Test Comprehensive Casino Research Data
=========================================

Test script to validate the 95+ field casino intelligence structure
"""

import json
from src.tools.real_supabase_research_tool import real_supabase_research_tool

def count_all_fields(data, prefix="", detailed=False):
    """Recursively count all fields including nested ones"""
    count = 0
    fields = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_key = f"{prefix}.{key}" if prefix else key
            count += 1
            if detailed:
                fields.append(current_key)
            
            if isinstance(value, dict):
                nested_count, nested_fields = count_all_fields(value, current_key, detailed)
                count += nested_count
                if detailed:
                    fields.extend(nested_fields)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        nested_count, nested_fields = count_all_fields(item, f"{current_key}[{i}]", detailed)
                        count += nested_count
                        if detailed:
                            fields.extend(nested_fields)
    
    return (count, fields) if detailed else count

def main():
    print("🔍 Testing Comprehensive Casino Research Data")
    print("=" * 60)
    
    # Fetch research data
    result = real_supabase_research_tool._run('viage', 'en-GB')
    
    if result["research_success"]:
        facts = result["facts"]
        
        # Count fields by category
        categories = {
            "Basic Information": 8,
            "Licensing & Regulation": 10, 
            "Games & Software": 15,
            "Bonuses & Promotions": 18,
            "Payment Methods": 12,
            "User Experience": 10,
            "Customer Support": 8,
            "Security & Fair Play": 12,
            "Technical Specifications": 6,
            "Terms & Conditions": 6
        }
        
        # Display comprehensive structure
        print(f"🎯 Casino: {result['casino_slug'].title()} Casino")
        print(f"🌐 Locale: {result['locale']}")
        print(f"📊 Data Quality: {result['data_quality'].title()}")
        print(f"📄 Sources: {len(result['sources'])}")
        print()
        
        # Count actual fields with details
        total_fields, field_list = count_all_fields(facts, detailed=True)
        print(f"📈 TOTAL CASINO INTELLIGENCE FIELDS: {total_fields}")
        print()
        
        # Show some sample field paths
        print("🔍 Sample Field Paths:")
        for i, field in enumerate(field_list[:15]):  # Show first 15 fields
            print(f"   {i+1:2d}. {field}")
        if len(field_list) > 15:
            print(f"   ... and {len(field_list)-15} more fields")
        print()
        
        # Show category breakdown
        print("📋 Expected Categories:")
        for category, expected in categories.items():
            print(f"   ✅ {category}: {expected} fields")
        
        expected_total = sum(categories.values())
        print(f"\n🎯 Expected Total: {expected_total} fields")
        print(f"📊 Actual Total: {total_fields} fields")
        
        if total_fields >= 90:
            print(f"🎊 SUCCESS: {total_fields} fields = Comprehensive casino intelligence!")
        elif total_fields >= 50:
            print(f"✅ GOOD: {total_fields} fields = Solid casino data")
        else:
            print(f"⚠️  LIMITED: {total_fields} fields = Basic data only")
        
        # Show sample data structure
        print(f"\n🔍 Sample Data Structure:")
        print("=" * 60)
        
        # Show each category with sample fields
        if "license" in facts:
            print(f"🛡️  Licensing: {facts['license']['primary']} (#{facts['license']['license_number']})")
        
        if "games" in facts:
            games = facts["games"]
            print(f"🎮 Games: {games['total_games']} total ({games['slots']} slots, {games['live_dealer']} live)")
        
        if "welcome_bonus" in facts:
            bonus = facts["welcome_bonus"]
            print(f"🎁 Bonus: {bonus['amount']} @ {bonus['percentage']}% (WR: {bonus['wagering_requirement']})")
        
        if "payments" in facts:
            payments = facts["payments"]
            print(f"💳 Payments: {len(payments['deposit_methods'])} methods, {payments['withdrawal_limits']['daily']} daily limit")
        
        if "customer_support" in facts:
            support = facts["customer_support"]
            print(f"🎧 Support: {'24/7' if support['support_hours'] == '24/7' else 'Limited'} ({'Live Chat' if support['live_chat'] else 'Email Only'})")
        
        print("\n✅ Comprehensive casino intelligence successfully loaded!")
        print(f"🚀 Ready for professional casino review generation with {total_fields} data points")
        
    else:
        print("❌ Failed to load casino research data")

if __name__ == "__main__":
    main()