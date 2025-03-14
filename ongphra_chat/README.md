# Thai Fortune Teller API

A modern API for Thai fortune telling based on the ancient "7 Numbers 9 Bases" (เลข 7 ตัว 9 ฐาน) divination system.

## Features

- **Birth Chart Calculation**: Calculates birth bases according to traditional Thai numerology
- **AI-Powered Readings**: Uses OpenAI to generate natural and insightful fortune readings
- **Domain-Driven Design**: Clean, modular architecture for maintainability and extensibility
- **RESTful API**: Simple and well-documented FastAPI endpoints

## Architecture

The application follows a domain-driven design with clean separation of concerns:

- **API Layer**: Handles HTTP requests and responses
- **Core Service**: Orchestrates the application flow
- **Domain Services**: Specialized services for calculations, meanings, and responses
- **Domain Models**: Structured data models for different aspects of the system
- **Repositories**: Data access layer for categories and readings

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/thai-fortune-teller.git
cd thai-fortune-teller
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key
MODEL_NAME=gpt-4-turbo
DEBUG=True
```

### Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.

### Docker Deployment

Build and run with Docker:

```bash
docker build -t thai-fortune-teller .
docker run -p 8000:8000 --env-file .env thai-fortune-teller
```

## API Endpoints

### Get Fortune Reading

```
POST /fortune
```

**Request Body:**

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
  "fortune": "คำทำนายจากหมอดู...",
  "bases": {
    "base1": [1, 2, 3, 4, 5, 6, 7],
    "base2": [1, 2, 3, 4, 5, 6, 7],
    "base3": [3, 4, 5, 6, 7, 1, 2],
    "base4": [5, 8, 11, 14, 17, 13, 16]
  },
  "birth_info": {
    "date": "1990-01-01",
    "day": "อาทิตย์",
    "day_value": 1,
    "month": 1,
    "year_animal": "ระกา",
    "year_start_number": 10
  }
}
```

### General Interaction (No Birth Info)

If you don't provide birth information, the API still responds with general guidance:

```json
{
  "question": "ศาสตร์เลข 7 ตัว 9 ฐานคืออะไร?",
  "language": "thai"
}
```

## Project Structure

```
thai_fortune_teller/
│
├── app/                         # Main application package
│   ├── api/                     # API layer
│   ├── core/                    # Core application logic
│   ├── services/                # Domain services
│   ├── domain/                  # Domain models
│   ├── repository/              # Data access layer
│   ├── config/                  # Configuration
│   └── utils/                   # Utilities
│
├── data/                        # Data files
│   ├── categories.csv           # Category definitions
│   └── readings.csv             # Readings data
│
├── tests/                       # Tests
├── .env                         # Environment variables
├── requirements.txt             # Project dependencies
└── Dockerfile                   # Docker configuration
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.