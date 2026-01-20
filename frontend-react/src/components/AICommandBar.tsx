import React, { useState } from 'react';
import { Sparkles, ArrowRight, Command } from 'lucide-react';

interface Props {
  onCommand: (cmd: string) => void;
  isProcessing?: boolean;
}

const AICommandBar: React.FC<Props> = ({ onCommand, isProcessing }) => {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onCommand(input);
      setInput('');
    }
  };

  return (
    <div className={`relative w-full max-w-2xl mx-auto transition-all duration-300 z-50 ${isFocused ? 'scale-105' : 'scale-100'}`}>
      <div className={`absolute -inset-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-25 transition-opacity duration-500 ${isFocused ? 'opacity-75' : 'opacity-25'}`}></div>
      
      <form onSubmit={handleSubmit} className="relative glass-panel rounded-xl p-1 flex items-center gap-2 shadow-2xl">
        <div className="pl-3 text-neon-purple">
          <Sparkles size={20} className={isProcessing ? 'animate-spin' : ''} />
        </div>
        
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={isProcessing ? "AI 正在分析数据..." : "Ask AI: 'Show me coffee sales from last weekend'..."}
          className="flex-1 bg-transparent border-none outline-none text-white placeholder-slate-400 h-10 px-2 font-mono text-sm"
          disabled={isProcessing}
        />

        <div className="hidden md:flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded text-[10px] text-slate-500 font-mono border border-white/5">
          <Command size={10} />
          <span>K</span>
        </div>

        <button 
          type="submit" 
          disabled={!input.trim() || isProcessing}
          className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ArrowRight size={16} />
        </button>
      </form>
    </div>
  );
};

export default AICommandBar;
