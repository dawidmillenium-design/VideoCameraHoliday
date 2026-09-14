"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Camera, MapPin, Zap, Github, BarChart3 } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TerminalLog } from "@/components/TerminalLog";
import { toast } from "sonner";

export default function Home() {
  const [camera, setCamera] = useState("");
  const [destination, setDestination] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [activities, setActivities] = useState<any[]>([]);
  const [goalProgress, setGoalProgress] = useState(0); // 0-100

  useEffect(() => {
    // Fetch initial activity
    fetch("/api/activity")
      .then(res => res.json())
      .then(data => {
        setActivities(data);
        // Simple logic: 4 successful runs = 40% progress
        const successCount = data.filter((r: any) => r.conclusion === "success").length;
        setGoalProgress(Math.min((successCount / 10) * 100, 100));
      })
      .catch(err => console.error(err));
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!camera || !destination) {
      toast.error("Please fill in both fields");
      return;
    }

    setIsGenerating(true);
    toast.info("Initializing DeepSeek Engine...");

    try {
      await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera, destination }),
      });
      toast.success("Workflow Dispatched! Check the Terminal.");
      
      // Simulate completion after logs finish
      setTimeout(() => {
        setIsGenerating(false);
      }, 8000); // Matches terminal log duration approx
    } catch (error) {
      toast.error("Connection failed");
      setIsGenerating(false);
    }
  };

  // SVG Progress Circle Config
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (goalProgress / 100) * circumference;

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-20 lg:w-64 border-r border-white/5 p-6 flex flex-col gap-8 bg-slate-900/30 backdrop-blur-sm hidden md:flex">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center">
            <Camera className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight hidden lg:block">LensRanker</span>
        </div>
        <nav className="flex flex-col gap-4">
          <a href="#" className="flex items-center gap-3 text-slate-400 hover:text-white transition-colors px-2 py-2 rounded-lg bg-white/5">
            <Zap className="w-5 h-5" />
            <span className="hidden lg:inline">Dashboard</span>
          </a>
          <a href="#" className="flex items-center gap-3 text-slate-400 hover:text-white transition-colors px-2 py-2 rounded-lg">
            <BarChart3 className="w-5 h-5" />
            <span className="hidden lg:inline">Analytics</span>
          </a>
          <a href="https://github.com/dawidmillenium-design/VideoCameraHoliday" target="_blank" className="flex items-center gap-3 text-slate-400 hover:text-white transition-colors px-2 py-2 rounded-lg">
            <Github className="w-5 h-5" />
            <span className="hidden lg:inline">Repository</span>
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-8">
        <header className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              Content Command Center
            </h1>
            <p className="text-slate-400 mt-1">Automating SEO for VideoCameraHoliday</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs font-medium text-green-400">System Online</span>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Hero Generator */}
          <div className="lg:col-span-2 space-y-6">
            <GlassCard className="border-primary/20 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
              
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" /> Magic Generate
              </h2>
              
              <form onSubmit={handleGenerate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Target Camera Gear</label>
                    <div className="relative">
                      <Camera className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                      <input 
                        list="cameras"
                        value={camera}
                        onChange={(e) => setCamera(e.target.value)}
                        placeholder="e.g., Sony A7IV"
                        className="w-full bg-black/40 border border-white/10 rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-primary transition-colors text-white placeholder:text-slate-600"
                      />
                      <datalist id="cameras">
                        <option value="Sony A7IV" />
                        <option value="Fuji XT5" />
                        <option value="DJI Osmo Pocket 3" />
                        <option value="Canon R5" />
                      </datalist>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Holiday Destination</label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                      <input 
                        value={destination}
                        onChange={(e) => setDestination(e.target.value)}
                        placeholder="e.g., Kyoto, Japan"
                        className="w-full bg-black/40 border border-white/10 rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-primary transition-colors text-white placeholder:text-slate-600"
                      />
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full bg-gradient-to-r from-primary to-cyan-400 text-black font-bold py-4 rounded-xl shadow-lg hover:shadow-primary/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                >
                  <Zap className="w-5 h-5 group-hover:animate-pulse" />
                  {isGenerating ? "Generating Content..." : "Generate SEO Article"}
                </button>
              </form>
            </GlassCard>

            {/* Terminal */}
            <TerminalLog isGenerating={isGenerating} />
          </div>

          {/* Right Column: Stats & Activity */}
          <div className="space-y-6">
            <GlassCard className="text-center">
              <h3 className="text-sm font-medium text-slate-400 mb-6">Monthly Content Goal</h3>
              <div className="relative w-32 h-32 mx-auto mb-4">
                <svg className="w-full h-full -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r={radius}
                    stroke="#1e293b"
                    strokeWidth="12"
                    fill="transparent"
                  />
                  <motion.circle
                    cx="64"
                    cy="64"
                    r={radius}
                    stroke="url(#gradient)"
                    strokeWidth="12"
                    fill="transparent"
                    strokeLinecap="round"
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#06b6d4" />
                      <stop offset="100%" stopColor="#f97316" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold">{goalProgress}%</span>
                </div>
              </div>
              <p className="text-xs text-slate-500">4 of 10 posts generated</p>
            </GlassCard>

            <GlassCard>
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Github className="w-5 h-5" /> Live Activity
              </h3>
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                {activities.map((run) => (
                  <div key={run.id} className="flex items-center justify-between p-3 rounded-lg bg-black/20 border border-white/5">
                    <div>
                      <p className="text-sm font-medium text-white truncate max-w-[150px]">
                        {run.name || "Content Generation"}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(run.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <StatusBadge status={run.status === "completed" ? (run.conclusion || "success") : run.status} />
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>
      </main>
    </div>
  );
}
