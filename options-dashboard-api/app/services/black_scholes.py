import math
from scipy.stats import norm
from typing import Dict
from .base_model import BasePricingModel, OptionParameters, PricingResult

class BlackScholesModel(BasePricingModel):
    
    def calculate(self, params: OptionParameters, **kwargs) -> PricingResult:
        """Calculate Black-Scholes option price and Greeks"""
        price, greeks, computation_time = self._time_calculation(
            self._calculate_price_and_greeks, params
        )
        
        return PricingResult(
            price=price,
            computation_time=computation_time,
            model_name="Black-Scholes",
            greeks=greeks
        )
    
    def calculate_greeks(self, params: OptionParameters, **kwargs) -> Dict[str, float]:
        """Calculate only the Greeks (faster when price not needed)"""
        _, greeks, _ = self._calculate_price_and_greeks(params)
        return greeks
    
    def _calculate_price_and_greeks(self, params: OptionParameters):
        """Internal method that calculates both price and Greeks"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        # Calculate d1 and d2
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Calculate option price
        if params.option_type.lower() == "call":
            price = (S * math.exp(-q * T) * norm.cdf(d1) - 
                    K * math.exp(-r * T) * norm.cdf(d2))
        else:  # put
            price = (K * math.exp(-r * T) * norm.cdf(-d2) - 
                    S * math.exp(-q * T) * norm.cdf(-d1))
        
        # Calculate Greeks
        greeks = self._calculate_greeks_analytical(params, d1, d2)
        
        return price, greeks
    
    def _calculate_greeks_analytical(self, params: OptionParameters, d1: float, d2: float) -> Dict[str, float]:
        """Calculate Greeks using analytical formulas"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        # Common calculations
        nd1 = norm.cdf(d1)
        nd2 = norm.cdf(d2)
        pdf_d1 = norm.pdf(d1)
        
        if params.option_type.lower() == "call":
            delta = math.exp(-q * T) * nd1
            theta = ((-S * pdf_d1 * sigma * math.exp(-q * T)) / (2 * math.sqrt(T)) -
                    r * K * math.exp(-r * T) * nd2 +
                    q * S * math.exp(-q * T) * nd1)
            rho = K * T * math.exp(-r * T) * nd2 / 100
        else:  # put
            delta = -math.exp(-q * T) * norm.cdf(-d1)
            theta = ((-S * pdf_d1 * sigma * math.exp(-q * T)) / (2 * math.sqrt(T)) +
                    r * K * math.exp(-r * T) * norm.cdf(-d2) -
                    q * S * math.exp(-q * T) * norm.cdf(-d1))
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
        
        # Gamma and Vega are the same for calls and puts
        gamma = (pdf_d1 * math.exp(-q * T)) / (S * sigma * math.sqrt(T))
        vega = S * math.exp(-q * T) * pdf_d1 * math.sqrt(T) / 100
        
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta / 365,  # Convert to per-day
            "vega": vega,
            "rho": rho
        }