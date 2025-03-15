# tests/test_reading_service.py
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.reading_service import ReadingService
from app.services.calculator import CalculatorService
from app.domain.meaning import Reading, Category, MeaningCollection
from app.domain.bases import BasesResult, Bases
from app.domain.birth import BirthInfo


@pytest.fixture
def mock_reading_repository():
    """Create a mock reading repository"""
    repo = AsyncMock()
    
    # Mock get_by_base_and_position method
    repo.get_by_base_and_position.return_value = [
        Reading(
            id=1,
            base=1,
            position=1,
            relationship_id=21,
            content="Test reading content",
            heading="สินทรัพย์ (โภคา) สัมพันธ์กับ เพื่อนฝูง การติดต่อ (สหัชชะ)"
        )
    ]
    
    return repo


@pytest.fixture
def mock_category_repository():
    """Create a mock category repository"""
    repo = AsyncMock()
    
    # Mock get_by_name method
    async def get_by_name(name):
        if name == "โภคา":
            return Category(id=21, category_name="assets", category_thai_name="สินทรัพย์")
        elif name == "สหัชชะ":
            return Category(id=14, category_name="friends", category_thai_name="เพื่อนฝูง การติดต่อ")
        return None
    
    # Mock get_by_thai_name method
    async def get_by_thai_name(thai_name):
        if thai_name == "สินทรัพย์":
            return Category(id=21, category_name="assets", category_thai_name="สินทรัพย์")
        elif thai_name == "เพื่อนฝูง การติดต่อ":
            return Category(id=14, category_name="friends", category_thai_name="เพื่อนฝูง การติดต่อ")
        return None
    
    repo.get_by_name.side_effect = get_by_name
    repo.get_by_thai_name.side_effect = get_by_thai_name
    
    return repo


@pytest.fixture
def reading_service(mock_reading_repository, mock_category_repository):
    """Create a reading service with mock repositories"""
    return ReadingService(mock_reading_repository, mock_category_repository)


@pytest.mark.asyncio
async def test_extract_elements_from_heading(reading_service):
    """Test extracting elements from a heading"""
    heading = "สินทรัพย์ (โภคา) สัมพันธ์กับ เพื่อนฝูง การติดต่อ (สหัชชะ)"
    element1, element2 = await reading_service.extract_elements_from_heading(heading)
    
    assert element1 == "โภคา"
    assert element2 == "สหัชชะ"


@pytest.mark.asyncio
async def test_get_category_by_element_name(reading_service):
    """Test getting a category by element name"""
    category = await reading_service.get_category_by_element_name("โภคา")
    
    assert category is not None
    assert category.id == 21
    assert category.category_name == "assets"
    assert category.category_thai_name == "สินทรัพย์"


@pytest.mark.asyncio
async def test_extract_meanings_from_calculator_result(reading_service):
    """Test extracting meanings from calculator result"""
    # Create a mock BasesResult
    birth_info = BirthInfo(
        date=datetime(2000, 1, 1),
        day="อาทิตย์",
        day_value=1,
        month=1,
        year_animal="ชวด",
        year_start_number=1
    )
    
    bases = Bases(
        base1=[1, 2, 3, 4, 5, 6, 7],
        base2=[1, 2, 3, 4, 5, 6, 7],
        base3=[1, 2, 3, 4, 5, 6, 7],
        base4=[3, 6, 9, 12, 15, 18, 21]
    )
    
    bases_result = BasesResult(
        birth_info=birth_info,
        bases=bases
    )
    
    # Extract meanings
    meanings = await reading_service.extract_meanings_from_calculator_result(bases_result)
    
    # Verify results
    assert isinstance(meanings, MeaningCollection)
    assert len(meanings.items) > 0
    
    # Check the first meaning
    first_meaning = meanings.items[0]
    assert first_meaning.base == 1
    assert first_meaning.position == 1
    assert first_meaning.heading == "สินทรัพย์ (โภคา) สัมพันธ์กับ เพื่อนฝูง การติดต่อ (สหัชชะ)"
    assert first_meaning.meaning == "Test reading content"
    assert first_meaning.category == "assets - friends" 