export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: 'text' | 'chart' | 'alert' | 'execution';
  metadata?: any;
  timestamp: string;
}

export const HISTORY_DATA: Record<string, Message[]> = {
  'YESTERDAY': [
    {
      id: 'h1',
      role: 'system',
      content: 'SYSTEM LOG: DEC 28. SESSION STARTED.',
      type: 'text',
      timestamp: '09:00:00'
    },
    {
      id: 'h2',
      role: 'assistant',
      content: 'Morning Analysis: Market breadth is weak. NIFTY facing resistance at 19,600. Suggest focusing on defensive sectors like Pharma.',
      type: 'text',
      timestamp: '09:15:20'
    },
    {
      id: 'h3',
      role: 'user',
      content: 'Any shorts in Banking?',
      type: 'text',
      timestamp: '09:30:45'
    },
    {
      id: 'h4',
      role: 'assistant',
      content: 'Scanning BANKNIFTY components...\n\nOpportunity Identified: HDFCBANK\nShort below 1680. Target 1665.\nReason: Weak opening candles + High Put writing.',
      type: 'text',
      timestamp: '09:30:48'
    },
    {
      id: 'h5',
      role: 'user',
      content: 'Execute Short HDFCBANK.',
      type: 'text',
      timestamp: '09:32:10'
    },
    {
      id: 'h6',
      role: 'assistant',
      content: 'Order Executed: SELL HDFCBANK @ 1679.50. Stop Loss set at 1685.',
      type: 'execution',
      timestamp: '09:32:12'
    },
    {
      id: 'h7',
      role: 'system',
      content: 'ALERT: HDFCBANK TARGET HIT (1665). PROFIT BOOKED.',
      type: 'alert',
      timestamp: '10:45:00'
    },
    {
      id: 'h8',
      role: 'assistant',
      content: 'Session Summary: Net P&L +₹12,400. System shutting down for maintenance.',
      type: 'text',
      timestamp: '15:30:00'
    }
  ]
};

export const LIVE_MESSAGES_INIT: Message[] = [
    {
      id: 'init-1',
      role: 'system',
      content: 'SYSTEM INITIALIZED. CONNECTED TO NSE/BSE DATA STREAMS. LATENCY: 14ms.',
      type: 'text',
      timestamp: '09:14:58'
    },
    {
      id: '1',
      role: 'assistant',
      content: 'Hagrid AI Online. \n\nMarket Pre-open Analysis:\n- GLOBAL CUES: Negative (US Inflation Data)\n- SGX NIFTY: -45 pts\n- FII ACTIVITY: Net Sellers (₹-1,200cr)\n\nI recommend a cautious approach for the first 30 minutes.',
      type: 'text',
      timestamp: '09:15:02'
    },
    {
      id: '2',
      role: 'user',
      content: 'Show me the technicals for TATASTEEL. Is it a buy at current levels?',
      type: 'text',
      timestamp: '09:45:12'
    },
    {
      id: '3',
      role: 'assistant',
      content: 'Analyzing TATASTEEL (15m Timeframe)...\n\nCurrent Price: 118.50\n\n- RSI: 32 (Oversold)\n- MACD: Bearish Crossover\n- Support: 117.80\n- Resistance: 121.00\n\nVERDICT: WAIT. Price is approaching major support at 117.80. Look for reversal candles before entry.',
      type: 'chart',
      metadata: { symbol: 'TATASTEEL' },
      timestamp: '09:45:15'
    },
    {
      id: '4',
      role: 'user',
      content: 'Set an alert if NIFTY crosses 19,500.',
      type: 'text',
      timestamp: '10:12:30'
    },
    {
      id: '5',
      role: 'assistant',
      content: 'Alert Set: NIFTY 50 > 19,500. \nI will notify you immediately upon breach.',
      type: 'text',
      timestamp: '10:12:32'
    },
    {
      id: 'alert-1',
      role: 'system',
      content: 'ALERT TRIGGERED: VOLUME SPIKE DETECTED IN [ADANIENT] > 300% AVG.',
      type: 'alert',
      timestamp: '11:05:00'
    },
    {
      id: '6',
      role: 'user',
      content: 'Scan the market for high probability intraday setups. I need 10 stocks with at least 1% move potential. Use 5x leverage logic.',
      type: 'text',
      timestamp: '11:20:15'
    },
    {
      id: '7',
      role: 'assistant',
      content: 'Scanning NIFTY 500 universe... \n\nFound 10 opportunities matching criteria:\n- Min Volatility: >1.2%\n- Volume Spike: >200% avg\n- Sector Momentum: Aligned\n\nI have prepared the trade cards in the "AI PICKS" tab with specific Entry, Target (TP), and Stop Loss (SL) levels.\n\nSummary:\n1. RELIANCE (Long)\n2. ADANIENT (Short)\n3. TCS (Long)\n...and 7 others.\n\nGo to the AI PICKS tab to review and execute.',
      type: 'text',
      timestamp: '11:20:18'
    },
    {
      id: '8',
      role: 'user',
      content: 'Execute the RELIANCE trade. Market order.',
      type: 'text',
      timestamp: '11:22:45'
    },
    {
      id: '9',
      role: 'assistant',
      content: 'Order Placed Successfully.\n\nBUY RELIANCE\nQty: 100\nPrice: MKT (Avg. 2456.75)\nOrder ID: #ORD-998231\n\nPosition is now active. Monitoring P&L.',
      type: 'execution',
      timestamp: '11:22:48'
    }
];

