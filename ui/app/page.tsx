'use client';

import React, { useState, useRef } from 'react';
import { Send, Cpu, Clock, AlertTriangle, CheckCircle, BarChart2, Lock } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { DateNavigator } from '@/components/shared/date-navigator';
import { StockChart } from '@/components/shared/stock-chart';
import { HISTORY_DATA, LIVE_MESSAGES_INIT, Message } from '@/data/mock-data';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { format, subDays, parseISO, isSameDay } from 'date-fns';
import { AutoResizeTextarea } from '@/components/ui/auto-resize-textarea';
import ScrollToBottom from '@/components/ui/scroll-to-bottom';
import { StickToBottom } from 'use-stick-to-bottom';

export default function AnalysisPage() {
  const { selectedDate } = useAppStore();
  const [input, setInput] = useState('');

  // Current "Live" Messages
  const [liveMessages, setLiveMessages] = useState<Message[]>(LIVE_MESSAGES_INIT);
  const [isTyping, setIsTyping] = useState(false);

  const today = new Date();
  const selectedDateObj = parseISO(selectedDate);
  const isToday = isSameDay(selectedDateObj, today);
  const yesterday = subDays(today, 1);
  const isYesterday = isSameDay(selectedDateObj, yesterday);

  const displayMessages = isToday
    ? liveMessages
    : (isYesterday ? HISTORY_DATA['YESTERDAY'] : []);

  const isHistorical = !isToday;

  const handleSend = () => {
    if (!input.trim() || isHistorical) return;

    const now = new Date();
    const timeString = format(now, 'HH:mm:ss');

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      type: 'text',
      timestamp: timeString
    };

    setLiveMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Mock AI response
    setTimeout(() => {
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        type: 'text',
        timestamp: format(new Date(), 'HH:mm:ss')
      };

      const lowerInput = userMsg.content.toLowerCase();

      if (lowerInput.includes('reliance') || lowerInput.includes('chart')) {
        aiMsg.content = 'Here is the technical analysis for RELIANCE based on 15m candles. RSI is currently at 65 (Neutral/Bullish). MACD crossover detected suggesting upward momentum.';
        aiMsg.type = 'chart';
        aiMsg.metadata = { symbol: 'RELIANCE' };
      } else if (lowerInput.includes('buy') || lowerInput.includes('order')) {
        aiMsg.content = 'Order Request Received. \nValidating margins... \n\nOrder placed successfully:\nBUY RELIANCE @ MKT\nQty: 100\nMargin Used: ₹49,500';
        aiMsg.type = 'execution';
      } else if (lowerInput.includes('picks') || lowerInput.includes('suggest')) {
        aiMsg.content = 'I have refreshed the Staging Area with new potential setups based on current market breadth. Check the "AI Picks" tab for details.';
      } else {
        aiMsg.content = 'I am processing market data. Please specify a stock or command.';
      }

      setLiveMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full font-mono text-sm bg-background text-foreground">
      {/* Date Navigation */}
      <DateNavigator />

      {/* Messages Area */}
      <StickToBottom
        className="flex-1 overflow-auto p-4 scrollbar-hide relative flex flex-col"
        resize="smooth"
        initial="smooth"
      >
        <StickToBottom.Content className="flex flex-col gap-6 pb-4">
          <AnimatePresence mode="popLayout">
            {displayMessages.length > 0 ? (
              displayMessages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'system' ? (
                    <div className="w-full flex justify-center my-2">
                      <div className="text-[10px] uppercase tracking-widest text-destructive border border-destructive px-3 py-1 bg-destructive/10 flex items-center gap-2">
                        <AlertTriangle size={12} />
                        {msg.content}
                        <span className="opacity-50 border-l border-destructive pl-2 ml-2">{msg.timestamp}</span>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={cn(
                        "max-w-[80%] border p-4 shadow-sm relative group",
                        msg.role === 'user'
                          ? "bg-sidebar border-border text-foreground"
                          : "bg-card border-border text-foreground/90",
                        msg.type === 'execution' ? "border-chart-2 bg-chart-2/5" : ""
                      )}
                    >
                      {/* Message Header */}
                      <div className="flex items-center gap-2 mb-3 text-xs font-bold uppercase tracking-wider text-muted-foreground border-b border-border pb-2">
                        {msg.role === 'assistant' ? <Cpu size={14} className="text-primary" /> : null}
                        {msg.role === 'assistant' ? 'Hagrid AI Core' : 'Operator'}

                        {msg.type === 'execution' && (
                          <span className="flex items-center gap-1 text-chart-2 ml-2 px-1.5 py-0.5 border border-chart-2 text-[9px] rounded-sm">
                            <CheckCircle size={9} /> EXECUTION
                          </span>
                        )}

                        <span className="ml-auto text-[10px] opacity-50 flex items-center gap-1">
                          <Clock size={10} /> {msg.timestamp}
                        </span>
                      </div>

                      {/* Content */}
                      <div className="whitespace-pre-wrap leading-relaxed text-[13px]">
                        {msg.content}
                      </div>

                      {/* Rich Media: Charts */}
                      {msg.type === 'chart' && msg.metadata && (
                        <div className="mt-4 border border-border p-2 bg-background">
                          <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground uppercase">
                            <BarChart2 size={12} /> Technical Chart: {msg.metadata.symbol}
                          </div>
                          <StockChart symbol={msg.metadata.symbol} />
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col items-center justify-center text-muted-foreground gap-4 py-20"
              >
                <Lock size={32} />
                <div className="text-center">
                  <p className="font-bold uppercase tracking-widest">Archived Log Encrypted</p>
                  <p className="text-xs mt-2">No accessible conversation history for this date.</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {isTyping && !isHistorical && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex justify-start w-full"
            >
              <div className="bg-card border border-border p-4 flex items-center gap-2">
                <motion.span
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                  className="w-1.5 h-1.5 bg-chart-3"
                />
                <motion.span
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                  className="w-1.5 h-1.5 bg-chart-3"
                />
                <motion.span
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                  className="w-1.5 h-1.5 bg-chart-3"
                />
              </div>
            </motion.div>
          )}
        </StickToBottom.Content>
        <ScrollToBottom />
      </StickToBottom>

      {/* Input Area */}
      <div className="p-4 bg-background border-t border-border">
        <div className="max-w-4xl mx-auto flex items-end gap-3">
          <div className="flex-1 relative group">
            <AutoResizeTextarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isHistorical}
              placeholder={isHistorical ? "ARCHIVE MODE - READ ONLY" : "Command Hagrid AI (e.g., 'Analyze Reliance', 'Buy TCS')..."}
              className={cn(
                "border-border group-focus-within:border-primary",
                isHistorical && "opacity-50 cursor-not-allowed"
              )}
            />
          </div>
          <motion.button
            onClick={handleSend}
            disabled={!input.trim() || isTyping || isHistorical}
            whileHover={!isHistorical ? { scale: 1.05, backgroundColor: "var(--sidebar-accent)", borderColor: "var(--primary)", color: "var(--primary)" } : {}}
            whileTap={!isHistorical ? { scale: 0.95 } : {}}
            className={cn(
              "h-[42px] w-[42px] flex items-center justify-center border text-primary transition-colors shrink-0 mb-1 rounded-md",
              isHistorical
                ? "border-border bg-card text-muted-foreground opacity-50 cursor-not-allowed"
                : "border-border bg-card disabled:opacity-30 disabled:cursor-not-allowed"
            )}
          >
            {isHistorical ? <Lock size={18} /> : <Send size={18} />}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
