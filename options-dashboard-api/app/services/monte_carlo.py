import numpy as np
import math
from typing import Dict
from .base_model import BasePricingModel, OptionParameters, PricingResult

class MonteCarloModel(BasePricingModel):
    
    def calculate(self, params: OptionParameters, simulations: int = 10000, **kwargs) -> PricingResult:
        """Calculate Monte Carlo option price and Greeks"""
        price, computation_time = self._time_calculation(
            self._calculate_price, params, simulations
        )
        
        # Calculate Greeks using finite differences
        greeks = self.calculate_greeks(params, simulations=simulations)
        
        return PricingResult(
            price=price,
            computation_time=computation_time,
            model_name="Monte Carlo",
            greeks=greeks,
            parameters={"simulations": simulations}
        )
    
    def calculate_greeks(self, params: OptionParameters, simulations: int = 10000, **kwargs) -> Dict[str, float]:
        """Calculate Greeks using finite differences"""
        return self._calculate_greeks_finite_diff(params, simulations)
    
    def _calculate_price(self, params: OptionParameters, simulations: int, seed: int = 42) -> float:
        """Calculate option price using Monte Carlo simulation"""
        # Set seed for reproducible results during development
        np.random.seed(seed)
        
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        # Generate random paths using geometric Brownian motion
        z = np.random.standard_normal(simulations)
        
        # Calculate final stock prices
        ST = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * math.sqrt(T) * z)
        
        # Calculate payoffs
        if params.option_type.lower() == "call":
            payoffs = np.maximum(0, ST - K)
        else:  # put
            payoffs = np.maximum(0, K - ST)
        
        # Calculate option price as discounted expected payoff
        price = math.exp(-r * T) * np.mean(payoffs)
        
        return price
    
    def _calculate_greeks_finite_diff(self, params: OptionParameters, simulations: int) -> Dict[str, float]:
        """Calculate Greeks using finite differences"""
        # Use same seed for all calculations to reduce noise
        seed = 42
        
        # Base price
        price_base = self._calculate_price(params, simulations, seed)
        
        # Delta: finite difference with 1% spot price change
        dS = params.spot_price * 0.01
        params_up = OptionParameters(**params.__dict__)
        params_down = OptionParameters(**params.__dict__)
        params_up.spot_price += dS
        params_down.spot_price -= dS
        
        price_up = self._calculate_price(params_up, simulations, seed)
        price_down = self._calculate_price(params_down, simulations, seed)
        delta = (price_up - price_down) / (2 * dS)
        
        # Gamma: second derivative
        gamma = (price_up - 2 * price_base + price_down) / (dS ** 2)
        
        # Theta: finite difference with time (1 day change)
        dt = 1/365
        params_theta = OptionParameters(**params.__dict__)
        params_theta.time_to_expiry = max(params.time_to_expiry - dt, dt)
        price_theta = self._calculate_price(params_theta, simulations, seed)
        theta = (price_theta - price_base)  # Per day change
        
        # Vega: finite difference with volatility (1% change)
        dv = 0.01
        params_vega = OptionParameters(**params.__dict__)
        params_vega.volatility += dv
        price_vega = self._calculate_price(params_vega, simulations, seed)
        vega = (price_vega - price_base) / 100  # Convert to 1% change
        
        # Rho: finite difference with interest rate (1% change)
        dr = 0.01
        params_rho = OptionParameters(**params.__dict__)
        params_rho.risk_free_rate += dr
        price_rho = self._calculate_price(params_rho, simulations, seed)
        rho = (price_rho - price_base) / 100  # Convert to 1% change
        
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho
        }