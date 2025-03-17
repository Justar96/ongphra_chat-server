# Ongphra Chat - Thai Fortune Telling API

A FastAPI application for Thai fortune telling based on the "เลข 7 ตัว 9 ฐาน" (7 Numbers 9 Bases) system.

## System Architecture

The application follows a clean architecture pattern with the following components:

- **API Layer**: FastAPI routes and endpoints
- **Service Layer**: Business logic and orchestration
- **Repository Layer**: Data access and persistence
- **Domain Layer**: Core entities and models

## Fortune Telling Logic

### Refined Fortune Telling Flow

The system follows these steps to generate a fortune reading:

1. **Input Collection**:
   - Birth date (YYYY-MM-DD)
   - Thai day (อาทิตย์, จันทร์, อังคาร, etc.)
   - Optional question

2. **Base Calculation** (CalculatorService):
   - Calculates the "7 numbers in 9 bases" using the birth date and Thai day
   - Generates 4 bases with 7 positions each
   - Each base and position has specific meanings in Thai astrology

3. **Reading Extraction** (ReadingService):
   - Uses the calculated bases to query the database for relevant readings
   - Extracts readings directly based on base numbers and positions
   - Does NOT query by topic keywords like "การเงิน" (finance)
   - Instead, uses the base values to find the appropriate ภพ (house/base)

4. **Prompt Generation** (PromptService):
   - Creates a detailed prompt for the AI model
   - Includes birth information, calculated bases, and extracted readings
   - Formats the readings to highlight the most relevant ones based on match scores

5. **Response Generation** (ResponseService):
   - Uses OpenAI to generate a personalized fortune reading
   - Incorporates the extracted readings into the response
   - Focuses on the user's question while using the base readings for context

### Key Concept: Base-Driven Readings

The refined logic focuses on using the calculated bases to drive the readings, rather than keyword matching:

1. The system calculates the 7 numbers in 9 bases based on birth information
2. Each base (ฐาน) and position has specific meanings in Thai astrology
3. The system queries the database for readings associated with these specific bases and positions
4. The AI uses these readings to generate a personalized response

This approach ensures that the fortune telling is truly based on the traditional Thai "เลข 7 ตัว 9 ฐาน" system, rather than simple keyword matching.

### Database Query Flow

The database query flow is a critical part of the fortune telling system. Here's how it works in detail:

#### 1. Mapping Bases to House Numbers

In Thai astrology, each base (ฐาน) corresponds to a specific aspect of life:

- **Base 1 (ฐานที่ 1)**: Derived from the day of birth, maps to house numbers 1-4
  - House 1: ตนุ (Body/Self)
  - House 2: ธนัง (Wealth/Possessions)
  - House 3: สหัชชะ (Siblings/Communication)
  - House 4: พันธุ (Family/Home)

- **Base 2 (ฐานที่ 2)**: Derived from the month, maps to house numbers 5-7
  - House 5: ปุตตะ (Children/Creativity)
  - House 6: ริปุ (Enemies/Health challenges)
  - House 7: ปัตนิ (Spouse/Partnerships)

- **Base 3 (ฐานที่ 3)**: Derived from the year, maps to house numbers 8-10
  - House 8: มรณะ (Death/Transformation)
  - House 9: กดุมภะ (Fortune/Higher learning)
  - House 10: กัมมะ (Career/Public status)

- **Base 4 (ฐานที่ 4)**: Sum of bases 1-3, maps to house numbers 11-12
  - House 11: ลาภะ (Gains/Social networks)
  - House 12: วินาสนะ (Loss/Spirituality)

#### 2. Database Schema Design

The database schema is designed to support this mapping:

- **categories table**: Contains the houses (ภพ) with their house_number (1-12)
- **category_combinations table**: Represents relationships between two houses
- **readings table**: Contains fortune readings for specific house combinations

#### 3. Query Process

When a user provides their birth date and Thai day:

1. The `CalculatorService` calculates the 4 bases with 7 positions each
2. For each base (1-4) and position (1-7), the `ReadingService` calls:
   ```python
   readings = await self.reading_repository.get_by_base_and_position(base_num, position_num)
   ```

