from typing import List, Dict, Any
from .base_model import OptionParameters, PricingResult
from .black_scholes import BlackScholesModel
from .binomial_tree import BinomialTreeModel
from .monte_carlo import MonteCarloModel

class PricingEngine:
    """Central engine that orchestrates all pricing models"""
    
    def __init__(self):
        self.models = {
            'black_scholes': BlackScholesModel(),
            'binomial': BinomialTreeModel(),
            'monte_carlo': MonteCarloModel()
        }
    
    def calculate_all_models(self, 
                           params: OptionParameters,
                           binomial_steps: int = 100,
                           monte_carlo_simulations: int = 10000) -> List[PricingResult]:
        """Calculate option price using all available models"""
        results = []
        
        # Black-Scholes (fastest, analytical)
        try:
            bs_result = self.models['black_scholes'].calculate(params)
            results.append(bs_result)
        except Exception as e:
            print(f"Black-Scholes calculation failed: {e}")
        
        # Binomial Tree
        try:
            binomial_result = self.models['binomial'].calculate(params, steps=binomial_steps)
            results.append(binomial_result)
        except Exception as e:
            print(f"Binomial tree calculation failed: {e}")
        
        # Monte Carlo
        try:
            mc_result = self.models['monte_carlo'].calculate(params, simulations=monte_carlo_simulations)
            results.append(mc_result)
        except Exception as e:
            print(f"Monte Carlo calculation failed: {e}")
        
        return results
    
    def calculate_single_model(self, 
                             model_name: str, 
                             params: OptionParameters, 
                             **kwargs) -> PricingResult:
        """Calculate using a specific model"""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        return self.models[model_name].calculate(params, **kwargs)
    
    def get_model_comparison_metrics(self, results: List[PricingResult]) -> Dict[str, Any]:
        """Calculate comparison metrics across models"""
        if not results:
            return {}
        
        prices = [r.price for r in results]
        computation_times = [r.computation_time for r in results]
        
        avg_price = sum(prices) / len(prices)
        max_diff = max(abs(p - avg_price) for p in prices)
        max_diff_pct = (max_diff / avg_price * 100) if avg_price > 0 else 0
        
        return {
            "average_price": round(avg_price, 6),
            "max_difference": round(max_diff, 6),
            "max_difference_pct": round(max_diff_pct, 4),
            "total_computation_time": round(sum(computation_times) * 1000, 2),  # Convert to ms
            "fastest_model": min(results, key=lambda r: r.computation_time).model_name,
            "slowest_model": max(results, key=lambda r: r.computation_time).model_name,
            "price_range": {
                "min": round(min(prices), 6),
                "max": round(max(prices), 6)
            }
        }
    
    def validate_parameters(self, params: OptionParameters) -> List[str]:
        """Validate option parameters and return list of errors"""
        errors = []
        
        if params.spot_price <= 0:
            errors.append("Spot price must be positive")
        
        if params.strike_price <= 0:
            errors.append("Strike price must be positive")
        
        if params.time_to_expiry <= 0:
            errors.append("Time to expiry must be positive")
        
        if params.volatility <= 0:
            errors.append("Volatility must be positive")
        
        if params.option_type.lower() not in ['call', 'put']:
            errors.append("Option type must be 'call' or 'put'")
        
        if params.time_to_expiry > 10:  # More than 10 years
            errors.append("Time to expiry seems unusually long (>10 years)")
        
        if params.volatility > 5:  # More than 500%
            errors.append("Volatility seems unusually high (>500%)")
        
        return errors

# Create global instance
pricing_engine = PricingEngine()