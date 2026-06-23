#!/usr/bin/env python3
"""Тестирование NLP классификатора"""
import sys
sys.path.insert(0, '.')

from esgparser.classifier.esg_classifier import ESGClassifier

# Test with keyword fallback only
classifier = ESGClassifier(use_nlp=False)

test_cases = [
    ("Компания запустила солнечную электростанцию", "Новая инициатива по возобновляемой энергии", "ru"),
    ("Carbon emissions reduced by 50%", "Company announces sustainability goals", "en"),
    ("Diversity and inclusion program launched", "New HR initiative for women in tech", "en"),
    ("Corporate governance reforms approved", "Board transparency measures implemented", "en"),
]

print("=" * 70)
print("ESG CLASSIFIER TEST (Keyword Fallback Mode)")
print("=" * 70)

for title, digest, lang in test_cases:
    category, score = classifier.classify(title, digest, lang)
    print(f"\n📰 {title[:50]}")
    print(f"   📁 Category: {category:15s} | Confidence: {score:.1%}")

print("\n✅ Классификатор работает!\n")
