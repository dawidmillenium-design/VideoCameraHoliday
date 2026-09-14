import { motion } from "framer-motion";
import { Terminal } from "lucide-react";

const logMessages = [
  "Connecting to DeepSeek API...",
  "Analyzing target keywords for 'Sony A7IV'...",
  "Scraping top 10 travel photography articles...",
  "Generating semantic outline...",
  "Drafting content (2500 words)...",
  "Optimizing YAML frontmatter...",
  "Committing to branch: lensranker/auto-sony-a7iv..."
];

export function TerminalLog({ isGenerating }: { isGenerating: boolean }) {
  return (
    <div className="rounded-lg bg-black/80 border border-white/5 overflow-hidden font-mono text-sm shadow-inner">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5 bg-white/5">
        <Terminal className="w-4 h-4 text-cyan-400" />
        <span className="text-slate-400 text-xs">system_logs</span>
        <div className="flex gap-1.5 ml-auto">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
        </div>
      </div>
      <div className="p-4 h-48 overflow-y-auto space-y-1">
        {isGenerating ? (
          logMessages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.5 }}
              className="text-slate-300 flex"
            >
              <span className="text-cyan-500 mr-2">&gt;</span>
              <span>{msg}</span>
            </motion.div>
          ))
        ) : (
          <div className="text-slate-500 italic">System idle. Waiting for generation trigger...</div>
        )}
      </div>
    </div>
  );
}
