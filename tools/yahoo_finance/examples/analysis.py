"""Examples for fetching analyst recommendations and estimates from Yahoo Finance.

This script demonstrates how to:
- Fetch analyst recommendations
- Get price targets
- View upgrades/downgrades history
- Access earnings and revenue estimates
- Analyze EPS trends
- Get growth estimates
"""

from tools.yahoo_finance import YFinanceClient


def fetch_recommendations(symbol: str = "AAPL"):
    """Fetch analyst recommendations for a ticker."""
    print("=" * 60)
    print(f"Analyst Recommendations for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    print(f"\nSymbol: {analysis.symbol}")

    # Recommendations summary
    print("\n--- Recommendations Summary ---")
    if analysis.recommendations_summary:
        for r in analysis.recommendations_summary:
            period = r.get('period', 'N/A')
            strong_buy = r.get('strongBuy', 0)
            buy = r.get('buy', 0)
            hold = r.get('hold', 0)
            sell = r.get('sell', 0)
            strong_sell = r.get('strongSell', 0)

            print(f"\n  Period: {period}")
            print(f"    Strong Buy: {strong_buy}")
            print(f"    Buy: {buy}")
            print(f"    Hold: {hold}")
            print(f"    Sell: {sell}")
            print(f"    Strong Sell: {strong_sell}")

            total = strong_buy + buy + hold + sell + strong_sell
            if total > 0:
                bullish = ((strong_buy + buy) / total) * 100
                print(f"    Bullish %: {bullish:.1f}%")
    else:
        print("  No recommendations summary available")


def fetch_price_targets(symbol: str = "MSFT"):
    """Fetch analyst price targets."""
    print("\n" + "=" * 60)
    print(f"Analyst Price Targets for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    # Also get current price for comparison
    info = client.get_ticker_info(symbol)
    current_price = info.info.get('currentPrice', 0)

    print(f"\nCurrent Price: ${current_price:.2f}" if current_price else "\nCurrent Price: N/A")

    targets = analysis.analyst_price_targets
    if targets:
        print("\n--- Price Targets ---")
        mean_target = targets.get('mean', targets.get('current', 0))
        high_target = targets.get('high', 0)
        low_target = targets.get('low', 0)
        num_analysts = targets.get('numberOfAnalysts', targets.get('numberOfAnalystOpinions', 'N/A'))

        print(f"  Target Mean: ${mean_target:.2f}" if mean_target else "  Target Mean: N/A")
        print(f"  Target High: ${high_target:.2f}" if high_target else "  Target High: N/A")
        print(f"  Target Low: ${low_target:.2f}" if low_target else "  Target Low: N/A")
        print(f"  Number of Analysts: {num_analysts}")

        if current_price and mean_target:
            upside = ((mean_target - current_price) / current_price) * 100
            print(f"\n  Implied Upside to Mean: {upside:+.1f}%")
            if high_target:
                upside_high = ((high_target - current_price) / current_price) * 100
                print(f"  Implied Upside to High: {upside_high:+.1f}%")
            if low_target:
                downside_low = ((low_target - current_price) / current_price) * 100
                print(f"  Implied Move to Low: {downside_low:+.1f}%")
    else:
        print("\n  No price target data available")


def fetch_upgrades_downgrades(symbol: str = "GOOGL"):
    """Fetch recent upgrades and downgrades."""
    print("\n" + "=" * 60)
    print(f"Recent Upgrades/Downgrades for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.upgrades_downgrades:
        print("\n  No upgrades/downgrades data available")
        return

    print("\n--- Recent Rating Changes ---")
    print(f"| {'Date':<12} | {'Firm':<25} | {'From':<12} | {'To':<12} | {'Action':<12} |")
    print("|" + "-" * 14 + "|" + "-" * 27 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 14 + "|")

    for ud in analysis.upgrades_downgrades[:20]:  # Last 20
        # Handle different date formats
        grade_date = ud.get('GradeDate', ud.get('index', 'N/A'))
        if hasattr(grade_date, 'strftime'):
            date_str = grade_date.strftime('%Y-%m-%d')
        else:
            date_str = str(grade_date)[:12]

        firm = str(ud.get('Firm', 'N/A'))[:25]
        from_grade = str(ud.get('FromGrade', 'N/A'))[:12]
        to_grade = str(ud.get('ToGrade', 'N/A'))[:12]
        action = str(ud.get('Action', 'N/A'))[:12]

        print(f"| {date_str:<12} | {firm:<25} | {from_grade:<12} | {to_grade:<12} | {action:<12} |")


def fetch_earnings_estimates(symbol: str = "AMZN"):
    """Fetch earnings estimates."""
    print("\n" + "=" * 60)
    print(f"Earnings Estimates for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.earnings_estimate:
        print("\n  No earnings estimates available")
        return

    print("\n--- Earnings Estimates ---")

    # earnings_estimate is typically transposed with periods as rows
    for est in analysis.earnings_estimate:
        period = est.get('Date', est.get('index', 'N/A'))
        avg = est.get('avg', est.get('Avg. Estimate', 'N/A'))
        low = est.get('low', est.get('Low Estimate', 'N/A'))
        high = est.get('high', est.get('High Estimate', 'N/A'))
        num_analysts = est.get('numberOfAnalysts', est.get('No. of Analysts', 'N/A'))
        growth = est.get('growth', est.get('Year Ago EPS', 'N/A'))

        print(f"\n  Period: {period}")
        print(f"    Avg Estimate: ${avg:.2f}" if isinstance(avg, (int, float)) else f"    Avg Estimate: {avg}")
        print(f"    Low Estimate: ${low:.2f}" if isinstance(low, (int, float)) else f"    Low Estimate: {low}")
        print(f"    High Estimate: ${high:.2f}" if isinstance(high, (int, float)) else f"    High Estimate: {high}")
        print(f"    Number of Analysts: {num_analysts}")


def fetch_revenue_estimates(symbol: str = "NVDA"):
    """Fetch revenue estimates."""
    print("\n" + "=" * 60)
    print(f"Revenue Estimates for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.revenue_estimate:
        print("\n  No revenue estimates available")
        return

    print("\n--- Revenue Estimates ---")

    for est in analysis.revenue_estimate:
        period = est.get('Date', est.get('index', 'N/A'))
        avg = est.get('avg', est.get('Avg. Estimate', 0))
        low = est.get('low', est.get('Low Estimate', 0))
        high = est.get('high', est.get('High Estimate', 0))
        num_analysts = est.get('numberOfAnalysts', est.get('No. of Analysts', 'N/A'))

        def fmt_rev(v):
            if v is None or (isinstance(v, float) and v != v):
                return "N/A"
            try:
                v = float(v)
                if v >= 1e12:
                    return f"${v/1e12:.2f}T"
                elif v >= 1e9:
                    return f"${v/1e9:.2f}B"
                elif v >= 1e6:
                    return f"${v/1e6:.2f}M"
                else:
                    return f"${v:,.0f}"
            except:
                return "N/A"

        print(f"\n  Period: {period}")
        print(f"    Avg Estimate: {fmt_rev(avg)}")
        print(f"    Low Estimate: {fmt_rev(low)}")
        print(f"    High Estimate: {fmt_rev(high)}")
        print(f"    Number of Analysts: {num_analysts}")


def fetch_earnings_history(symbol: str = "META"):
    """Fetch earnings history (actual vs estimate)."""
    print("\n" + "=" * 60)
    print(f"Earnings History for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.earnings_history:
        print("\n  No earnings history available")
        return

    print("\n--- Earnings History (Actual vs Estimate) ---")
    print(f"| {'Quarter':<12} | {'Estimate':>10} | {'Actual':>10} | {'Surprise':>10} | {'Surprise %':>12} |")
    print("|" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 14 + "|")

    for eh in analysis.earnings_history:
        quarter = eh.get('index', eh.get('Quarter', 'N/A'))
        if hasattr(quarter, 'strftime'):
            quarter_str = quarter.strftime('%Y-%m-%d')
        else:
            quarter_str = str(quarter)[:12]

        estimate = eh.get('epsEstimate', eh.get('EPS Estimate', 0))
        actual = eh.get('epsActual', eh.get('EPS Actual', 0))
        diff = eh.get('epsDifference', eh.get('Difference', 0))
        surprise_pct = eh.get('surprisePercent', eh.get('Surprise %', 0))

        est_str = f"${estimate:.2f}" if isinstance(estimate, (int, float)) else "N/A"
        act_str = f"${actual:.2f}" if isinstance(actual, (int, float)) else "N/A"
        diff_str = f"${diff:+.2f}" if isinstance(diff, (int, float)) else "N/A"
        surp_str = f"{surprise_pct*100:+.1f}%" if isinstance(surprise_pct, (int, float)) and surprise_pct < 10 else f"{surprise_pct:+.1f}%" if isinstance(surprise_pct, (int, float)) else "N/A"

        print(f"| {quarter_str:<12} | {est_str:>10} | {act_str:>10} | {diff_str:>10} | {surp_str:>12} |")


def fetch_eps_trend(symbol: str = "TSLA"):
    """Fetch EPS trend data."""
    print("\n" + "=" * 60)
    print(f"EPS Trend for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.eps_trend:
        print("\n  No EPS trend data available")
        return

    print("\n--- EPS Trend ---")

    for trend in analysis.eps_trend:
        period = trend.get('Date', trend.get('index', 'N/A'))
        current = trend.get('current', trend.get('Current Estimate', 'N/A'))
        d7_ago = trend.get('7daysAgo', trend.get('7 Days Ago', 'N/A'))
        d30_ago = trend.get('30daysAgo', trend.get('30 Days Ago', 'N/A'))
        d60_ago = trend.get('60daysAgo', trend.get('60 Days Ago', 'N/A'))
        d90_ago = trend.get('90daysAgo', trend.get('90 Days Ago', 'N/A'))

        print(f"\n  Period: {period}")
        print(f"    Current Estimate: {current}")
        print(f"    7 Days Ago: {d7_ago}")
        print(f"    30 Days Ago: {d30_ago}")
        print(f"    60 Days Ago: {d60_ago}")
        print(f"    90 Days Ago: {d90_ago}")


def fetch_growth_estimates(symbol: str = "AMD"):
    """Fetch growth estimates."""
    print("\n" + "=" * 60)
    print(f"Growth Estimates for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.growth_estimates:
        print("\n  No growth estimates available")
        return

    print("\n--- Growth Estimates ---")

    for est in analysis.growth_estimates:
        metric = est.get('Date', est.get('index', 'N/A'))
        stock_val = est.get(symbol, est.get('Stock', 'N/A'))
        industry_val = est.get('industry', est.get('Industry', 'N/A'))
        sector_val = est.get('sector', est.get('Sector', 'N/A'))
        sp500_val = est.get('index', est.get('S&P 500', 'N/A'))

        def fmt_pct(v):
            if v is None or (isinstance(v, float) and v != v):
                return "N/A"
            try:
                return f"{float(v)*100:.1f}%" if float(v) < 10 else f"{float(v):.1f}%"
            except:
                return str(v)

        print(f"\n  {metric}:")
        print(f"    {symbol}: {fmt_pct(stock_val)}")
        print(f"    Industry: {fmt_pct(industry_val)}")
        print(f"    Sector: {fmt_pct(sector_val)}")
        print(f"    S&P 500: {fmt_pct(sp500_val)}")


def compare_analyst_sentiment():
    """Compare analyst sentiment across stocks."""
    print("\n" + "=" * 60)
    print("Analyst Sentiment Comparison")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]
    client = YFinanceClient()

    print("\n| Symbol | Strong Buy | Buy | Hold | Sell | Target | Upside |")
    print("|--------|------------|-----|------|------|--------|--------|")

    for symbol in symbols:
        try:
            analysis = client.get_analysis(symbol)
            info = client.get_ticker_info(symbol)

            current_price = info.info.get('currentPrice', 0)

            # Get latest recommendation summary
            strong_buy = buy = hold = sell = 0
            if analysis.recommendations_summary:
                latest = analysis.recommendations_summary[0]
                strong_buy = latest.get('strongBuy', 0)
                buy = latest.get('buy', 0)
                hold = latest.get('hold', 0)
                sell = latest.get('sell', 0) + latest.get('strongSell', 0)

            # Get target
            target = 0
            if analysis.analyst_price_targets:
                target = analysis.analyst_price_targets.get('mean', 0)

            upside = ((target - current_price) / current_price * 100) if current_price and target else 0

            target_str = f"${target:.0f}" if target else "N/A"
            upside_str = f"{upside:+.1f}%" if upside else "N/A"

            print(f"| {symbol:<6} | {strong_buy:>10} | {buy:>3} | {hold:>4} | {sell:>4} | {target_str:>6} | {upside_str:>6} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:30]} |")


def fetch_recent_recommendations(symbol: str = "AAPL"):
    """Fetch recent analyst recommendations."""
    print("\n" + "=" * 60)
    print(f"Recent Analyst Recommendations for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    analysis = client.get_analysis(symbol)

    if not analysis.recommendations:
        print("\n  No recent recommendations available")
        return

    print("\n--- Recent Recommendations ---")
    print(f"| {'Date':<12} | {'Firm':<25} | {'To Grade':<15} | {'Action':<12} |")
    print("|" + "-" * 14 + "|" + "-" * 27 + "|" + "-" * 17 + "|" + "-" * 14 + "|")

    for rec in analysis.recommendations[:15]:
        # Handle date
        rec_date = rec.get('index', rec.get('Date', 'N/A'))
        if hasattr(rec_date, 'strftime'):
            date_str = rec_date.strftime('%Y-%m-%d')
        else:
            date_str = str(rec_date)[:12]

        firm = str(rec.get('Firm', 'N/A'))[:25]
        to_grade = str(rec.get('To Grade', rec.get('toGrade', 'N/A')))[:15]
        action = str(rec.get('Action', 'N/A'))[:12]

        print(f"| {date_str:<12} | {firm:<25} | {to_grade:<15} | {action:<12} |")


def fetch_calendar_events(symbol: str = "MSFT"):
    """Fetch calendar events (earnings dates, etc.)."""
    print("\n" + "=" * 60)
    print(f"Calendar Events for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    calendar = client.get_calendar(symbol)

    print(f"\nSymbol: {calendar.symbol}")

    # Calendar info
    if calendar.calendar:
        print("\n--- Calendar ---")
        for key, value in calendar.calendar.items():
            print(f"  {key}: {value}")
    else:
        print("\n--- Calendar ---")
        print("  No calendar data available")

    # Earnings dates
    print("\n--- Upcoming/Recent Earnings Dates ---")
    if calendar.earnings_dates:
        for ed in calendar.earnings_dates[:10]:
            date = ed.get('index', ed.get('Earnings Date', 'N/A'))
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d %H:%M')
            else:
                date_str = str(date)

            eps_est = ed.get('EPS Estimate', ed.get('epsEstimate', 'N/A'))
            eps_act = ed.get('Reported EPS', ed.get('epsActual', 'N/A'))
            surprise = ed.get('Surprise(%)', ed.get('surprisePercent', 'N/A'))

            print(f"  {date_str}")
            print(f"    EPS Estimate: {eps_est}")
            print(f"    Reported EPS: {eps_act}")
            print(f"    Surprise: {surprise}")
            print()
    else:
        print("  No earnings dates available")


if __name__ == "__main__":
    # Run all examples
    fetch_recommendations("AAPL")
    fetch_price_targets("MSFT")
    fetch_upgrades_downgrades("GOOGL")
    fetch_earnings_estimates("AMZN")
    fetch_revenue_estimates("NVDA")
    fetch_earnings_history("META")
    fetch_eps_trend("TSLA")
    fetch_growth_estimates("AMD")
    compare_analyst_sentiment()
    fetch_recent_recommendations("AAPL")
    fetch_calendar_events("MSFT")
