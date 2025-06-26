export interface OptionParameters {
  symbol: string;
  optionType: 'call' | 'put';
  spotPrice: number;
  strikePrice: number;
  timeToExpiry: number;
  riskFreeRate: number;
  dividendYield: number;
  volatility: number;
}

export interface PricingResult {
  modelName: string;
  price: number;
  computationTime: number;
}

export interface GreeksResult {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}