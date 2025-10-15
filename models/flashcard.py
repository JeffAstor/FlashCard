"""
FlashCard Models - Core data models for flash cards and sets
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.content_blocks import create_block_from_dict, create_block_from_type


class FlashCard:
    """Represents a single flash card with two sides"""
    
    def __init__(self, card_id=None):
        self.card_id = card_id if card_id else str(uuid.uuid4())
        self.information_side = []  # List of content blocks
        self.answer_side = []       # List of content blocks
        self.status = "Unknown"     # Known/Review/Unknown
        self.created_date = datetime.now().isoformat()
        self.last_studied = None
        
    def add_block_to_side(self, side, block):
        """Add content block to specified side"""
        if side == "information":
            if len(self.information_side) >= 10:
                raise ValueError("Maximum of 10 blocks per side allowed")
            self.information_side.append(block)
        elif side == "answer":
            if len(self.answer_side) >= 10:
                raise ValueError("Maximum of 10 blocks per side allowed")
            self.answer_side.append(block)
        else:
            raise ValueError("Invalid side. Must be 'information' or 'answer'")
            
    def remove_block_from_side(self, side, block_index):
        """Remove block from side"""
        if side == "information":
            if 0 <= block_index < len(self.information_side):
                del self.information_side[block_index]
            else:
                raise IndexError("Block index out of range")
        elif side == "answer":
            if 0 <= block_index < len(self.answer_side):
                del self.answer_side[block_index]
            else:
                raise IndexError("Block index out of range")
        else:
            raise ValueError("Invalid side. Must be 'information' or 'answer'")
            
    def move_block(self, side, from_index, to_index):
        """Reorder blocks within side"""
        if side == "information":
            blocks = self.information_side
        elif side == "answer":
            blocks = self.answer_side
        else:
            raise ValueError("Invalid side. Must be 'information' or 'answer'")
            
        if not (0 <= from_index < len(blocks) and 0 <= to_index < len(blocks)):
            raise IndexError("Block index out of range")
            
        block = blocks.pop(from_index)
        blocks.insert(to_index, block)
        
    def get_side_blocks(self, side):
        """Return blocks for specified side"""
        if side == "information":
            return self.information_side
        elif side == "answer":
            return self.answer_side
        else:
            raise ValueError("Invalid side. Must be 'information' or 'answer'")
            
    def set_status(self, status):
        """Update card study status"""
        valid_statuses = ["Known", "Review", "Unknown"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        self.status = status
        self.last_studied = datetime.now().isoformat()
        
    def to_dict(self):
        """Serialize card to dictionary"""
        return {
            "card_id": self.card_id,
            "information_side": [block.to_dict() for block in self.information_side],
            "answer_side": [block.to_dict() for block in self.answer_side],
            "status": self.status,
            "created_date": self.created_date,
            "last_studied": self.last_studied
        }
        
    @classmethod
    def from_dict(cls, data):
        """Deserialize card from dictionary"""
        card = cls(data.get("card_id"))
        
        # Load information side blocks
        for block_data in data.get("information_side", []):
            block = create_block_from_dict(block_data)
            card.information_side.append(block)
            
        # Load answer side blocks
        for block_data in data.get("answer_side", []):
            block = create_block_from_dict(block_data)
            card.answer_side.append(block)
            
        card.status = data.get("status", "Unknown")
        card.created_date = data.get("created_date", card.created_date)
        card.last_studied = data.get("last_studied")
        
        return card


class FlashCardSet:
    """Container for a collection of flash cards with metadata"""
    
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.icon_set = "default"
        self.tags = []
        self.difficulty_level = 1  # 1-5 scale
        self.created_date = datetime.now().isoformat()
        self.last_accessed = None
        self.cards = []
        
    @property
    def card_count(self):
        """Number of cards in set"""
        return len(self.cards)
        
    def add_card(self, card):
        """Add card to set"""
        if not isinstance(card, FlashCard):
            raise TypeError("Card must be a FlashCard instance")
        self.cards.append(card)
        
    def remove_card(self, card_id):
        """Remove card from set"""
        self.cards = [card for card in self.cards if card.card_id != card_id]
        
    def get_card(self, card_id):
        """Retrieve specific card"""
        for card in self.cards:
            if card.card_id == card_id:
                return card
        return None
        
    def get_card_by_index(self, index):
        """Get card by position"""
        if 0 <= index < len(self.cards):
            return self.cards[index]
        raise IndexError("Card index out of range")
        
    def move_card(self, from_index, to_index):
        """Reorder cards"""
        if not (0 <= from_index < len(self.cards) and 0 <= to_index < len(self.cards)):
            raise IndexError("Card index out of range")
            
        card = self.cards.pop(from_index)
        self.cards.insert(to_index, card)
        
    def get_cards_by_status(self, status):
        """Filter cards by study status"""
        return [card for card in self.cards if card.status == status]
        
    def update_metadata(self, description=None, tags=None, difficulty=None, icon_set=None):
        """Update set metadata"""
        if description is not None:
            self.description = description
        if tags is not None:
            self.tags = tags if isinstance(tags, list) else [tags]
        if difficulty is not None:
            if 1 <= difficulty <= 5:
                self.difficulty_level = difficulty
            else:
                raise ValueError("Difficulty level must be between 1 and 5")
        if icon_set is not None:
            self.icon_set = icon_set
            
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now().isoformat()
        
    def get_progress_stats(self):
        """Get basic progress statistics"""
        total = len(self.cards)
        if total == 0:
            return {"total": 0, "known": 0, "review": 0, "unknown": 0, "progress": 0}
            
        known = len([c for c in self.cards if c.status == "Known"])
        review = len([c for c in self.cards if c.status == "Review"])
        unknown = len([c for c in self.cards if c.status == "Unknown"])
        progress = (known / total) * 100 if total > 0 else 0
        
        return {
            "total": total,
            "known": known,
            "review": review,
            "unknown": unknown,
            "progress": progress
        }
        
    def to_dict(self):
        """Serialize set to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "icon_set": self.icon_set,
            "tags": self.tags,
            "difficulty_level": self.difficulty_level,
            "created_date": self.created_date,
            "last_accessed": self.last_accessed,
            "card_count": self.card_count
        }
        
    def cards_to_dict(self):
        """Serialize cards to dictionary for separate storage"""
        return {
            "cards": [card.to_dict() for card in self.cards]
        }
        
    @classmethod
    def from_dict(cls, set_data, cards_data=None):
        """Deserialize set from dictionary"""
        flash_set = cls(set_data["name"], set_data.get("description", ""))
        
        flash_set.icon_set = set_data.get("icon_set", "default")
        flash_set.tags = set_data.get("tags", [])
        flash_set.difficulty_level = set_data.get("difficulty_level", 1)
        flash_set.created_date = set_data.get("created_date", flash_set.created_date)
        flash_set.last_accessed = set_data.get("last_accessed")
        
        # Load cards if provided
        if cards_data:
            for card_data in cards_data.get("cards", []):
                card = FlashCard.from_dict(card_data)
                flash_set.cards.append(card)
                
        return flash_set
        
    def create_empty_card(self):
        """Create and add a new empty card to the set"""
        card = FlashCard()
        self.add_card(card)
        return card
        
    def validate(self):
        """Validate set data"""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Set name cannot be empty")
            
        if len(self.name) > 128:
            errors.append("Set name cannot exceed 128 characters")
            
        if self.difficulty_level < 1 or self.difficulty_level > 5:
            errors.append("Difficulty level must be between 1 and 5")
            
        # Validate cards
        for i, card in enumerate(self.cards):
            for side in ["information", "answer"]:
                for j, block in enumerate(card.get_side_blocks(side)):
                    is_valid, error_msg = block.validate()
                    if not is_valid:
                        errors.append(f"Card {i+1}, {side} side, block {j+1}: {error_msg}")
                        
        return len(errors) == 0, errors