import numpy as np
import math
from typing import Dict
from .base_model import BasePricingModel, OptionParameters, PricingResult

class BinomialTreeModel(BasePricingModel):
    
    def calculate(self, params: OptionParameters, steps: int = 100, **kwargs) -> PricingResult:
        """Calculate binomial tree option price and Greeks"""
        price, computation_time = self._time_calculation(
            self._calculate_price, params, steps
        )
        
        # Calculate Greeks using finite differences
        greeks = self.calculate_greeks(params, steps=steps)
        
        return PricingResult(
            price=price,
            computation_time=computation_time,
            model_name="Binomial Tree",
            greeks=greeks,
            parameters={"steps": steps}
        )
    
    def calculate_greeks(self, params: OptionParameters, steps: int = 100, **kwargs) -> Dict[str, float]:
        """Calculate Greeks using finite differences"""
        return self._calculate_greeks_finite_diff(params, steps)
    
    def _calculate_price(self, params: OptionParameters, steps: int) -> float:
        """Calculate option price using binomial tree"""
        S = params.spot_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield
        sigma = params.volatility
        
        # Calculate parameters
        dt = T / steps
        u = math.exp(sigma * math.sqrt(dt))  # Up factor
        d = 1 / u  # Down factor
        p = (math.exp((r - q) * dt) - d) / (u - d)  # Risk-neutral probability
        
        # Initialize stock price tree
        stock_prices = np.zeros((steps + 1, steps + 1))
        
        # Fill the stock price tree
        for i in range(steps + 1):
            for j in range(i + 1):
                stock_prices[j, i] = S * (u ** (i - j)) * (d ** j)
        
        # Initialize option value tree
        option_values = np.zeros((steps + 1, steps + 1))
        
        # Fill terminal option values
        for j in range(steps + 1):
            if params.option_type.lower() == "call":
                option_values[j, steps] = max(0, stock_prices[j, steps] - K)
            else:
                option_values[j, steps] = max(0, K - stock_prices[j, steps])
        
        # Backward induction
        discount = math.exp(-r * dt)
        for i in range(steps - 1, -1, -1):
            for j in range(i + 1):
                option_values[j, i] = discount * (
                    p * option_values[j, i + 1] + (1 - p) * option_values[j + 1, i + 1]
                )
        
        return option_values[0, 0]
    
    def _calculate_greeks_finite_diff(self, params: OptionParameters, steps: int) -> Dict[str, float]:
        """Calculate Greeks using finite differences"""
        # Base price
        price_base = self._calculate_price(params, steps)
        
        # Delta: finite difference with 1% spot price change
        dS = params.spot_price * 0.01
        params_up = OptionParameters(**params.__dict__)
        params_down = OptionParameters(**params.__dict__)
        params_up.spot_price += dS
        params_down.spot_price -= dS
        
        price_up = self._calculate_price(params_up, steps)
        price_down = self._calculate_price(params_down, steps)
        delta = (price_up - price_down) / (2 * dS)
        
        # Gamma: second derivative
        gamma = (price_up - 2 * price_base + price_down) / (dS ** 2)
        
        # Theta: finite difference with time (1 day change)
        dt = 1/365
        params_theta = OptionParameters(**params.__dict__)
        params_theta.time_to_expiry = max(params.time_to_expiry - dt, dt)
        price_theta = self._calculate_price(params_theta, steps)
        theta = (price_theta - price_base)  # Per day change
        
        # Vega: finite difference with volatility (1% change)
        dv = 0.01
        params_vega = OptionParameters(**params.__dict__)
        params_vega.volatility += dv
        price_vega = self._calculate_price(params_vega, steps)
        vega = (price_vega - price_base) / 100  # Convert to 1% change
        
        # Rho: finite difference with interest rate (1% change)
        dr = 0.01
        params_rho = OptionParameters(**params.__dict__)
        params_rho.risk_free_rate += dr
        price_rho = self._calculate_price(params_rho, steps)
        rho = (price_rho - price_base) / 100  # Convert to 1% change
        
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho
        }