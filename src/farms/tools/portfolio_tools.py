import numpy as np
from scipy.optimize import minimize

def describe(name, series):
    std = np.std(series)         # Compute the standard deviation (volatility)
    mean = np.mean(series)       # Compute the mean (average return)
    # Print formatted output with consistent spacing and precision
    print(f"{name:20s} |  Mean: {mean:.4f} | Std Dev: {std:.6f}")


def portfolio_volatility(weights, covariance_matrix):
    return np.sqrt(weights.T @ covariance_matrix @ weights)  # Essential Math Fact #5


def EFRS_portfolio(target_return, expected_returns, covariance_matrix):

    # Define constraints (tuple with two dictionaries)
    constraints = (# Constraint 1: Ensure portfolio return equals the target return
        # "type": "eq" specifies an equality constraint (must be exactly zero)
        # "fun": defines the function
        {"type": "eq", "fun": lambda w: w.T @ expected_returns - target_return},

        # Constraint 2: Ensure portfolio weights sum to 1 (fully invested)
        # "type": "eq" specifies an equality constraint (must be exactly zero)
        # "fun": defines the function
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},)

    # starting values
    N = expected_returns.shape[0]
    initial_weights = np.ones(N) / N

    # Python's version of Excel Solver
    # the function to minimize is portfolio_volatility
    # the variables to change are defined by the first input to the function
    # in this case the first argument is the vector of portfolio weights
    result = minimize(fun=portfolio_volatility,  # function to minimize
        x0=initial_weights,  # starting values
        args=(covariance_matrix),  # additional arguments needed for function
        method="SLSQP",  # minimization method
        constraints=constraints,  # constraints
    )

    optimal_weights=result.x
    Ereturn = optimal_weights.T @ expected_returns
    volatility = portfolio_volatility(optimal_weights, covariance_matrix)

    return result.x, Ereturn, volatility


def portfolio_sharpe(weights: np.ndarray, expected_returns: np.ndarray,
                     covariance_matrix: np.ndarray, rf=None, zerocost=None) -> float:
    """
    Computes the Sharpe ratio of a portfolio given the asset weights, expected returns,
    covariance matrix, and risk-free rate.

    Parameters:
    -----------
    weights : np.ndarray
        A 1D NumPy array of portfolio weights (shape: `(n_assets,)`).
    expected_returns : np.ndarray
        A 1D NumPy array of expected returns for each asset (shape: `(n_assets,)`).
    covariance_matrix : np.ndarray
        A 2D NumPy array representing the covariance matrix of asset returns (shape: `(n_assets, n_assets)`).
    rf : float
        The risk-free rate.

    Returns:
    --------
    float
        The Sharpe ratio of the portfolio.

    Raises:
    -------
    TypeError:
        If any of the inputs are not NumPy arrays.
    ValueError:
        If the dimensions of inputs do not match.
    """

    # Enforce that all inputs are NumPy arrays
    if not isinstance(weights, np.ndarray):
        raise TypeError("weights must be a NumPy array")
    if not isinstance(expected_returns, np.ndarray):
        raise TypeError("expected_returns must be a NumPy array")
    if not isinstance(covariance_matrix, np.ndarray):
        raise TypeError("covariance_matrix must be a NumPy array")

    # Ensure correct dimensions
    if weights.ndim != 1:
        raise ValueError("weights must be a 1D vector")
    if expected_returns.ndim != 1:
        raise ValueError("expected_returns must be a 1D vector")
    if covariance_matrix.ndim != 2:
        raise ValueError("covariance_matrix must be a 2D array")

    # Get the number of assets from expected returns and weights
    n_assets = expected_returns.shape[0]

    # Check that weights and expected returns have the same length
    if weights.shape[0] != n_assets:
        raise ValueError(f"weights and expected_returns must have the same length ({n_assets})")

    # Check that the covariance matrix is square and matches the number of assets
    if covariance_matrix.shape != (n_assets, n_assets):
        raise ValueError(f"covariance_matrix must be a square matrix of shape ({n_assets}, {n_assets})")

    # Compute portfolio return as the weighted sum of expected asset returns
    port_ret = weights.T @ expected_returns

    # Compute portfolio volatility using the given covariance matrix
    port_vol = portfolio_volatility(weights, covariance_matrix)

    if zerocost == True:
        Sharpe=(port_ret) / port_vol
    else:
        Sharpe=(port_ret - rf) / port_vol

    # Compute and return the Sharpe ratio (excess return divided by risk)
    return Sharpe


def tangent_portfolio(expected_returns, covariance_matrix, rf=None, factors=None):
    """
    Calculates the weights, expected return, and volatility of the tangent portfolio.

    Parameters:
    expected_returns (np.array): Vector of expected returns for each asset.
    covariance_matrix (np.array): Covariance matrix of asset returns.
    rf (float): Risk-free rate of return.

    Returns:
    tuple: A tuple containing the tangent portfolio weights, expected return, and volatility.
    """
    N = expected_returns.shape[0]
    initial_weights = np.ones(N) / N  # Initialize as a 1D column vector

    if factors!=True:
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})  # Constraint: weights sum to 1

        # Define a lambda function to negate the output of portfolio_sharpe
        neg_portfolio_sharpe = lambda x, expected_returns, covariance_matrix, rf: -portfolio_sharpe(x, expected_returns, covariance_matrix, rf)

        # Perform optimization
        result = minimize(fun=neg_portfolio_sharpe, x0=initial_weights, args=(expected_returns, covariance_matrix, rf),
                      method="SLSQP", constraints=constraints)

        # Ensure result.x is reshaped as a column vector (N x 1)
        tangent_weights = result.x

        # Compute expected return and volatility for the tangent portfolio
        tangent_return = tangent_weights.T @ expected_returns
        tangent_volatility = portfolio_volatility(tangent_weights, covariance_matrix)
    else:
        constraints = ({'type': 'eq', 'fun': lambda x: x[0] - 1})  # Constraint: weights sum to 1

        # Define a lambda function to negate the output of portfolio_sharpe
        neg_portfolio_sharpe = lambda x, expected_returns, covariance_matrix: -portfolio_sharpe(x, expected_returns, covariance_matrix, zerocost=True)

        # Perform optimization
        result = minimize(fun=neg_portfolio_sharpe, x0=initial_weights, args=(expected_returns, covariance_matrix),
                      method="SLSQP", constraints=constraints)

        # Ensure result.x is reshaped as a column vector (N x 1)
        tangent_weights = result.x

        # Compute expected return and volatility for the tangent portfolio
        tangent_return = tangent_weights.T @ expected_returns
        tangent_volatility = portfolio_volatility(tangent_weights, covariance_matrix)


    return tangent_weights, tangent_return, tangent_volatility
