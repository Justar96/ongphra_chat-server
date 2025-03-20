# Reading Matching Algorithm

This document explains the algorithm used to match readings to a user's birth chart in the Ongphra Chat system.

## Overview

The reading matching algorithm is a multi-stage process that finds the most relevant fortune readings for a user based on their birth information. The algorithm aims to provide personalized readings by matching Thai astrological positions with appropriate interpretations from the database.

## Flow Diagram

```
┌─────────────────┐
│ Calculate Bases │
└────────┬────────┘
         │
         ▼
┌────────────────────┐
│ Extract Attributes │
└────────┬───────────┘
         │
         ▼
┌───────────────────┐
│ Progressive Match │
└────────┬──────────┘
         │
         ▼
┌────────────────┐
│ Score and Rank │
└────────┬───────┘
         │
         ▼
┌─────────────────┐
│ Return Readings │
└─────────────────┘
```

## Algorithm Steps

### 1. Base Calculation

The first step is calculating the four bases from the user's birth information:
- **Base 1 (Day)**: Derived from Thai day of birth
- **Base 2 (Month)**: Derived from month of birth
- **Base 3 (Year)**: Derived from year of birth and zodiac animal
- **Base 4 (Sum)**: The sum of the first three bases

Each base contains 7 values arranged in a sequence.

### 2. Attribute Extraction

For each reading in the database, we extract:
- Base number (1-4)
- Position number (1-7)
- Value at that position

Attributes may be explicit in the database or extracted from the reading's heading using regex patterns and Thai position name mappings.

### 3. Progressive Matching Strategy

The algorithm employs a three-tier matching strategy, attempting matches in this order:

#### a. Direct Matching

Readings match if:
- Base and position exist in the calculator result
- If the reading specifies a value, it must match the calculated value
  - Exact matches or modulo 9 matches (for numerological compatibility)

#### b. Category-Based Matching

If direct matches are insufficient:
- Map positions to Thai categorical names (e.g., "อัตตะ", "หินะ", etc.)
- Find readings associated with those categories

#### c. Flexible Matching

If still insufficient:
- Match by base only
- Match by position only
- Match by value only

### 4. Scoring and Ranking

Each potential match is assigned a score based on:

- **Base Weight**: Different bases have different significance
  - Day base (1): 0.95
  - Month base (2): 0.90
  - Year base (3): 0.85
  - Sum base (4): 0.80

- **Position Weight**: Different positions have different significance
  - Position 1: 1.0
  - Position 2: 0.95
  - ...
  - Position 7: 0.70

- **Value Significance**: Certain values like 1 and 9 get bonus points

- **Topic Relevance**: Readings related to the user's question get bonus points

Final score = (Base Weight × Position Weight) + Value Bonus + Topic Relevance

### 5. Deduplication and Limitation

- Duplicate readings are removed, keeping the one with the highest score
- Results are sorted by score (highest first)
- Limited to a maximum of 50 readings to prevent overwhelming results

## Special Handling

### Position Mapping

Thai positions like "อัตตะ", "หินะ", etc. are mapped to their corresponding base and position numbers. For example:
- "อัตตะ" maps to Base 1, Position 1
- "ตะนุ" maps to Base 2, Position 1

### Thai House System

The algorithm incorporates the traditional Thai house system, where house numbers 1-12 are mapped to the four bases:
- Houses 1-3 → Base 1
- Houses 4-6 → Base 2
- Houses 7-9 → Base 3
- Houses 10-12 → Base 4

### Cache Optimization

Results are cached using an LRU (Least Recently Used) strategy with size limits and expiration to enhance performance.

## Code Implementation

The main implementation is divided across these classes:
- `ReadingMatcher`: Handles the matching logic
- `ReadingService`: Orchestrates the reading process
- `MeaningExtractor`: Extracts meanings from matched readings

The algorithm balances precision with coverage to ensure users receive meaningful readings even when exact matches aren't available. 