import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

def black_scholes(type, S, K, T, rf, sigma):

    r=np.log(1+rf) # create continuous-time risk-free rate

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if type == "call":
        option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif type == "put":
        option_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("Invalid option type. Choose 'call' or 'put'.")

    return option_price


def implied_volatility(type, option_price, S, K, T, r):

    def objective(sigma):
        return black_scholes(type, S, K, T, r, sigma) - option_price

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return np.nan