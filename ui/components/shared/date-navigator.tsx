'use client';

import React from 'react';
import { motion } from 'motion/react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { format, addDays, subDays, parseISO, isSameDay, isFuture } from 'date-fns';

export function DateNavigator() {
	const { selectedDate, setSelectedDate } = useAppStore();

	const dateObj = parseISO(selectedDate);
	const today = new Date();

	const handlePrevDay = () => {
		const newDate = subDays(dateObj, 1);
		setSelectedDate(format(newDate, 'yyyy-MM-dd'));
	};

	const handleNextDay = () => {
		const newDate = addDays(dateObj, 1);
		// Don't allow future dates
		if (isFuture(newDate)) return;

		setSelectedDate(format(newDate, 'yyyy-MM-dd'));
	};

	const isToday = isSameDay(dateObj, today);
	const formattedDate = format(dateObj, 'yyyy-MM-dd');

	return (
		<div className="flex items-center justify-between p-4 border-b border-border bg-card shrink-0">
			<div className="flex items-center gap-2 text-xs uppercase tracking-widest text-muted-foreground">
				<Calendar size={14} />
				<span>Session Date</span>
			</div>

			<div className="flex items-center gap-4">
				<button
					onClick={handlePrevDay}
					className="p-1 hover:text-primary transition-colors"
				>
					<ChevronLeft size={16} />
				</button>

				<div className="text-sm font-bold text-foreground w-28 text-center">
					{formattedDate}
				</div>

				<button
					onClick={handleNextDay}
					disabled={isToday}
					className={cn(
						"p-1 transition-colors",
						isToday ? "text-muted-foreground opacity-50 cursor-not-allowed" : "hover:text-primary"
					)}
				>
					<ChevronRight size={16} />
				</button>
			</div>

			<div className="w-24 text-right">
				{isToday && (
					<motion.span
						initial={{ opacity: 0 }}
						animate={{ opacity: 1 }}
						className="text-[10px] text-chart-2 border border-chart-2 px-1.5 py-0.5"
					>
						LIVE SESSION
					</motion.span>
				)}
				{!isToday && (
					<span className="text-[10px] text-muted-foreground border border-border px-1.5 py-0.5">
						ARCHIVED
					</span>
				)}
			</div>
		</div>
	);
}