export const STOCKS = [
  { symbol: 'RELIANCE', ltp: 2456.75, change: 12.50, pChange: 0.51 },
  { symbol: 'TCS', ltp: 3560.20, change: -24.30, pChange: -0.68 },
  { symbol: 'HDFCBANK', ltp: 1640.10, change: 8.90, pChange: 0.55 },
  { symbol: 'INFY', ltp: 1540.50, change: -5.25, pChange: -0.34 },
  { symbol: 'ICICIBANK', ltp: 945.60, change: 14.20, pChange: 1.52 },
  { symbol: 'SBIN', ltp: 580.30, change: 3.40, pChange: 0.59 },
  { symbol: 'BHARTIARTL', ltp: 890.00, change: -1.10, pChange: -0.12 },
  { symbol: 'ITC', ltp: 445.50, change: 2.30, pChange: 0.52 },
  { symbol: 'KOTAKBANK', ltp: 1820.40, change: -10.50, pChange: -0.57 },
  { symbol: 'LT', ltp: 2980.90, change: 45.60, pChange: 1.55 },
];

export const POSITIONS = [
  { symbol: 'TATAMOTORS', qty: 100, avg: 620.50, ltp: 635.00, type: 'CNC' },
  { symbol: 'ADANIENT', qty: 50, avg: 2450.00, ltp: 2420.00, type: 'MIS' },
  { symbol: 'WIPRO', qty: 200, avg: 410.00, ltp: 412.50, type: 'CNC' },
];

export interface StockPick {
  id: number;
  symbol: string;
  type: 'LONG' | 'SHORT';
  entry: number;
  target: number;
  stopLoss: number;
  leverage: string;
  potential: string;
  confidence: string;
  reason: string;
  status: 'OPEN' | 'HIT' | 'SL' | 'EXPIRED';
  pnl?: string;
}

