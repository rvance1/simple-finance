import statsmodels.api as sm
import pandas as pd


def intercept(y,x):
    x_with_intercept = sm.add_constant(x)

    # Fit the model: y = β0 + β1*x
    model = sm.OLS(y, x_with_intercept)
    results = model.fit()

    # Return the slope (coefficient of x)
    return results.params[0]  # The slope is the second parameter (after the intercept)


def slope(y,x):
    x_with_intercept = sm.add_constant(x)

    # Fit the model: y = β0 + β1*x
    model = sm.OLS(y, x_with_intercept)
    results = model.fit()

    # Return the slope (coefficient of x)
    return results.params[1]  # The slope is the second parameter (after the intercept)



def run_ols(X, Y, ci=0.95):
    """
    Runs OLS regression of Y on X and returns coefficients and confidence intervals.

    Parameters
    ----------
    X : pandas Series or DataFrame
        Independent variable(s)
    Y : pandas Series
        Dependent variable
    ci : float, default 0.95
        Confidence level (e.g., 0.95 for 95% CI)
    Returns
    -------
    results_df : pandas DataFrame
        Table with coefficient, lower CI, upper CI
    """

    # If X is a Series, convert to DataFrame
    if isinstance(X, pd.Series):
        X = X.to_frame()

    # Add constant for intercept
    X = sm.add_constant(X)

    # Fit model
    model = sm.OLS(Y, X).fit()

    # Confidence intervals
    alpha = 1 - ci
    ci_bounds = model.conf_int(alpha=alpha)
    ci_bounds.columns = ['ci_lower', 'ci_upper'] # nice names

    # Build output table (aligns by index: const, mkt-rf, etc.)
    results_df = pd.concat([model.params.rename('coef'), ci_bounds], axis=1)

    return results_df