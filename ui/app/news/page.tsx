'use client';

import React from 'react';
import { Radio, AlertTriangle, Rss, Globe, TrendingUp } from 'lucide-react';
import { motion } from 'motion/react';

export default function NewsPage() {
	return (
		<div className="h-full flex flex-col items-center justify-center font-mono text-foreground bg-background p-8 text-center relative overflow-hidden">

			{/* Background Decor */}
			<div className="absolute inset-0 overflow-hidden pointer-events-none">
				<div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl opacity-20 animate-pulse"></div>
				<div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-chart-3/5 rounded-full blur-3xl opacity-20"></div>
			</div>

			<motion.div
				initial={{ scale: 0.9, opacity: 0 }}
				animate={{ scale: 1, opacity: 1 }}
				transition={{ duration: 0.5 }}
				className="max-w-md w-full border border-primary/30 p-1 bg-card/50 backdrop-blur-sm rounded-2xl shadow-2xl relative z-10"
			>
				<div className="border border-primary/20 p-8 rounded-xl bg-card/80 flex flex-col items-center">
					<div className="relative mb-6">
						<div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse"></div>
						<Radio className="w-16 h-16 text-primary relative z-10" />
					</div>

					<h2 className="text-2xl font-bold uppercase tracking-widest mb-3 text-foreground">News Stream Active</h2>

					<div className="space-y-4 mb-8 w-full">
						<div className="flex items-center gap-3 text-sm text-muted-foreground bg-background/50 p-3 rounded-lg border border-border/50">
							<Globe size={16} className="text-chart-4" />
							<span className="flex-1 text-left">Connecting to Global Feeds...</span>
							<span className="text-chart-2 text-[10px] font-bold">OK</span>
						</div>
						<div className="flex items-center gap-3 text-sm text-muted-foreground bg-background/50 p-3 rounded-lg border border-border/50">
							<TrendingUp size={16} className="text-chart-5" />
							<span className="flex-1 text-left">Sentiment Analysis Engine</span>
							<span className="text-chart-3 text-[10px] font-bold">INIT</span>
						</div>
						<div className="flex items-center gap-3 text-sm text-muted-foreground bg-background/50 p-3 rounded-lg border border-border/50">
							<Rss size={16} className="text-chart-1" />
							<span className="flex-1 text-left">Real-time Ticker Stream</span>
							<span className="text-muted-foreground text-[10px] font-bold">WAIT</span>
						</div>
					</div>

					<p className="text-muted-foreground text-xs max-w-xs leading-relaxed border-t border-border pt-4">
						System is currently establishing a secure low-latency connection to Bloomberg and Reuters terminals.
					</p>
				</div>
			</motion.div>

			<motion.div
				initial={{ y: 20, opacity: 0 }}
				animate={{ y: 0, opacity: 1 }}
				transition={{ delay: 0.5 }}
				className="mt-8 flex items-center gap-2 text-xs text-destructive border border-destructive/50 px-4 py-2 bg-destructive/5 rounded-full backdrop-blur-md"
			>
				<AlertTriangle size={14} />
				<span className="font-bold tracking-wide">BETA FEATURE: LATENCY {'>'} 200ms</span>
			</motion.div>
		</div>
	);
}