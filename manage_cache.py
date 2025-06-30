#!/usr/bin/env python3
"""
Utility to manage the Tesco nutrition cache.
"""

from meal_prep_agent.nutrition_cache import (
    get_cache_stats, 
    clear_nutrition_cache, 
    export_cache_to_csv
)
import sys

def show_cache_stats():
    """Display cache statistics."""
    print("📊 Tesco Nutrition Cache Statistics")
    print("="*50)
    
    stats = get_cache_stats()
    
    print(f"📦 Total Cached Products: {stats['total_cached_products']}")
    print(f"🎯 Total Cache Hits: {stats['total_cache_hits']}")
    print(f"💾 Cache File Size: {stats['cache_file_size_kb']} KB")
    print(f"⏰ Last Updated: {stats['last_updated']}")
    
    if stats['most_popular_products']:
        print(f"\n🏆 Most Popular Products:")
        for i, product in enumerate(stats['most_popular_products'], 1):
            print(f"  {i}. {product['name']} ({product['hits']} hits)")
    
    print(f"\n💰 Estimated API Call Savings: {stats['total_cache_hits']} requests")
    print(f"⚡ Cache Hit Rate: {stats['total_cache_hits']}/{stats['total_cached_products'] + stats['total_cache_hits']} requests")

def export_cache():
    """Export cache to CSV for analysis."""
    output_file = "tesco_nutrition_cache_export.csv"
    export_cache_to_csv(output_file)
    print(f"📄 Cache exported to: {output_file}")

def clear_cache():
    """Clear the entire cache."""
    confirm = input("⚠️ Are you sure you want to clear the entire cache? (y/N): ")
    if confirm.lower() == 'y':
        clear_nutrition_cache()
        print("🗑️ Cache cleared successfully!")
    else:
        print("❌ Cache clear cancelled")

def main():
    """Main cache management interface."""
    if len(sys.argv) < 2:
        print("🛠️ Tesco Nutrition Cache Manager")
        print("="*40)
        print("Usage:")
        print("  python manage_cache.py stats    - Show cache statistics")
        print("  python manage_cache.py export   - Export cache to CSV")
        print("  python manage_cache.py clear    - Clear entire cache")
        print("  python manage_cache.py help     - Show this help")
        return
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        show_cache_stats()
    elif command == "export":
        export_cache()
    elif command == "clear":
        clear_cache()
    elif command == "help":
        main()
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python manage_cache.py help' for usage information")

if __name__ == "__main__":
    main()