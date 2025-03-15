# app/core/exceptions.py

class FortuneServiceException(Exception):
    """Base exception for the fortune service"""
    pass


class CalculationError(FortuneServiceException):
    """Exception raised for errors in birth calculation"""
    pass


class MeaningExtractionError(FortuneServiceException):
    """Exception raised for errors in meaning extraction"""
    pass


class PromptGenerationError(FortuneServiceException):
    """Exception raised for errors in prompt generation"""
    pass


class ResponseGenerationError(FortuneServiceException):
    """Exception raised for errors in response generation"""
    pass


class RepositoryError(FortuneServiceException):
    """Exception raised for errors in data access"""
    pass


class ValidationError(FortuneServiceException):
    """Exception raised for validation errors"""
    pass


class ReadingError(FortuneServiceException):
    """Exception raised for errors in reading extraction or processing"""
    pass