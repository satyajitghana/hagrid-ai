'use client'

import type React from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { useStickToBottomContext } from 'use-stick-to-bottom'
import { Button } from '@/components/ui/button'
import { ArrowDown } from 'lucide-react'

const ScrollToBottom: React.FC = () => {
	const { isAtBottom, scrollToBottom } = useStickToBottomContext()

	return (
		<AnimatePresence>
			{!isAtBottom && (
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					exit={{ opacity: 0, y: 20 }}
					transition={{ duration: 0.3, ease: 'easeInOut' }}
					className="absolute bottom-4 left-1/2 -translate-x-1/2"
				>
					<Button
						onClick={() => scrollToBottom()}
						type="button"
						size="icon"
						variant="secondary"
						className="border border-border bg-card text-foreground shadow-md transition-shadow duration-300 hover:bg-accent"
					>
						<ArrowDown className="h-4 w-4" />
					</Button>
				</motion.div>
			)}
		</AnimatePresence>
	)
}

export default ScrollToBottom