3. The `ReadingRepository` executes this SQL query:
   ```sql
   SELECT r.*, cc.file_name 
   FROM readings r
   JOIN category_combinations cc ON r.combination_id = cc.id
   JOIN categories c1 ON cc.category1_id = c1.id
   JOIN categories c2 ON cc.category2_id = c2.id
   WHERE c1.house_number = %s AND c2.house_number = %s
   ORDER BY r.id
   ```
   
   Where:
   - The first parameter is the base number (1-4)
   - The second parameter is the position number (1-7)

4. This query finds readings where:
   - The first category's house_number matches the base number
   - The second category's house_number matches the position number

5. The readings are then processed, scored, and used to generate the AI prompt

#### 4. Example Query Flow

For a user born on February 14, 1996 (Wednesday/พุธ):

1. Calculate Base 1: [4, 5, 6, 7, 1, 2, 3] (from Wednesday)
2. Calculate Base 2: [2, 3, 4, 5, 6, 7, 1] (from February)
3. Calculate Base 3: [3, 4, 5, 6, 7, 1, 2] (from 1996)
4. Calculate Base 4: [9, 12, 15, 18, 14, 10, 6] (sum of bases 1-3)

5. For Base 1, Position 2 (value 5):
   - Query: `WHERE c1.house_number = 1 AND c2.house_number = 2`
   - This finds readings related to ตนุ (Body/Self) and ธนัง (Wealth)

6. For Base 2, Position 3 (value 4):
   - Query: `WHERE c1.house_number = 2 AND c2.house_number = 3`
   - This finds readings related to ธนัง (Wealth) and สหัชชะ (Siblings)

7. And so on for all base-position combinations

This approach ensures that the fortune reading is based on the traditional Thai astrological system, using the calculated bases to find relevant readings in the database.

## API Endpoints

### Fortune Telling

```
POST /fortune
```

Request body:
```json
{
  "birth_date": "1990-01-01",
  "thai_day": "อาทิตย์",
  "question": "ฉันจะประสบความสำเร็จในชีวิตหรือไม่?",
  "language": "thai"
}
```

**Response:**

```json
{
  "birth_date": "1990-01-01",
  "thai_day": "อาทิตย์",
  "question": "ฉันจะประสบความสำเร็จในชีวิตหรือไม่?",
  "heading": "ร่างกาย (ตนุ) สัมพันธ์กับ ทรัพย์สิน (ธนัง)",
  "meaning": "การดูแลสุขภาพจะส่งผลดีต่อการเงิน ควรลงทุนในสุขภาพเพื่อลดค่าใช้จ่ายในอนาคต",
  "influence_type": "ดี"
}
```

### Web Form Submission

```
POST /fortune-web
```

Form data:
- birth_date: "1990-01-01"
- thai_day: "อาทิตย์"
- question: "ฉันจะประสบความสำเร็จในชีวิตหรือไม่?"

### Export PDF

```
GET /export-pdf?birth_date=1990-01-01&thai_day=อาทิตย์&question=ฉันจะประสบความสำเร็จในชีวิตหรือไม่?
```

Returns a PDF file with the fortune reading.

## Database Schema

### Tables

- **categories**
  - id: Primary key
  - name: Category name (e.g., กดุมภะ)
  - thai_meaning: Thai meaning (e.g., รายได้รายจ่าย)
  - house_number: House number in Thai astrology (1-12)
  - house_type: Type of house influence (กาลปักษ์, เกณฑ์ชะตา, จร)

- **category_combinations**
  - id: Primary key
  - file_name: Original JSON filename without extension
  - category1_id: Foreign key to categories
  - category2_id: Foreign key to categories
  - category3_id: Foreign key to categories (nullable)

- **readings**
  - id: Primary key
  - combination_id: Foreign key to category_combinations
  - heading: Reading heading (e.g., "ร่างกาย (ตนุ) สัมพันธ์กับ ทรัพย์สิน (ธนัง)")
  - meaning: Reading content
  - influence_type: Type of influence (ดี, ไม่ดี, ปานกลาง)

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables (see `.env.example`)
6. Run the application: `uvicorn app.main:app --reload`

## Development

### Running Tests

```
pytest
```

### Code Style

The project follows PEP 8 guidelines with a maximum line length of 100 characters.

## License

This project is licensed under the MIT License - see the LICENSE file for details.