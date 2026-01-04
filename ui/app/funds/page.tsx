'use client';

import React from 'react';
import { ArrowUpRight, ArrowDownLeft, Wallet, CreditCard, Landmark, History } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';

export default function FundsPage() {
	return (
		<div className="h-full flex flex-col font-mono text-sm bg-background text-foreground overflow-y-auto">
			<div className="max-w-4xl mx-auto w-full p-8 space-y-8">

				{/* Header Section */}
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-2xl font-bold tracking-tight text-foreground">Funds & Margin</h1>
						<p className="text-muted-foreground mt-1">Manage your trading account balance and transactions.</p>
					</div>
					<div className="p-3 bg-primary/10 rounded-full border border-primary/20">
						<Wallet className="text-primary h-6 w-6" />
					</div>
				</div>

				{/* Balance Card */}
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.4 }}
					className="grid grid-cols-1 md:grid-cols-3 gap-6"
				>
					<div className="md:col-span-2 bg-gradient-to-br from-card to-card/50 border border-border p-8 rounded-xl relative overflow-hidden shadow-lg">
						<div className="absolute top-0 right-0 p-32 bg-primary/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

						<div className="relative z-10">
							<div className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
								<span className="w-2 h-2 bg-chart-2 rounded-full animate-pulse"></span>
								Available Margin
							</div>
							<motion.div
								initial={{ scale: 0.9, opacity: 0 }}
								animate={{ scale: 1, opacity: 1 }}
								transition={{ delay: 0.2, type: "spring" }}
								className="text-5xl font-bold text-foreground mb-8 tracking-tight"
							>
								₹ 1,24,500<span className="text-2xl text-muted-foreground">.00</span>
							</motion.div>

							<div className="grid grid-cols-2 gap-8 border-t border-border pt-6">
								<div>
									<div className="text-xs uppercase text-muted-foreground mb-1">Used Margin</div>
									<div className="text-xl font-medium text-foreground">₹ 45,230.50</div>
								</div>
								<div>
									<div className="text-xs uppercase text-muted-foreground mb-1">Opening Balance</div>
									<div className="text-xl font-medium text-foreground">₹ 1,69,730.50</div>
								</div>
							</div>
						</div>
					</div>

					<div className="space-y-4">
						<motion.button
							whileHover={{ scale: 1.02 }}
							whileTap={{ scale: 0.98 }}
							className="w-full h-full max-h-[140px] flex flex-col justify-center items-center gap-3 bg-primary/10 border border-primary/20 hover:bg-primary/20 hover:border-primary/50 text-primary rounded-xl transition-all cursor-pointer p-6 group"
						>
							<div className="p-3 bg-background rounded-full group-hover:scale-110 transition-transform duration-300 shadow-sm">
								<ArrowDownLeft size={24} />
							</div>
							<span className="font-bold uppercase tracking-wider">Add Funds</span>
						</motion.button>

						<motion.button
							whileHover={{ scale: 1.02 }}
							whileTap={{ scale: 0.98 }}
							className="w-full h-full max-h-[140px] flex flex-col justify-center items-center gap-3 bg-card border border-border hover:border-foreground/20 text-foreground rounded-xl transition-all cursor-pointer p-6 group"
						>
							<div className="p-3 bg-background rounded-full group-hover:scale-110 transition-transform duration-300 shadow-sm border border-border">
								<ArrowUpRight size={24} className="text-muted-foreground group-hover:text-foreground" />
							</div>
							<span className="font-bold uppercase tracking-wider text-muted-foreground group-hover:text-foreground">Withdraw</span>
						</motion.button>
					</div>
				</motion.div>

				{/* Transactions */}
				<div className="pt-8">
					<motion.h3
						initial={{ opacity: 0 }}
						animate={{ opacity: 1 }}
						transition={{ delay: 0.5 }}
						className="flex items-center gap-2 text-lg font-bold border-b border-border pb-4 mb-6 text-foreground"
					>
						<History size={18} className="text-primary" />
						Recent Transactions
					</motion.h3>
					<div className="space-y-4">
						{[
							{ date: '29 Dec, 2025', desc: 'Fund Addition via UPI', amount: '+50,000.00', status: 'Success', icon: ArrowDownLeft, type: 'credit' },
							{ date: '28 Dec, 2025', desc: 'Settlement Payout', amount: '-12,400.00', status: 'Processed', icon: Landmark, type: 'debit' },
							{ date: '25 Dec, 2025', desc: 'Quarterly Maintenance Charges', amount: '-354.00', status: 'Debited', icon: CreditCard, type: 'debit' },
						].map((tx, i) => (
							<motion.div
								key={i}
								initial={{ opacity: 0, x: -20 }}
								animate={{ opacity: 1, x: 0 }}
								transition={{ delay: 0.6 + (i * 0.1) }}
								whileHover={{ x: 4, backgroundColor: 'var(--sidebar-accent)' }}
								className="flex items-center p-4 rounded-lg border border-border bg-card/50 hover:border-primary/30 transition-all cursor-default"
							>
								<div className={cn(
									"p-3 rounded-full mr-4 border",
									tx.type === 'credit' ? "bg-chart-2/10 border-chart-2/20 text-chart-2" : "bg-card border-border text-muted-foreground"
								)}>
									<tx.icon size={18} />
								</div>
								<div className="flex-1">
									<div className="font-bold text-foreground">{tx.desc}</div>
									<div className="text-xs text-muted-foreground mt-0.5">{tx.date}</div>
								</div>
								<div className="text-right">
									<div className={cn(
										"font-mono font-bold text-lg",
										tx.amount.startsWith('+') ? 'text-chart-2' : 'text-foreground'
									)}>
										{tx.amount}
									</div>
									<div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground bg-background px-2 py-0.5 rounded-full inline-block mt-1 border border-border">
										{tx.status}
									</div>
								</div>
							</motion.div>
						))}
					</div>
				</div>
			</div>
		</div>
	);
}