'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Terminal, BarChart2, Briefcase, Wallet, Bell, Settings, Radio, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
	{ id: 'analysis', icon: Terminal, label: 'Analysis', path: '/' },
	{ id: 'staging', icon: Zap, label: 'AI Picks', path: '/staging' },
	{ id: 'market', icon: BarChart2, label: 'Market Watch', path: '/market' },
	{ id: 'positions', icon: Briefcase, label: 'Positions', path: '/positions' },
	{ id: 'funds', icon: Wallet, label: 'Funds', path: '/funds' },
	{ id: 'news', icon: Radio, label: 'News Stream', path: '/news' },
];

export function Sidebar() {
	const pathname = usePathname();

	return (
		<div className="w-64 flex flex-col border-r border-sidebar-border bg-sidebar shrink-0 z-20 h-full">
			<div className="p-4 border-b border-sidebar-border bg-background text-foreground shrink-0">
				<div className="flex items-center gap-2">
					<motion.div
						animate={{ opacity: [1, 0.5, 1] }}
						transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
						className="w-3 h-3 bg-chart-2 rounded-none"
					/>
					<h1 className="font-bold text-lg tracking-widest text-foreground">HAGRID AI</h1>
				</div>
				<div className="text-[10px] text-muted-foreground mt-1 uppercase">v1.0.4 • Connected</div>
			</div>

			<nav className="flex-1 flex flex-col overflow-y-auto scrollbar-hide">
				{NAV_ITEMS.map((item) => {
					const isActive = pathname === item.path || (item.path !== '/' && pathname?.startsWith(item.path));

					return (
						<Link
							key={item.id}
							href={item.path}
							className="relative w-full group"
						>
							<div className={cn(
								"flex items-center gap-3 p-3 text-sm font-mono transition-colors border-b border-r border-sidebar-border z-10 relative",
								isActive
									? "bg-background text-primary border-r-transparent"
									: "bg-sidebar text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground"
							)}>
								<item.icon size={16} className={cn(
									"transition-transform duration-300",
									isActive ? "scale-110" : "group-hover:scale-110"
								)} />
								<span className="uppercase tracking-wider">{item.label}</span>
								{isActive && (
									<motion.span
										layoutId="activeTabIndicator"
										className="ml-auto text-primary font-bold"
										initial={{ opacity: 0, x: -10 }}
										animate={{ opacity: 1, x: 0 }}
										transition={{ duration: 0.2 }}
									>
										›
									</motion.span>
								)}
							</div>
							{isActive && (
								<motion.div
									layoutId="activeTabBg"
									className="absolute inset-0 bg-background border-l-4 border-l-primary"
									initial={{ opacity: 0 }}
									animate={{ opacity: 1 }}
									transition={{ duration: 0.2 }}
								/>
							)}
						</Link>
					);
				})}

				<div className="mt-auto shrink-0">
					<div className="border-t border-sidebar-border p-4 text-xs space-y-2 bg-background">
						<div className="flex justify-between items-center group cursor-default">
							<span className="text-muted-foreground group-hover:text-foreground transition-colors">NIFTY 50</span>
							<span className="font-bold text-chart-2 group-hover:scale-105 transition-transform">19,450.00</span>
						</div>
						<div className="flex justify-between items-center group cursor-default">
							<span className="text-muted-foreground group-hover:text-foreground transition-colors">BANKNIFTY</span>
							<span className="font-bold text-destructive group-hover:scale-105 transition-transform">44,200.50</span>
						</div>
					</div>
					<button className="w-full flex items-center gap-3 p-3 text-sm font-mono border-t border-sidebar-border hover:bg-sidebar-accent text-muted-foreground hover:text-foreground text-left transition-colors group">
						<motion.div whileHover={{ rotate: 90 }} transition={{ duration: 0.2 }}>
							<Settings size={16} />
						</motion.div>
						<span className="uppercase tracking-wider">Settings</span>
					</button>
				</div>
			</nav>
		</div>
	);
}