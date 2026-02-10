"""Configuration loader utility"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file (defaults to config/config.yaml)

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default to config/config.yaml relative to project root
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def get_arxiv_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ArXiv-specific configuration"""
    return config.get('arxiv', {})


def get_filtering_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract filtering-specific configuration"""
    return config.get('filtering', {})


def get_llm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract LLM-specific configuration"""
    return config.get('llm', {})


def get_keywords(config: Dict[str, Any]) -> Dict[str, list]:
    """Extract research keywords"""
    return config.get('keywords', {})
