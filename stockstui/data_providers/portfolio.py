from dataclasses import dataclass
from typing import List, Dict, Optional
import json
from pathlib import Path

@dataclass
class Portfolio:
    """
    Represents a portfolio of stocks for display grouping purposes.
    
    This simplified model is used to group stocks together for display,
    without tracking transactions or performance metrics.
    """
    name: str
    description: str
    tickers: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        """Create a Portfolio instance from a dictionary."""
        return cls(
            name=data.get('name', 'Unnamed Portfolio'),
            description=data.get('description', ''),
            tickers=data.get('tickers', [])
        )
    
    def to_dict(self) -> Dict:
        """Convert the Portfolio instance to a dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'tickers': self.tickers
        }
    
    def add_ticker(self, ticker: str) -> None:
        """Add a ticker to the portfolio if it doesn't already exist."""
        if ticker not in self.tickers:
            self.tickers.append(ticker)
    
    def remove_ticker(self, ticker: str) -> None:
        """Remove a ticker from the portfolio."""
        if ticker in self.tickers:
            self.tickers.remove(ticker)

def load_portfolios(file_path: Path) -> Dict[str, Portfolio]:
    """
    Load portfolios from a JSON file.
    
    Args:
        file_path: Path to the portfolios JSON file.
        
    Returns:
        A dictionary mapping portfolio names to Portfolio objects.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        portfolios = {}
        for name, portfolio_data in data.items():
            portfolios[name] = Portfolio.from_dict(portfolio_data)
        
        return portfolios
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading portfolios: {e}")
        return {}

def save_portfolios(portfolios: Dict[str, Portfolio], file_path: Path) -> bool:
    """
    Save portfolios to a JSON file.
    
    Args:
        portfolios: Dictionary mapping portfolio names to Portfolio objects.
        file_path: Path to save the portfolios JSON file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        data = {name: portfolio.to_dict() for name, portfolio in portfolios.items()}
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        return True
    except IOError as e:
        print(f"Error saving portfolios: {e}")
        return False