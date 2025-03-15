# app/main.py
import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, Response, Form, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import time
import uvicorn
from datetime import datetime
from typing import Optional
import tempfile
import importlib.util

from app.api.router import router as fortune_router
from app.core.exceptions import FortuneServiceException
from app.config.settings import get_settings
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.services.reading_service import ReadingService, get_reading_service
from app.domain.meaning import Category, Reading

# Get settings
settings = get_settings()

# Ensure logs directory exists
logs_dir = os.path.join(settings.base_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Ensure static and templates directories exist
static_dir = os.path.join(settings.base_dir, "static")
templates_dir = os.path.join(settings.base_dir, "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(logs_dir, "app.log")
csv_log_file = os.path.join(logs_dir, "csv_operations.log")

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # Ensure UTF-8 encoding for Thai characters
        )
    ]
)

# Configure CSV operations logger
csv_logger = logging.getLogger('app.repository')
csv_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
csv_handler = RotatingFileHandler(
    csv_log_file,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3,
    encoding='utf-8'  # Ensure UTF-8 encoding for Thai characters
)
csv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
csv_logger.addHandler(csv_handler)

# Configure meaning service logger
meaning_logger = logging.getLogger('app.services.meaning')
meaning_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

# Get main logger
logger = logging.getLogger(__name__)
logger.info("Application starting up with logging configured")
logger.info(f"CSV operations will be logged to: {csv_log_file}")
logger.info(f"General logs will be written to: {log_file}")

# Try to import WeasyPrint for PDF generation
try:
    from weasyprint import HTML
    has_weasyprint = True
    logger.info("WeasyPrint successfully imported for PDF generation")
except ImportError:
    has_weasyprint = False
    logger.warning("WeasyPrint not available. PDF export functionality will be disabled.")
except Exception as e:
    has_weasyprint = False
    logger.warning(f"Error importing WeasyPrint: {str(e)}. PDF export functionality will be disabled.")

# Try to import ElementMatcher if needed
try:
    from app.scripts.element_matcher import ElementMatcher
    has_element_matcher = True
except ImportError:
    has_element_matcher = False
    logger.warning("ElementMatcher not available. Some functionality may be limited.")

# Check if jinja2 is available
has_jinja2 = importlib.util.find_spec("jinja2") is not None
if has_jinja2:
    try:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory=templates_dir)
        logger.info("Jinja2Templates successfully imported for HTML templating")
    except Exception as e:
        has_jinja2 = False
        logger.warning(f"Error initializing Jinja2Templates: {str(e)}. HTML templating functionality will be disabled.")
else:
    logger.warning("Jinja2 not available. HTML templating functionality will be disabled.")

