"""Logging configuration and utilities"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "paper_assistant", log_level: str = None) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Get log level from environment or use default
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # File handler with daily rotation
    log_file = log_dir / f"paper_assistant_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_paper_info(logger: logging.Logger, paper_dict: dict):
    """Log paper information in a structured format"""
    logger.info(f"Paper: {paper_dict.get('title', 'Unknown')}")
    logger.info(f"  ArXiv ID: {paper_dict.get('arxiv_id', 'N/A')}")
    logger.info(f"  Authors: {', '.join(paper_dict.get('authors', [])[:3])}...")
    logger.info(f"  Categories: {', '.join(paper_dict.get('categories', []))}")
