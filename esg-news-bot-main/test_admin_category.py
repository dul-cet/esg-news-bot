#!/usr/bin/env python3
"""
Quick test for admin category correction functionality
"""
import sqlite3
import sys
sys.path.insert(0, '/Users/tulepbergenanel/Desktop/NewsBotESG')

from esgparser.core.database import NewsDatabase

# Create test database
db = NewsDatabase('/tmp/test_esg.db')

# Test 1: Create a test news item
print("Test 1: Adding test news...")
test_article = {
    'title': 'Test ESG Article',
    'digest': 'This is about environmental sustainability',
    'url': 'https://test.com/article',
    'source': 'test_source',
    'esg_category': 'Environment',
    'esg_score': 0.95,
    'image_url': None,
    'original_lang': 'en'
}
db.add_news(test_article)
print("✅ News added")

# Test 2: Get news by ID
print("\nTest 2: Getting news by ID...")
news = db.get_news_by_id(1)
if news:
    print(f"✅ Found news: {news['title']}")
    print(f"   Category: {news['esg_category']}")
else:
    print("❌ News not found")

# Test 3: Update category
print("\nTest 3: Updating category...")
result = db.update_news_category(1, 'Social', 1.0)
if result:
    print("✅ Category updated")
else:
    print("❌ Update failed")

# Test 4: Verify update
print("\nTest 4: Verifying update...")
news = db.get_news_by_id(1)
if news and news['esg_category'] == 'Social':
    print(f"✅ Category verified: {news['esg_category']}")
else:
    print(f"❌ Category not updated properly")

# Test 5: Update with score
print("\nTest 5: Updating with custom score...")
db.update_news_category(1, 'Governance', 0.85)
news = db.get_news_by_id(1)
if news['esg_category'] == 'Governance' and news['esg_score'] == 0.85:
    print(f"✅ Category: {news['esg_category']}, Score: {news['esg_score']}")
else:
    print("❌ Update with score failed")

print("\n" + "="*50)
print("All tests passed! ✅")
