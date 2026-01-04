'use client';

import React from 'react';
import { motion } from 'motion/react';
import { POSITIONS } from '@/data/mock-data';
import { cn } from '@/lib/utils';
import { Briefcase, TrendingUp, TrendingDown } from 'lucide-react';

const container = {
	hidden: { opacity: 0 },
	show: {
		opacity: 1,
		transition: {
			staggerChildren: 0.1
		}
	}
};

const item = {
	hidden: { opacity: 0, x: -10 },
	show: { opacity: 1, x: 0 }
};

export default function PositionsPage() {
	const totalPnL = POSITIONS.reduce((acc, pos) => acc + (pos.ltp - pos.avg) * pos.qty, 0);

	return (
		<div className="h-full flex flex-col font-mono text-sm bg-background text-foreground">
			<div className="border-b border-border p-6 flex justify-between items-center bg-card shadow-sm">
				<div className="flex items-center gap-3">
					<div className="p-2 bg-primary/10 rounded-md">
						<Briefcase className="text-primary" size={20} />
					</div>
					<div>
						<h2 className="font-bold uppercase tracking-widest text-foreground text-lg">Portfolio</h2>
						<div className="text-xs text-muted-foreground mt-0.5">3 Open Positions</div>
					</div>
				</div>

				<motion.div
					key={totalPnL}
					initial={{ scale: 0.9, opacity: 0 }}
					animate={{ scale: 1, opacity: 1 }}
					className={cn(
						"text-right px-4 py-2 rounded-md border",
						totalPnL >= 0 ? "bg-chart-2/5 border-chart-2/20" : "bg-destructive/5 border-destructive/20"
					)}
				>
					<div className="text-xs uppercase text-muted-foreground mb-1">Total P&L</div>
					<div className={cn(
						"text-2xl font-bold font-mono flex items-center gap-2",
						totalPnL >= 0 ? 'text-chart-2' : 'text-destructive'
					)}>
						{totalPnL >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
						₹ {Math.abs(totalPnL).toFixed(2)}
					</div>
				</motion.div>
			</div>

			<div className="flex-1 overflow-auto scrollbar-hide p-6">
				<div className="rounded-lg border border-border overflow-hidden bg-card/30">
					<table className="w-full text-left border-collapse">
						<thead className="bg-card text-xs uppercase text-muted-foreground border-b border-border">
							<tr>
								<th className="p-4 font-semibold tracking-wider">Instrument</th>
								<th className="p-4 font-semibold tracking-wider text-center">Type</th>
								<th className="p-4 font-semibold tracking-wider text-right">Qty</th>
								<th className="p-4 font-semibold tracking-wider text-right">Avg Price</th>
								<th className="p-4 font-semibold tracking-wider text-right">LTP</th>
								<th className="p-4 font-semibold tracking-wider text-right">P&L</th>
							</tr>
						</thead>
						<motion.tbody
							variants={container}
							initial="hidden"
							animate="show"
						>
							{POSITIONS.map((pos) => {
								const pnl = (pos.ltp - pos.avg) * pos.qty;
								const pnlPercent = ((pos.ltp - pos.avg) / pos.avg) * 100;

								return (
									<motion.tr
										key={pos.symbol}
										variants={item}
										whileHover={{ backgroundColor: 'var(--sidebar-accent)' }}
										className="border-b border-border/50 transition-colors cursor-pointer group last:border-0"
									>
										<td className="p-4 font-bold text-foreground group-hover:text-primary transition-colors">
											{pos.symbol}
										</td>
										<td className="p-4 text-center">
											<span className={cn(
												"text-[10px] font-bold px-2 py-1 rounded border",
												pos.type === 'CNC' ? "border-chart-4 text-chart-4 bg-chart-4/10" : "border-chart-3 text-chart-3 bg-chart-3/10"
											)}>
												{pos.type}
											</span>
										</td>
										<td className="p-4 text-right text-foreground font-mono">{pos.qty}</td>
										<td className="p-4 text-right text-muted-foreground font-mono">{pos.avg.toFixed(2)}</td>
										<td className="p-4 text-right text-foreground font-mono">{pos.ltp.toFixed(2)}</td>
										<td className="p-4 text-right">
											<div className={cn(
												"font-mono font-bold",
												pnl >= 0 ? 'text-chart-2' : 'text-destructive'
											)}>
												{pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
											</div>
											<div className={cn(
												"text-[10px]",
												pnl >= 0 ? 'text-chart-2/70' : 'text-destructive/70'
											)}>
												({pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)
											</div>
										</td>
									</motion.tr>
								);
							})}
						</motion.tbody>
					</table>
				</div>
			</div>
		</div>
	);
}