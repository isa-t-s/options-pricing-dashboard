from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from app.services.pricing_engine import pricing_engine
from app.services.base_model import OptionParameters
import asyncio

router = APIRouter()

class OptionRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    option_type: str = Field(..., description="'call' or 'put'")
    spot_price: float = Field(..., gt=0, description="Current stock price")
    strike_price: float = Field(..., gt=0, description="Strike price")
    time_to_expiry: float = Field(..., gt=0, description="Time to expiry in years")
    risk_free_rate: float = Field(..., description="Risk-free rate as decimal")
    dividend_yield: float = Field(0.0, ge=0, description="Dividend yield as decimal")
    volatility: float = Field(..., gt=0, description="Volatility as decimal")
    
    # Model-specific parameters
    binomial_steps: int = Field(100, ge=10, le=1000, description="Number of binomial steps")
    monte_carlo_simulations: int = Field(10000, ge=1000, le=100000, description="MC simulations")
    
    @validator('option_type')
    def validate_option_type(cls, v):
        if v.lower() not in ['call', 'put']:
            raise ValueError('Option type must be "call" or "put"')
        return v.lower()

class PricingResponse(BaseModel):
    symbol: str
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    validation_errors: List[str] = []

@router.post("/price", response_model=PricingResponse)
async def calculate_option_price(request: OptionRequest):
    """Calculate option price using all pricing models"""
    try:
        # Convert request to OptionParameters
        params = OptionParameters(
            spot_price=request.spot_price,
            strike_price=request.strike_price,
            time_to_expiry=request.time_to_expiry,
            risk_free_rate=request.risk_free_rate,
            dividend_yield=request.dividend_yield,
            volatility=request.volatility,
            option_type=request.option_type
        )
        
        # Validate parameters
        validation_errors = pricing_engine.validate_parameters(params)
        if validation_errors:
            return PricingResponse(
                symbol=request.symbol,
                results=[],
                summary={},
                validation_errors=validation_errors
            )
        
        # Calculate using all models
        pricing_results = pricing_engine.calculate_all_models(
            params,
            binomial_steps=request.binomial_steps,
            monte_carlo_simulations=request.monte_carlo_simulations
        )
        
        # Format results for API response
        formatted_results = []
        for result in pricing_results:
            formatted_result = {
                "model_name": result.model_name,
                "price": round(result.price, 6),
                "computation_time": round(result.computation_time * 1000, 2),  # Convert to ms
                "greeks": {k: round(v, 6) for k, v in (result.greeks or {}).items()}
            }
            
            # Add model-specific parameters
            if result.parameters:
                formatted_result["parameters"] = result.parameters
            
            formatted_results.append(formatted_result)
        
        # Calculate summary statistics
        summary = pricing_engine.get_model_comparison_metrics(pricing_results)
        
        return PricingResponse(
            symbol=request.symbol,
            results=formatted_results,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

@router.get("/greeks/{symbol}")
async def calculate_greeks(
    symbol: str,
    spot_price: float,
    strike_price: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
    model: str = "black_scholes"
):
    """Calculate option Greeks using specified model"""
    try:
        params = OptionParameters(
            spot_price=spot_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            volatility=volatility,
            option_type=option_type.lower()
        )
        
        # Validate parameters
        validation_errors = pricing_engine.validate_parameters(params)
        if validation_errors:
            raise HTTPException(status_code=400, detail=f"Parameter validation failed: {validation_errors}")
        
        # Calculate using specified model
        result = pricing_engine.calculate_single_model(model, params)
        
        return {
            "symbol": symbol,
            "model": result.model_name,
            "greeks": result.greeks,
            "price": round(result.price, 6),
            "computation_time": round(result.computation_time * 1000, 2)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

@router.post("/heatmap")
async def generate_heatmap(
    request: OptionRequest,
    spot_range: List[float] = [0.8, 1.2],  # As multipliers of current spot
    time_range: List[float] = [0.1, 1.0],  # Time to expiry range in years
    grid_size: int = 20,
    model: str = "black_scholes"
):
    """Generate data for heat map visualization"""
    try:
        base_params = OptionParameters(
            spot_price=request.spot_price,
            strike_price=request.strike_price,
            time_to_expiry=request.time_to_expiry,
            risk_free_rate=request.risk_free_rate,
            dividend_yield=request.dividend_yield,
            volatility=request.volatility,
            option_type=request.option_type
        )
        
        # Validate base parameters
        validation_errors = pricing_engine.validate_parameters(base_params)
        if validation_errors:
            raise HTTPException(status_code=400, detail=f"Parameter validation failed: {validation_errors}")
        
        # Generate ranges
        import numpy as np
        spot_prices = np.linspace(
            request.spot_price * spot_range[0],
            request.spot_price * spot_range[1],
            grid_size
        )
        
        times = np.linspace(time_range[0], time_range[1], grid_size)
        
        # Calculate price matrix
        price_matrix = []
        delta_matrix = []
        gamma_matrix = []
        
        for t in times:
            price_row = []
            delta_row = []
            gamma_row = []
            
            for s in spot_prices:
                params = OptionParameters(
                    spot_price=s,
                    strike_price=base_params.strike_price,
                    time_to_expiry=t,
                    risk_free_rate=base_params.risk_free_rate,
                    dividend_yield=base_params.dividend_yield,
                    volatility=base_params.volatility,
                    option_type=base_params.option_type
                )
                
                result = pricing_engine.calculate_single_model(model, params)
                price_row.append(round(result.price, 6))
                delta_row.append(round(result.greeks.get("delta", 0), 6))
                gamma_row.append(round(result.greeks.get("gamma", 0), 6))
            
            price_matrix.append(price_row)
            delta_matrix.append(delta_row)
            gamma_matrix.append(gamma_row)
        
        return {
            "symbol": request.symbol,
            "model": model,
            "spot_prices": [round(float(s), 4) for s in spot_prices],
            "times": [round(float(t), 6) for t in times],
            "price_matrix": price_matrix,
            "delta_matrix": delta_matrix,
            "gamma_matrix": gamma_matrix,
            "parameters": {
                "strike_price": request.strike_price,
                "risk_free_rate": request.risk_free_rate,
                "volatility": request.volatility,
                "option_type": request.option_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Heatmap generation error: {str(e)}")

@router.get("/models")
async def get_available_models():
    """Get list of available pricing models"""
    return {
        "models": [
            {
                "name": "black_scholes",
                "display_name": "Black-Scholes",
                "description": "Analytical solution with exact Greeks",
                "parameters": []
            },
            {
                "name": "binomial",
                "display_name": "Binomial Tree",
                "description": "Discrete-time tree model",
                "parameters": ["steps"]
            },
            {
                "name": "monte_carlo",
                "display_name": "Monte Carlo",
                "description": "Stochastic simulation",
                "parameters": ["simulations"]
            }
        ]
    }