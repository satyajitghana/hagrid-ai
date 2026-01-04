'use client';

import React from 'react';
import {
	Area,
	AreaChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { CHART_DATA } from '@/data/mock-data';

export function StockChart({ symbol }: { symbol: string }) {
	return (
		<div className="w-full h-[250px] border border-border bg-card p-2 mt-2 mb-2">
			<div className="text-xs font-bold mb-2 uppercase px-2 text-foreground">{symbol} - Intraday (15m)</div>
			<ResponsiveContainer width="100%" height="90%">
				<AreaChart data={CHART_DATA}>
					<defs>
						<linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
							<stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.1} />
							<stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
						</linearGradient>
					</defs>
					<CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
					<XAxis
						dataKey="time"
						tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
						axisLine={false}
						tickLine={false}
					/>
					<YAxis
						domain={['auto', 'auto']}
						tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
						axisLine={false}
						tickLine={false}
						width={30}
					/>
					<Tooltip
						contentStyle={{
							backgroundColor: 'var(--card)',
							border: '1px solid var(--border)',
							borderRadius: '0px',
							fontSize: '12px',
							fontFamily: 'monospace',
							color: 'var(--foreground)'
						}}
						itemStyle={{ color: 'var(--foreground)' }}
						labelStyle={{ color: 'var(--muted-foreground)' }}
					/>
					<Area
						type="monotone"
						dataKey="price"
						stroke="var(--chart-1)"
						strokeWidth={1.5}
						fillOpacity={1}
						fill="url(#colorPrice)"
					/>
				</AreaChart>
			</ResponsiveContainer>
		</div>
	);
}