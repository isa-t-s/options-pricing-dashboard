from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class OptionParameters:
    spot_price: float
    strike_price: float
    time_to_expiry: float  # in years
    risk_free_rate: float
    dividend_yield: float = 0.0
    volatility: float
    option_type: str = "call"  # "call" or "put"

@dataclass
class PricingResult:
    price: float
    computation_time: float
    model_name: str
    greeks: Dict[str, float] = None
    parameters: Dict[str, Any] = None

class BasePricingModel(ABC):
    """Abstract base class for all pricing models"""
    
    @abstractmethod
    def calculate(self, params: OptionParameters, **kwargs) -> PricingResult:
        """Calculate option price and Greeks"""
        pass
    
    @abstractmethod
    def calculate_greeks(self, params: OptionParameters, **kwargs) -> Dict[str, float]:
        """Calculate option Greeks"""
        pass
    
    def _time_calculation(self, func, *args, **kwargs):
        """Helper method to time calculations"""
        start_time = time.time()
        result = func(*args, **kwargs)
        computation_time = time.time() - start_time
        return result, computation_time