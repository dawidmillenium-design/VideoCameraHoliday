import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "success" | "running" | "failed" | "pending";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const colors = {
    success: "bg-green-500/20 text-green-400 border-green-500/30",
    running: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
    pending: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  };

  const dotColors = {
    success: "bg-green-500",
    running: "bg-cyan-500 animate-pulse",
    failed: "bg-red-500",
    pending: "bg-slate-500",
  };

  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border", colors[status])}>
      <span className={cn("w-2 h-2 rounded-full", dotColors[status])} />
      {status.toUpperCase()}
    </span>
  );
}
