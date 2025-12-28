"""Domain layer exceptions"""


class DomainException(Exception):
    """Base exception for domain layer errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ValidationException(DomainException):
    """Exception raised for validation errors in domain entities"""
    pass


class RepositoryException(DomainException):
    """Exception raised for repository operation failures"""
    pass


class TranscriptionException(DomainException):
    """Exception raised for transcription-specific errors"""
    pass


class AudioFileException(DomainException):
    """Exception raised for audio file-specific errors"""
    pass


class ServiceException(DomainException):
    """Exception raised for service operation failures"""
    pass
