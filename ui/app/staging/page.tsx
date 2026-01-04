'use client';

import React from 'react';
import { Target, ShieldAlert, Zap, CheckCircle, ArrowRight, History, Lock, TrendingUp, AlertOctagon } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { DateNavigator } from '@/components/shared/date-navigator';
import { LIVE_SUGGESTIONS, HISTORY_SUGGESTIONS } from '@/data/mock-data';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { format, subDays, parseISO, isSameDay } from 'date-fns';

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
	hidden: { opacity: 0, y: 20 },
	show: { opacity: 1, y: 0 }
};

export default function StagingPage() {
	const { selectedDate } = useAppStore();

	const today = new Date();
	const selectedDateObj = parseISO(selectedDate);
	const isToday = isSameDay(selectedDateObj, today);
	const yesterday = subDays(today, 1);
	const isYesterday = isSameDay(selectedDateObj, yesterday);

	const displayPicks = isToday
		? LIVE_SUGGESTIONS
		: (isYesterday ? HISTORY_SUGGESTIONS['YESTERDAY'] : []);

	const isHistorical = !isToday;

	return (
		<div className="h-full flex flex-col font-mono text-foreground bg-background">
			<div className="border-b border-border p-4 flex justify-between items-center bg-card shadow-sm z-10">
				<div className="flex items-center gap-3">
					<div className="p-2 bg-chart-3/10 rounded-md border border-chart-3/20">
						<Zap className="text-chart-3" size={18} />
					</div>
					<div>
						<h2 className="font-bold uppercase tracking-widest text-foreground text-sm">
							{isHistorical ? 'Historical Trade Log' : 'AI Trade Staging'}
						</h2>
						<div className="text-[10px] text-muted-foreground">
							Strategy: <span className="text-primary">High Volatility Intraday</span>
						</div>
					</div>
				</div>
				<div className="flex items-center gap-4 text-xs">
					<div className="flex items-center gap-2 text-muted-foreground bg-background px-3 py-1.5 rounded-full border border-border">
						<ShieldAlert size={14} className="text-primary" />
						<span>LEVERAGE: <span className="text-foreground font-bold">5X</span></span>
					</div>
					<div className="flex items-center gap-2 text-muted-foreground bg-background px-3 py-1.5 rounded-full border border-border">
						<Target size={14} className="text-chart-2" />
						<span>MIN TARGET: <span className="text-foreground font-bold">1.5%</span></span>
					</div>
				</div>
			</div>

			{/* Date Navigation */}
			<DateNavigator />

			<div className="flex-1 overflow-auto p-6 scrollbar-hide bg-background/50">
				<AnimatePresence mode="wait">
					{displayPicks.length > 0 ? (
						<motion.div
							key={selectedDate} // Trigger animation on date change
							variants={container}
							initial="hidden"
							animate="show"
							className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 gap-4 max-w-7xl mx-auto"
						>
							{displayPicks.map((stock) => (
								<motion.div
									key={stock.id}
									variants={item}
									whileHover={{ y: -2, boxShadow: '0 10px 30px -10px rgba(0,0,0,0.3)' }}
									className={cn(
										"border p-0 transition-all duration-300 group flex flex-col relative overflow-hidden rounded-xl bg-card",
										stock.status === 'HIT' ? "border-chart-2/50" :
											stock.status === 'SL' ? "border-destructive/50" :
												"border-border hover:border-primary/50"
									)}
								>
									{/* Status Overlay Badge for History */}
									{isHistorical && (
										<div className={cn(
											"absolute top-0 right-0 px-4 py-1 text-[10px] font-bold uppercase tracking-wider z-20 rounded-bl-xl",
											stock.status === 'HIT' ? "bg-chart-2 text-background" : "bg-destructive text-foreground"
										)}>
											{stock.status === 'HIT' ? 'TARGET MET' : 'STOP LOSS HIT'}
										</div>
									)}

									{/* Top Section */}
									<div className="p-5 border-b border-border/50 relative">
										{/* Background Glow */}
										<div className={cn(
											"absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-20 pointer-events-none",
											stock.type === 'LONG' ? "bg-chart-2" : "bg-destructive"
										)} />

										<div className="flex justify-between items-start mb-4">
											<div className="flex items-center gap-3">
												<div className={cn(
													"w-10 h-10 rounded-lg flex items-center justify-center border",
													stock.type === 'LONG' ? "bg-chart-2/10 border-chart-2/20 text-chart-2" : "bg-destructive/10 border-destructive/20 text-destructive"
												)}>
													{stock.type === 'LONG' ? <TrendingUp size={20} /> : <TrendingUp size={20} className="rotate-180" />}
												</div>
												<div>
													<h3 className="text-lg font-bold text-foreground leading-none mb-1">{stock.symbol}</h3>
													<span className={cn(
														"text-[10px] font-bold px-1.5 py-0.5 rounded border inline-block",
														stock.type === 'LONG' ? "border-chart-2/30 text-chart-2" : "border-destructive/30 text-destructive"
													)}>
														{stock.type}
													</span>
												</div>
											</div>
											<div className="text-right z-10">
												{isHistorical && stock.pnl ? (
													<div className={cn(
														"text-xl font-bold",
														stock.status === 'HIT' ? "text-chart-2" : "text-destructive"
													)}>
														{stock.pnl}
													</div>
												) : (
													<div className="text-xl font-bold text-chart-2">
														{stock.potential}
													</div>
												)}
												<div className="text-[10px] text-muted-foreground uppercase font-medium">{isHistorical ? 'Realized PnL' : 'Proj. Return'}</div>
											</div>
										</div>

										<div className="flex items-center justify-between text-xs text-muted-foreground bg-background/50 rounded-lg p-2 border border-border/50">
											<span>AI Confidence Score:</span>
											<div className="flex items-center gap-2">
												<div className="w-16 h-1.5 bg-border rounded-full overflow-hidden">
													<div
														className="h-full bg-primary"
														style={{ width: stock.confidence }}
													/>
												</div>
												<span className="text-primary font-bold">{stock.confidence}</span>
											</div>
										</div>
									</div>

									{/* Data Grid */}
									<div className="grid grid-cols-3 divide-x divide-border/50 border-b border-border/50 bg-background/30 text-sm">
										<div className="p-3 text-center">
											<div className="text-[10px] text-muted-foreground uppercase mb-1 font-bold tracking-wider">Entry</div>
											<div className="font-bold text-foreground">{stock.entry.toFixed(2)}</div>
										</div>
										<div className="p-3 text-center">
											<div className="text-[10px] text-muted-foreground uppercase mb-1 font-bold tracking-wider">Target</div>
											<div className="font-bold text-chart-2">{stock.target.toFixed(2)}</div>
										</div>
										<div className="p-3 text-center">
											<div className="text-[10px] text-muted-foreground uppercase mb-1 font-bold tracking-wider">Stop Loss</div>
											<div className="font-bold text-destructive">{stock.stopLoss.toFixed(2)}</div>
										</div>
									</div>

									{/* Reasoning */}
									<div className="p-4 flex-1 bg-card">
										<div className="flex gap-3 items-start text-xs text-muted-foreground">
											<AlertOctagon size={16} className="text-chart-3 shrink-0 mt-0.5" />
											<p className="leading-relaxed">
												<span className="font-bold text-chart-3 block mb-1">AI Analysis:</span>
												{stock.reason}
											</p>
										</div>
									</div>

									{/* Action */}
									<button
										disabled={isHistorical}
										className={cn(
											"w-full py-4 border-t transition-all uppercase text-xs font-bold flex items-center justify-center gap-2",
											isHistorical
												? "bg-background border-border text-muted-foreground cursor-not-allowed"
												: "bg-background border-border text-foreground hover:bg-chart-2 hover:text-background hover:border-chart-2 group-hover:bg-primary group-hover:text-background group-hover:border-primary"
										)}
									>
										{isHistorical ? <Lock size={14} /> : <CheckCircle size={14} />}
										{isHistorical ? 'Trade Closed' : 'Execute Order Now'}
									</button>
								</motion.div>
							))}
						</motion.div>
					) : (
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							className="h-full flex flex-col items-center justify-center text-muted-foreground gap-4 py-20"
						>
							<History size={48} className="opacity-20" />
							<div className="text-center">
								<p className="font-bold uppercase tracking-widest text-lg text-muted-foreground/50">No Logs Found</p>
								<p className="text-xs mt-2 text-muted-foreground/40">No trade suggestions were recorded for this date.</p>
							</div>
						</motion.div>
					)}
				</AnimatePresence>

				{!isHistorical && (
					<div className="mt-8 border-t border-border pt-6 flex justify-end max-w-7xl mx-auto">
						<motion.button
							whileHover={{ scale: 1.05 }}
							whileTap={{ scale: 0.95 }}
							className="bg-primary text-background font-bold uppercase text-sm px-8 py-4 rounded-lg flex items-center gap-3 transition-shadow shadow-lg hover:shadow-primary/20"
						>
							Execute All Picks <ArrowRight size={16} />
						</motion.button>
					</div>
				)}
			</div>
		</div>
	);
}