'use client';

import React from 'react';
import { TrendingUp, TrendingDown, ArrowUp, ArrowDown } from 'lucide-react';
import { motion } from 'motion/react';
import { STOCKS } from '@/data/mock-data';
import { cn } from '@/lib/utils';

const container = {
	hidden: { opacity: 0 },
	show: {
		opacity: 1,
		transition: {
			staggerChildren: 0.05
		}
	}
};

const item = {
	hidden: { opacity: 0, x: -10 },
	show: { opacity: 1, x: 0 }
};

export default function MarketWatchPage() {
	return (
		<div className="h-full flex flex-col font-mono text-sm bg-background text-foreground">
			<div className="border-b border-border p-4 flex justify-between items-center bg-card shadow-sm">
				<div className="flex items-center gap-2">
					<h2 className="font-bold uppercase tracking-widest text-foreground">Market Watch</h2>
					<span className="text-[10px] text-muted-foreground px-1.5 py-0.5 border border-border rounded">LIVE FEED</span>
				</div>
				<div className="flex gap-6 text-xs font-medium">
					<motion.div
						animate={{ color: ['var(--chart-2)', 'var(--primary)', 'var(--chart-2)'] }}
						transition={{ duration: 3, repeat: Infinity }}
						className="flex items-center gap-1"
					>
						<span>NIFTY</span>
						<span className="text-chart-2">19,450.00</span>
						<span className="text-[10px] text-chart-2 bg-chart-2/10 px-1 rounded">(+0.45%)</span>
					</motion.div>
					<motion.div
						animate={{ color: ['var(--destructive)', '#fb4934', 'var(--destructive)'] }}
						transition={{ duration: 3, repeat: Infinity }}
						className="flex items-center gap-1"
					>
						<span>SENSEX</span>
						<span className="text-destructive">65,340.00</span>
						<span className="text-[10px] text-destructive bg-destructive/10 px-1 rounded">(-0.12%)</span>
					</motion.div>
				</div>
			</div>

			<div className="flex-1 overflow-auto scrollbar-hide bg-background/50">
				<table className="w-full text-left border-collapse">
					<thead className="bg-card/50 backdrop-blur-sm text-xs uppercase sticky top-0 text-muted-foreground z-10 border-b border-border">
						<tr>
							<th className="p-4 font-semibold tracking-wider w-1/4">Symbol</th>
							<th className="p-4 font-semibold text-right tracking-wider">Price</th>
							<th className="p-4 font-semibold text-right tracking-wider">Change</th>
							<th className="p-4 font-semibold text-right tracking-wider">% Change</th>
						</tr>
					</thead>
					<motion.tbody
						variants={container}
						initial="hidden"
						animate="show"
					>
						{STOCKS.map((stock, i) => (
							<motion.tr
								key={stock.symbol}
								variants={item}
								whileHover={{ backgroundColor: 'var(--sidebar-accent)' }}
								className={cn(
									"border-b border-border/50 cursor-pointer group transition-colors",
									i % 2 === 0 ? "bg-transparent" : "bg-card/20"
								)}
							>
								<td className="p-4 font-bold group-hover:text-primary text-foreground transition-colors flex items-center gap-2">
									{stock.symbol}
								</td>
								<td className="p-4 text-right text-foreground font-mono">{stock.ltp.toFixed(2)}</td>
								<td className={cn(
									"p-4 text-right font-mono",
									stock.change >= 0 ? 'text-chart-2' : 'text-destructive'
								)}>
									{stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)}
								</td>
								<td className={cn(
									"p-4 text-right font-mono flex items-center justify-end gap-2",
									stock.pChange >= 0 ? 'text-chart-2' : 'text-destructive'
								)}>
									{stock.pChange > 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
									{Math.abs(stock.pChange).toFixed(2)}%
								</td>
							</motion.tr>
						))}
					</motion.tbody>
				</table>
			</div>

			<div className="p-2 border-t border-border text-xs text-muted-foreground uppercase flex justify-between bg-card items-center">
				<div className="flex items-center gap-2">
					<span>Connection:</span>
					<span className="text-chart-2 font-bold">Stable (14ms)</span>
				</div>
				<div className="flex items-center gap-2">
					<motion.span
						animate={{ opacity: [1, 0.2, 1] }}
						transition={{ duration: 1.5, repeat: Infinity }}
						className="w-2 h-2 bg-chart-2 rounded-full shadow-[0_0_8px_var(--chart-2)]"
					/>
					<span className="text-chart-2 font-bold tracking-wider">LIVE MARKET DATA</span>
				</div>
			</div>
		</div>
	);
}