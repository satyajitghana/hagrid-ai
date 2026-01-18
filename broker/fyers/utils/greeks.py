"""
Options Greeks Calculator for Fyers.

Computes:
- Implied Volatility (Brent's root-finding method)
- Delta, Gamma, Theta (per day), Vega (per 1%), Rho (per 1%)

Uses Black-Scholes model for European-style options.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


# Default risk-free rate (annual, decimal)
DEFAULT_RISK_FREE_RATE = 0.065  # ~6.5% for India


def bs_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "CE"
) -> float:
    """
    Black-Scholes European option price.

    Args:
        S: Spot price
        K: Strike price
        T: Time-to-expiry in years
        r: Annual risk-free rate (decimal, e.g., 0.065 for 6.5%)
        sigma: Volatility (decimal, e.g., 0.20 for 20%)
        option_type: "CE" for Call, "PE" for Put

    Returns:
        Option price
    """
    if T <= 0:
        # At expiry, option value is intrinsic
        if option_type == "CE":
            return max(S - K, 0.0)
        else:
            return max(K - S, 0.0)

    if sigma <= 0:
        # Zero vol -> option is present value of intrinsic
        if option_type == "CE":
            return max(S - K * math.exp(-r * T), 0.0)
        else:
            return max(K * math.exp(-r * T) - S, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "CE":
        return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    else:
        return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "CE",
    tol: float = 1e-6,
    maxiter: int = 100
) -> float:
    """
    Compute implied volatility using Brent's root-finding method.

    Args:
        market_price: Observed market price of the option
        S: Spot price
        K: Strike price
        T: Time-to-expiry in years
        r: Risk-free rate (annual, decimal)
        option_type: "CE" or "PE"
        tol: Tolerance for convergence
        maxiter: Maximum iterations

    Returns:
        Implied volatility (decimal), or np.nan if computation fails
    """
    if market_price is None or market_price <= 0 or T <= 0:
        return np.nan

    def objective(sigma):
        return bs_price(S, K, T, r, sigma, option_type) - market_price

    low = 1e-6
    high = 5.0  # 500% vol as upper bound

    try:
        f_low = objective(low)
        f_high = objective(high)

        if np.sign(f_low) == np.sign(f_high):
            # Check if price is below intrinsic
            intrinsic = max(S - K, 0.0) if option_type == "CE" else max(K - S, 0.0)
            if market_price <= intrinsic + 1e-8:
                return 1e-6
            return np.nan

        iv = brentq(objective, low, high, xtol=tol, maxiter=maxiter)
        return float(iv)
    except Exception:
        return np.nan


def compute_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "CE"
) -> Dict[str, float]:
    """
    Compute option Greeks using Black-Scholes model.

    Args:
        S: Spot price
        K: Strike price
        T: Time-to-expiry in years
        r: Risk-free rate (annual, decimal)
        sigma: Implied volatility (decimal)
        option_type: "CE" or "PE"

    Returns:
        Dictionary with:
        - delta: Price sensitivity to underlying
        - gamma: Delta sensitivity to underlying
        - theta: Time decay per day (negative for long options)
        - vega: Price sensitivity to 1% change in volatility
        - rho: Price sensitivity to 1% change in interest rate
    """
    if T <= 0 or sigma is None or np.isnan(sigma) or sigma <= 0:
        return dict(delta=np.nan, gamma=np.nan, theta=np.nan, vega=np.nan, rho=np.nan)

    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    pdf_d1 = norm.pdf(d1)

    # Gamma (same for calls and puts)
    gamma = pdf_d1 / (S * sigma * sqrt_T)

    # Vega (same for calls and puts)
    # Raw vega is per unit vol, multiply by 0.01 for per 1% point
    vega_raw = S * pdf_d1 * sqrt_T
    vega_per_1pct = vega_raw * 0.01

    # Delta, Theta, Rho (differ for calls/puts)
    if option_type == "CE":
        delta = norm.cdf(d1)
        theta_raw = (
            -S * pdf_d1 * sigma / (2 * sqrt_T)
            - r * K * math.exp(-r * T) * norm.cdf(d2)
        )
        rho_raw = K * T * math.exp(-r * T) * norm.cdf(d2)
    else:
        delta = norm.cdf(d1) - 1
        theta_raw = (
            -S * pdf_d1 * sigma / (2 * sqrt_T)
            + r * K * math.exp(-r * T) * norm.cdf(-d2)
        )
        rho_raw = -K * T * math.exp(-r * T) * norm.cdf(-d2)

    # Theta per day (divide annual theta by 365)
    theta_per_day = theta_raw / 365.0

    # Rho per 1% point
    rho_per_1pct = rho_raw * 0.01

    return dict(
        delta=float(delta),
        gamma=float(gamma),
        theta=float(theta_per_day),
        vega=float(vega_per_1pct),
        rho=float(rho_per_1pct)
    )


def parse_expiry_to_epoch(expiry_field: Any) -> Optional[float]:
    """
    Parse expiry field to epoch seconds.

    Args:
        expiry_field: Can be:
            - Integer epoch (seconds or milliseconds)
            - ISO string like '2025-01-30T09:15:00' or '2025-01-30'
            - datetime object

    Returns:
        Epoch seconds as float, or None if parsing fails
    """
    if expiry_field is None:
        return None

    if isinstance(expiry_field, (int, float)):
        # If given in milliseconds (13 digits), convert
        if expiry_field > 1e12:
            return expiry_field / 1000.0
        return float(expiry_field)

    if isinstance(expiry_field, datetime):
        return expiry_field.timestamp()

    if isinstance(expiry_field, str):
        # Try numeric epoch string first (e.g., '1768903200')
        try:
            epoch = float(expiry_field)
            # If given in milliseconds (13 digits), convert
            if epoch > 1e12:
                return epoch / 1000.0
            return epoch
        except ValueError:
            pass

        # Try ISO formats
        try:
            dt = datetime.fromisoformat(expiry_field.replace('Z', '+00:00'))
            return dt.timestamp()
        except Exception:
            pass

        # Try common date formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(expiry_field, fmt)
                return dt.replace(tzinfo=timezone.utc).timestamp()
            except Exception:
                pass

    return None


def time_to_expiry_years(expiry_epoch: Optional[float]) -> float:
    """
    Calculate time to expiry in years.

    Args:
        expiry_epoch: Expiry timestamp in epoch seconds

    Returns:
        Time to expiry in years (0 if expired or invalid)
    """
    if expiry_epoch is None:
        return 0.0

    now = datetime.now(timezone.utc).timestamp()
    secs = max(0.0, expiry_epoch - now)
    return secs / (365.0 * 24.0 * 3600.0)


def compute_option_chain_greeks(
    options_chain: List[Dict[str, Any]],
    spot_price: float,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE
) -> List[Dict[str, Any]]:
    """
    Compute Greeks for an entire option chain.

    Args:
        options_chain: List of option data from Fyers option chain API
        spot_price: Current spot price of the underlying
        risk_free_rate: Annual risk-free rate (decimal)

    Returns:
        List of dictionaries with option data and computed Greeks
    """
    results = []

    for opt in options_chain:
        # Extract fields (handle various naming conventions)
        strike = opt.get("strike_price") or opt.get("strike")
        option_type = opt.get("option_type") or opt.get("optionType") or opt.get("type")

        if isinstance(option_type, str):
            option_type = option_type.strip().upper()

        # Get price (prefer LTP, else midpoint of bid/ask)
        ltp = opt.get("ltp")
        bid = opt.get("bid")
        ask = opt.get("ask")
        price = None

        if ltp is not None:
            try:
                price = float(ltp)
            except (ValueError, TypeError):
                pass

        if price is None and bid is not None and ask is not None:
            try:
                price = (float(bid) + float(ask)) / 2.0
            except (ValueError, TypeError):
                pass

        # Parse expiry
        expiry_raw = opt.get("expiry") or opt.get("expiry_timestamp") or opt.get("expiryDate")
        expiry_epoch = parse_expiry_to_epoch(expiry_raw)
        T = time_to_expiry_years(expiry_epoch)

        # Compute IV
        iv = np.nan
        if price is not None and strike is not None and T > 0:
            iv = implied_volatility(
                price, float(spot_price), float(strike), T, risk_free_rate, option_type
            )

        # Compute Greeks
        greeks = compute_greeks(
            float(spot_price), float(strike), T, risk_free_rate, iv, option_type
        )

        results.append({
            "symbol": opt.get("symbol", ""),
            "strike": float(strike) if strike else None,
            "option_type": option_type,
            "expiry_epoch": expiry_epoch,
            "time_to_expiry_years": round(T, 6),
            "time_to_expiry_days": round(T * 365, 2),
            "spot": float(spot_price),
            "ltp": price,
            "iv": round(iv * 100, 2) if not np.isnan(iv) else None,  # Convert to percentage
            "delta": round(greeks["delta"], 4) if not np.isnan(greeks["delta"]) else None,
            "gamma": round(greeks["gamma"], 6) if not np.isnan(greeks["gamma"]) else None,
            "theta": round(greeks["theta"], 4) if not np.isnan(greeks["theta"]) else None,
            "vega": round(greeks["vega"], 4) if not np.isnan(greeks["vega"]) else None,
            "rho": round(greeks["rho"], 4) if not np.isnan(greeks["rho"]) else None,
            "oi": opt.get("oi"),
            "volume": opt.get("volume"),
            "bid": opt.get("bid"),
            "ask": opt.get("ask"),
        })

    # Sort by strike then option type
    results.sort(key=lambda x: (x.get("strike") or 0, x.get("option_type") or ""))

    return results