export const LIVE_SUGGESTIONS: StockPick[] = [
  {
    id: 1,
    symbol: 'RELIANCE',
    type: 'LONG',
    entry: 2450.00,
    target: 2475.00,
    stopLoss: 2435.00,
    leverage: '5x',
    potential: '+5.10%',
    confidence: '92%',
    reason: 'Bullish flag breakout on 15m timeframe + Strong volume buying seen at support.',
    status: 'OPEN'
  },
  {
    id: 2,
    symbol: 'ADANIENT',
    type: 'SHORT',
    entry: 2420.00,
    target: 2395.00,
    stopLoss: 2435.00,
    leverage: '5x',
    potential: '+5.15%',
    confidence: '88%',
    reason: 'Double top formation rejection at 2430. RSA divergence indicates weakness.',
    status: 'OPEN'
  },
  {
    id: 3,
    symbol: 'TCS',
    type: 'LONG',
    entry: 3560.00,
    target: 3600.00,
    stopLoss: 3540.00,
    leverage: '5x',
    potential: '+5.60%',
    confidence: '85%',
    reason: 'IT Sector rotation. Moving average crossover (9/21 EMA) is bullish.',
    status: 'OPEN'
  },
  {
    id: 4,
    symbol: 'BAJFINANCE',
    type: 'SHORT',
    entry: 7100.00,
    target: 7020.00,
    stopLoss: 7140.00,
    leverage: '5x',
    potential: '+5.65%',
    confidence: '89%',
    reason: 'Faced resistance at 200 EMA. Heavy call writing at 7200 CE.',
    status: 'OPEN'
  },
  {
    id: 5,
    symbol: 'SBIN',
    type: 'LONG',
    entry: 580.00,
    target: 586.00,
    stopLoss: 576.00,
    leverage: '5x',
    potential: '+5.15%',
    confidence: '94%',
    reason: 'PSU Bank rally continuation. Breakout above previous day high.',
    status: 'OPEN'
  },
  {
    id: 6,
    symbol: 'INFY',
    type: 'LONG',
    entry: 1540.00,
    target: 1556.00,
    stopLoss: 1530.00,
    leverage: '5x',
    potential: '+5.20%',
    confidence: '81%',
    reason: 'Value buying emerging near 52-week support zone.',
    status: 'OPEN'
  },
  {
    id: 7,
    symbol: 'TATAMOTORS',
    type: 'SHORT',
    entry: 635.00,
    target: 628.00,
    stopLoss: 639.00,
    leverage: '5x',
    potential: '+5.50%',
    confidence: '86%',
    reason: 'Overbought on hourly charts. Stochastic RSI crossover downward.',
    status: 'OPEN'
  },
  {
    id: 8,
    symbol: 'ICICIBANK',
    type: 'LONG',
    entry: 945.00,
    target: 955.00,
    stopLoss: 939.00,
    leverage: '5x',
    potential: '+5.30%',
    confidence: '90%',
    reason: 'Strong quarterly results anticipation. Volume accumulation observed.',
    status: 'OPEN'
  },
  {
    id: 9,
    symbol: 'HINDALCO',
    type: 'SHORT',
    entry: 450.00,
    target: 445.00,
    stopLoss: 453.00,
    leverage: '5x',
    potential: '+5.55%',
    confidence: '83%',
    reason: 'Metal index weakness globally. Breakdown of rising wedge pattern.',
    status: 'OPEN'
  },
  {
    id: 10,
    symbol: 'AXISBANK',
    type: 'LONG',
    entry: 980.00,
    target: 990.00,
    stopLoss: 974.00,
    leverage: '5x',
    potential: '+5.10%',
    confidence: '87%',
    reason: 'Inverse Head & Shoulders pattern completion on 30m chart.',
    status: 'OPEN'
  }
];

export const HISTORY_SUGGESTIONS: Record<string, StockPick[]> = {
  'YESTERDAY': [
    {
      id: 101,
      symbol: 'HDFCBANK',
      type: 'SHORT',
      entry: 1680.00,
      target: 1665.00,
      stopLoss: 1688.00,
      leverage: '5x',
      potential: '+4.50%',
      confidence: '95%',
      reason: 'Gap down opening confirmed.',
      status: 'HIT',
      pnl: '+₹4,500'
    },
    {
      id: 102,
      symbol: 'TITAN',
      type: 'LONG',
      entry: 2950.00,
      target: 2980.00,
      stopLoss: 2935.00,
      leverage: '5x',
      potential: '+3.00%',
      confidence: '88%',
      reason: 'Wedding season demand surge.',
      status: 'SL',
      pnl: '-₹1,200'
    },
    {
      id: 103,
      symbol: 'SUNPHARMA',
      type: 'LONG',
      entry: 1120.00,
      target: 1135.00,
      stopLoss: 1112.00,
      leverage: '5x',
      potential: '+5.20%',
      confidence: '91%',
      reason: 'US FDA clearance news.',
      status: 'HIT',
      pnl: '+₹3,100'
    },
    {
      id: 104,
      symbol: 'MARUTI',
      type: 'SHORT',
      entry: 9800.00,
      target: 9700.00,
      stopLoss: 9850.00,
      leverage: '5x',
      potential: '+4.00%',
      confidence: '82%',
      reason: 'Weak monthly sales data.',
      status: 'HIT',
      pnl: '+₹6,200'
    }
  ]
};

export const CHART_DATA = [
  { time: '10:00', price: 2450 },
  { time: '10:30', price: 2455 },
  { time: '11:00', price: 2448 },
  { time: '11:30', price: 2460 },
  { time: '12:00', price: 2465 },
  { time: '12:30', price: 2462 },
  { time: '13:00', price: 2470 },
  { time: '13:30', price: 2475 },
  { time: '14:00', price: 2480 },
  { time: '14:30', price: 2478 },
  { time: '15:00', price: 2485 },
  { time: '15:30', price: 2490 },
];