import { cn } from "@/lib/utils"; // Assuming you have clsx/tailwind-merge setup
import { motion } from "framer-motion";

export function GlassCard({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("glass-card", className)}
      {...props}
    >
      {children}
    </motion.div>
  );
}
