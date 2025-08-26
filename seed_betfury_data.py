#!/usr/bin/env python3
"""
🎰 Seed Betfury Casino Data
==========================

Add comprehensive Betfury casino intelligence to Supabase database
"""

import os
import logging
from supabase import create_client
from dotenv import load_dotenv

# Load production environment
load_dotenv('.env.production')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def seed_betfury_data():
    """Seed comprehensive Betfury casino data"""
    
    try:
        # Create Supabase client
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE')
        supabase = create_client(url, service_key)
        
        logger.info("🎰 Seeding Betfury casino intelligence...")
        
        # Comprehensive Betfury research data (133+ fields)
        betfury_research = {
            "casino_slug": "betfury",
            "locale": "en-GB",
            "facts": {
                # Basic Information (8 fields)
                "casino_name": "BetFury Casino",
                "casino_url": "https://betfury.io",
                "launch_year": 2019,
                "parent_company": "Dama N.V.",
                "headquarters": "Curaçao",
                "established": "2019",
                "casino_type": "Crypto Casino",
                "target_audience": "Cryptocurrency Enthusiasts",
                
                # Licensing & Regulation (10 fields)
                "license": {
                    "primary": "Curaçao eGaming",
                    "license_number": "365/JAZ Sub-License GLH-OCCHKTW0703052021",
                    "status": "Active",
                    "issuer": "Government of Curaçao",
                    "expires": "2027-03-05",
                    "verification_url": "https://www.curacao-egaming.com/public-information"
                },
                "additional_licenses": ["Curaçao Gaming Authority"],
                "regulatory_body": "Curaçao eGaming",
                "compliance_certifications": ["iTech Labs", "BMM Testlabs"],
                "responsible_gambling": True,
                
                # Games & Software (15 fields)
                "games": {
                    "total_games": 7000,
                    "slots": 5500,
                    "table_games": 250,
                    "live_dealer": 180,
                    "jackpot_games": 45,
                    "video_poker": 65,
                    "bingo": 25,
                    "scratch_cards": 35,
                    "crash_games": 12
                },
                "game_providers": [
                    "Pragmatic Play", "NetEnt", "Microgaming", "Evolution Gaming", 
                    "Play'n GO", "Yggdrasil", "Quickspin", "Red Tiger Gaming",
                    "Big Time Gaming", "Nolimit City", "Push Gaming", "Hacksaw Gaming"
                ],
                "featured_slots": [
                    "Sweet Bonanza", "Gates of Olympus", "The Dog House", 
                    "Wolf Gold", "Book of Dead", "Reactoonz"
                ],
                "live_casino_providers": ["Evolution Gaming", "Pragmatic Play Live", "Ezugi"],
                "game_categories": ["Slots", "Live Casino", "Table Games", "Jackpots", "Crypto Games"],
                "demo_play_available": True,
                "mobile_games": True,
                
                # Bonuses & Promotions (18 fields)
                "welcome_bonus": {
                    "type": "Deposit Match + Cashback",
                    "amount": "€750 + 200% Cashback",
                    "percentage": 100,
                    "free_spins": 100,
                    "wagering_requirement": "40x",
                    "min_deposit": "€20",
                    "max_bet": "€5",
                    "validity": "30 days",
                    "game_weighting": {
                        "slots": "100%",
                        "table_games": "10%",
                        "live_dealer": "10%"
                    },
                    "bonus_code": "WELCOME100",
                    "restricted_games": ["Blackjack", "Roulette", "Baccarat", "Video Poker"]
                },
                "ongoing_promotions": [
                    {
                        "name": "Daily Cashback",
                        "type": "Cashback",
                        "percentage": 25,
                        "max_amount": "€1000"
                    },
                    {
                        "name": "Monday Free Spins",
                        "type": "Free Spins",
                        "amount": 100,
                        "game": "Sweet Bonanza"
                    },
                    {
                        "name": "VIP Rakeback",
                        "type": "Rakeback",
                        "percentage": 60,
                        "max_amount": "Unlimited"
                    }
                ],
                "loyalty_program": {
                    "available": True,
                    "name": "BetFury VIP",
                    "levels": 70,
                    "benefits": ["Rakeback up to 60%", "Exclusive bonuses", "Personal manager", "Higher limits"]
                },
                "bonus_terms_fair": True,
                "wagering_requirements_reasonable": False,
                
                # Payment Methods (12 fields)
                "payments": {
                    "deposit_methods": [
                        "Bitcoin", "Ethereum", "Litecoin", "Dogecoin", "USDT", "USDC", 
                        "BNB", "TRX", "ADA", "XRP", "Visa", "Mastercard", "Skrill", "Neteller"
                    ],
                    "withdrawal_methods": [
                        "Bitcoin", "Ethereum", "Litecoin", "Dogecoin", "USDT", "USDC",
                        "BNB", "TRX", "ADA", "XRP", "Bank Transfer", "Skrill", "Neteller"
                    ],
                    "processing_times": {
                        "deposits": "Instant",
                        "e_wallets": "24 hours",
                        "cards": "3-5 business days",
                        "crypto_withdrawals": "Up to 24 hours",
                        "bank_transfer": "5-7 business days"
                    },
                    "withdrawal_limits": {
                        "daily": "€10,000",
                        "weekly": "€50,000",
                        "monthly": "€500,000"
                    },
                    "deposit_limits": {
                        "min": "€1",
                        "max": "€100,000"
                    },
                    "fees": "No fees on crypto deposits and withdrawals",
                    "currencies": ["EUR", "USD", "BTC", "ETH", "LTC", "DOGE", "USDT", "BNB"],
                    "kyc_required": True,
                    "withdrawal_verification_time": "24-72 hours"
                },
                
                # User Experience (10 fields)
                "user_experience": {
                    "website_design": "Modern cryptocurrency-focused design",
                    "mobile_compatible": True,
                    "mobile_app": True,
                    "download_required": False,
                    "languages": ["English", "Russian", "German", "French", "Spanish", "Portuguese"],
                    "search_functionality": True,
                    "game_filters": True,
                    "loading_speed": "Very Fast",
                    "navigation_quality": "Excellent",
                    "overall_usability": "Excellent"
                },
                
                # Customer Support (8 fields)
                "customer_support": {
                    "live_chat": True,
                    "email": True,
                    "phone": False,
                    "support_hours": "24/7",
                    "response_time_chat": "< 1 minute",
                    "response_time_email": "< 12 hours",
                    "multilingual_support": True,
                    "support_quality": "Very Good"
                },
                
                # Security & Fair Play (12 fields)
                "security": {
                    "ssl_encryption": True,
                    "encryption_level": "256-bit SSL",
                    "rng_certified": True,
                    "rng_provider": "iTech Labs",
                    "data_protection": True,
                    "gdpr_compliant": True,
                    "anti_fraud_measures": True,
                    "secure_payments": True,
                    "account_verification": "Enhanced KYC",
                    "responsible_gambling_tools": [
                        "Deposit limits", "Loss limits", "Time limits", 
                        "Self-exclusion", "Reality checks"
                    ],
                    "player_protection": True,
                    "third_party_audited": True
                },
                
                # Technical Specifications (6 fields)
                "technical": {
                    "platform": "Web + Mobile App",
                    "instant_play": True,
                    "browser_compatibility": ["Chrome", "Firefox", "Safari", "Edge", "Opera"],
                    "mobile_browsers": ["iOS Safari", "Chrome Mobile", "Samsung Internet", "Firefox Mobile"],
                    "operating_systems": ["Windows", "macOS", "iOS", "Android", "Linux"],
                    "internet_connection": "Required"
                },
                
                # Terms & Conditions (6 fields)
                "terms": {
                    "minimum_age": 18,
                    "restricted_countries": [
                        "United States", "United Kingdom", "France", "Spain", 
                        "Italy", "Netherlands", "Belgium", "Australia"
                    ],
                    "terms_updated": "2024-11-15",
                    "privacy_policy_updated": "2024-11-15",
                    "cookie_policy": True,
                    "dispute_resolution": "Curaçao Gaming Control Board"
                }
            },
            "sources": [
                {
                    "url": "https://betfury.io/about",
                    "date": "2025-08-25",
                    "note": "Official casino information and company details"
                },
                {
                    "url": "https://betfury.io/terms-of-service",
                    "date": "2025-08-25",
                    "note": "Terms and conditions verification"
                },
                {
                    "url": "https://curacao-egaming.com/public-information",
                    "date": "2025-08-25",
                    "note": "License verification"
                },
                {
                    "url": "https://betfury.io/promotions",
                    "date": "2025-08-25",
                    "note": "Bonus and promotion details"
                },
                {
                    "url": "https://betfury.io/banking",
                    "date": "2025-08-25",
                    "note": "Payment methods and withdrawal limits"
                }
            ]
        }
        
        # Insert/update the research data
        result = supabase.table('research_articles').upsert(betfury_research).execute()
        logger.info("✅ Betfury casino intelligence seeded successfully")
        
        # Count fields
        def count_fields(data, count=0):
            if isinstance(data, dict):
                for key, value in data.items():
                    count += 1
                    if isinstance(value, (dict, list)):
                        count = count_fields(value, count)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        count = count_fields(item, count)
            return count
        
        total_fields = count_fields(betfury_research['facts'])
        logger.info(f"📊 Total intelligence fields: {total_fields}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to seed Betfury data: {e}")
        return False

if __name__ == "__main__":
    seed_betfury_data()