import pandas as pd
from typing import Dict, List, Set
import os
from .settings import CATEGORIES_PATH, READINGS_PATH

class MeaningEngine:
    def __init__(self):
        # Load CSV data
        self.categories_df = pd.read_csv(CATEGORIES_PATH)
        self.readings_df = pd.read_csv(READINGS_PATH)
        
    def identify_topics(self, question: str) -> Set[str]:
        """Identify relevant topics based on the question"""
        question_lower = question.lower()
        topics = set()
        
        # Map keywords to categories
        keyword_map = {
            "RELATIONSHIP": ["love", "relationship", "partner", "marriage", "รัก", "ความรัก", "คู่", "แต่งงาน", "คู่ครอง"],
            "FINANCE": ["money", "finance", "wealth", "business", "เงิน", "การเงิน", "ธุรกิจ", "ลงทุน", "ทรัพย์"],
            "CAREER": ["job", "work", "career", "promotion", "งาน", "อาชีพ", "เลื่อนตำแหน่ง", "การงาน"],
            "HEALTH": ["health", "illness", "disease", "สุขภาพ", "โรค", "เจ็บป่วย"],
            "EDUCATION": ["study", "school", "education", "exam", "เรียน", "การศึกษา", "สอบ", "โรงเรียน"]
        }
        
        # Check for keywords in the question
        for category, keywords in keyword_map.items():
            if any(keyword in question_lower for keyword in keywords):
                topics.add(category)
        
        # Default to general readings if no specific category is identified
        if not topics:
            topics.add("GENERAL")
            topics.add("PERSONALITY")
            
        return topics
    
    def extract_meanings(self, bases: Dict, question: str) -> List[Dict]:
        """
        Extract relevant meanings based on the bases and question
        Returns a list of meaning dictionaries with context
        """
        topics = self.identify_topics(question)
        
        # Get category IDs
        category_ids = self.categories_df[
            self.categories_df['category_name'].isin(topics)
        ]['id'].tolist()
        
        meanings = []
        
        # Only process the first 4 bases for now as specified
        base_keys = ["base1", "base2", "base3", "base4"]
        
        for base_idx, base_key in enumerate(base_keys, 1):
            if base_key not in bases:
                continue
                
            sequence = bases[base_key]
            for position, value in enumerate(sequence, 1):
                # Find relevant readings
                relevant_readings = self.readings_df[
                    (self.readings_df['relationship_id'].isin(category_ids)) &
                    (self.readings_df['base'] == base_idx) &
                    (self.readings_df['position'] == position)
                ]
                
                # For now, let's add some sample logic
                for _, reading in relevant_readings.iterrows():
                    meanings.append({
                        "base": base_idx,
                        "position": position,
                        "value": value,
                        "heading": reading["heading"],
                        "meaning": reading["meaning"],
                        "category": reading["category"] if "category" in reading else None
                    })
        
        return meanings