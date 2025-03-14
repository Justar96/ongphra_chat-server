# Create main project directory
New-Item -Path "ongphra_chat" -ItemType Directory -Force

# Create app directory structure
New-Item -Path "ongphra_chat\app" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\api" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\core" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\services" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\domain" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\repository" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\config" -ItemType Directory -Force
New-Item -Path "ongphra_chat\app\utils" -ItemType Directory -Force
New-Item -Path "ongphra_chat\data" -ItemType Directory -Force
New-Item -Path "ongphra_chat\tests" -ItemType Directory -Force

# Create __init__.py files
New-Item -Path "ongphra_chat\app\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\api\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\core\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\services\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\domain\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\repository\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\config\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\utils\__init__.py" -ItemType File -Force
New-Item -Path "ongphra_chat\tests\__init__.py" -ItemType File -Force

# Create main app files
New-Item -Path "ongphra_chat\app\main.py" -ItemType File -Force

# Create API layer files
New-Item -Path "ongphra_chat\app\api\router.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\api\schemas.py" -ItemType File -Force

# Create core files
New-Item -Path "ongphra_chat\app\core\service.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\core\exceptions.py" -ItemType File -Force

# Create services files
New-Item -Path "ongphra_chat\app\services\calculator.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\services\meaning.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\services\prompt.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\services\response.py" -ItemType File -Force

# Create domain model files
New-Item -Path "ongphra_chat\app\domain\birth.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\domain\bases.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\domain\meaning.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\domain\response.py" -ItemType File -Force

# Create repository files
New-Item -Path "ongphra_chat\app\repository\base.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\repository\csv_repository.py" -ItemType File -Force
New-Item -Path "ongphra_chat\app\repository\db_repository.py" -ItemType File -Force

# Create config files
New-Item -Path "ongphra_chat\app\config\settings.py" -ItemType File -Force

# Create utilities files
New-Item -Path "ongphra_chat\app\utils\helpers.py" -ItemType File -Force

# Create data files
New-Item -Path "ongphra_chat\data\categories.csv" -ItemType File -Force
New-Item -Path "ongphra_chat\data\readings.csv" -ItemType File -Force

# Create test files
New-Item -Path "ongphra_chat\tests\test_calculator.py" -ItemType File -Force
New-Item -Path "ongphra_chat\tests\test_meaning.py" -ItemType File -Force
New-Item -Path "ongphra_chat\tests\test_prompt.py" -ItemType File -Force
New-Item -Path "ongphra_chat\tests\test_api.py" -ItemType File -Force

Write-Host "OngPhra Chat project structure has been created successfully!" -ForegroundColor Green