# Create FastAPI app
app = FastAPI(
    title="Ongphra Chat API",
    description="API for fortune telling based on Thai astrology",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create a dummy templates object if Jinja2 is not available
if not has_jinja2:
    class DummyTemplates:
        def TemplateResponse(self, *args, **kwargs):
            return JSONResponse({"error": "HTML templating is not available"})
        
        def get_template(self, *args, **kwargs):
            class DummyTemplate:
                def render(self, *args, **kwargs):
                    return ""
            return DummyTemplate()
    
    templates = DummyTemplates()
    logger.warning("Using dummy templates due to missing Jinja2")

# Include routers
app.include_router(fortune_router)

# Register repositories and services for dependency injection
@app.on_event("startup")
async def startup_event():
    # Initialize repositories
    app.state.category_repository = CategoryRepository(
        os.path.join(settings.base_dir, "data", "categories.csv"),
        model_class=Category
    )
    app.state.reading_repository = ReadingRepository(
        os.path.join(settings.base_dir, "data", "readings.csv"),
        model_class=Reading
    )
    
    # Initialize services
    app.state.reading_service = ReadingService(
        app.state.reading_repository,
        app.state.category_repository
    )
    
    logging.info("Repositories and services initialized")

# Register dependencies
def get_category_repository():
    return app.state.category_repository

def get_reading_repository():
    return app.state.reading_repository

def get_reading_service_instance():
    return app.state.reading_service

app.dependency_overrides[CategoryRepository] = get_category_repository
app.dependency_overrides[ReadingRepository] = get_reading_repository
app.dependency_overrides[get_reading_service] = get_reading_service_instance

# Add middleware for request timing and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    logger.info(f"Response: {response.status_code} - Process time: {process_time:.4f}s")
    
    return response


# Exception handlers
@app.exception_handler(FortuneServiceException)
async def fortune_exception_handler(request: Request, exc: FortuneServiceException):
    """Handle FortuneServiceException with appropriate error message"""
    logger.error(f"FortuneServiceException: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with a generic error message"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # In production, don't expose the actual error
    if settings.debug:
        detail = str(exc)
    else:
        detail = "An internal server error occurred"
    
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


# Root endpoint - Web Interface
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint with web interface"""
    if not has_jinja2:
        return JSONResponse(
            status_code=503,
            content={"error": "HTML templating is not available"}
        )
        
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "Thai Fortune Teller"}
    )


# Web form submission endpoint
@app.post("/fortune-web", response_class=HTMLResponse)
async def fortune_web(
    request: Request,
    birth_date: str = Form(...),
    thai_day: str = Form(...),
    question: Optional[str] = Form(None)
):
    """Process fortune telling form submission"""
    logger.info(f"Web fortune request: birth_date={birth_date}, thai_day={thai_day}, question={question}")
    
    if not has_jinja2:
        return JSONResponse(
            status_code=503,
            content={"error": "HTML templating is not available"}
        )
    
    try:
        # Parse birth date
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        
        # Check if ElementMatcher is available
        if not has_element_matcher:
            return templates.TemplateResponse(
                "error.html", 
                {
                    "request": request, 
                    "title": "Feature Unavailable",
                    "error": "This feature is currently unavailable due to missing dependencies."
                }
            )
        
        # Get element matcher
        categories_csv = str(settings.categories_path)
        readings_csv = str(settings.readings_path)
        matcher = ElementMatcher(categories_csv, readings_csv)
        
        # Get meanings
        meanings = await matcher.get_meanings_for_birth_info(birth_date_obj, thai_day, question)
        
        # Render template with results
        return templates.TemplateResponse(
            "results.html", 
            {
                "request": request, 
                "title": "Fortune Results",
                "birth_date": birth_date,
                "thai_day": thai_day,
                "question": question,
                "meanings": meanings.items
            }
        )
    except Exception as e:
        logger.error(f"Error processing fortune request: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "title": "Error",
                "error": str(e) if settings.debug else "An error occurred processing your request."
            }
        )


# PDF Export endpoint
@app.get("/export-pdf")
async def export_pdf(
    request: Request,
    birth_date: str = Query(...),
    thai_day: str = Query(...),
    question: Optional[str] = Query(None)
):
    """Export fortune reading to PDF"""
    logger.info(f"PDF export request: birth_date={birth_date}, thai_day={thai_day}, question={question}")
    
    # Check if WeasyPrint is available
    if not has_weasyprint:
        if has_jinja2:
            return templates.TemplateResponse(
                "error.html", 
                {
                    "request": request, 
                    "title": "PDF Export Unavailable",
                    "error": "PDF export is currently unavailable due to missing dependencies."
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={"error": "PDF export is not available due to missing dependencies"}
            )
    
    try:
        # Parse birth date
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        
        # Check if ElementMatcher is available
        if not has_element_matcher:
            return templates.TemplateResponse(
                "error.html", 
                {
                    "request": request, 
                    "title": "Feature Unavailable",
                    "error": "This feature is currently unavailable due to missing dependencies."
                }
            )
        
        # Get element matcher
        categories_csv = str(settings.categories_path)
        readings_csv = str(settings.readings_path)
        matcher = ElementMatcher(categories_csv, readings_csv)
        
        # Get meanings
        meanings = await matcher.get_meanings_for_birth_info(birth_date_obj, thai_day, question)
        
        # Generate HTML content
        html_content = templates.get_template("pdf_template.html").render(
            title="Fortune Reading PDF",
            birth_date=birth_date,
            thai_day=thai_day,
            question=question,
            meanings=meanings.items
        )
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
        
        # Generate PDF from HTML
        HTML(string=html_content).write_pdf(pdf_path)
        
        # Generate filename for download
        filename = f"fortune_reading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return PDF file
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            background=lambda: os.unlink(pdf_path)  # Delete file after sending
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request, 
                "title": "PDF Export Error",
                "error": str(e) if settings.debug else "An error occurred generating the PDF."
            }
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    """Run the application directly"""
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug
    )