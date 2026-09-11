import os
import sys
import logging
import openai
from dataclasses import dataclass
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SEO_Pipeline")

# --- DeepSeek Client Initialization ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4.1-flash")

if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY is not set. Exiting.")
    sys.exit(1)

client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# --- Data Structures ---
@dataclass
class AgentProfile:
    name: str
    role: str
    goal: str
    backstory: str

@dataclass
class PipelineContext:
    base_context: str
    agent_outputs: Dict[str, str]

    def get_full_context(self) -> str:
        context = self.base_context
        for agent_name, output in self.agent_outputs.items():
            context += f"\n\n### [{agent_name} Output]\n{output}"
        return context

# --- Core Agent Engine ---
class AgentEngine:
    def __init__(self, profile: AgentProfile):
        self.profile = profile

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(openai.RateLimitError),
        before_sleep=lambda retry_state: logger.warning(f"Rate limited. Retrying in {retry_state.next_action.sleep}...")
    )
    def execute(self, task: str, context: str) -> str:
        prompt = f"""
        # ROLE
        You are {self.profile.name}, a world-class {self.profile.role}.
        
        # GOAL
        {self.profile.goal}
        
        # BACKSTORY & EXPERTISE
        {self.profile.backstory}
        
        # CURRENT CONTEXT
        {context}
        
        # YOUR TASK
        {task}
        
        # STRICT RULES
        1. Output MUST be in clean, structured Markdown (use H2, H3, tables, and bullet points).
        2. Be highly specific, actionable, and data-driven. No generic fluff.
        3. Focus strictly on the niche: real-world travel camera reviews (no lab specs).
        4. If you need to make a strategic assumption, state it clearly.
        """
        
        logger.info(f"🧠 Executing Agent: {self.profile.name}")
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, # Low temp for strategic accuracy
            max_tokens=4096
        )
        return response.choices[0].message.content

# --- Pipeline Definition ---
def run_pipeline():
    year_range = os.getenv("YEAR_RANGE", "2026-2027")
    destinations = os.getenv("FOCUS_DESTINATIONS", "Bangkok, Santorini, Alps, Lisbon, Finland")
    cameras = os.getenv("FOCUS_CAMERAS", "DJI Osmo Pocket 3, GoPro Hero 13 Black, Sony ZV-1 II, Insta360 X5")
    
    base_context = f"""
    PROJECT: Holiday Video Camera Blog ({year_range} Strategy)
    NICHE: Real-world travel camera reviews (field-tested, no lab specs).
    CORE GEAR: {cameras}
    CORE DESTINATIONS: {destinations}
    TARGET: SERP dominance, GEO (AI Overview) capture, and unfakeable E-E-A-T.
    """

    context = PipelineContext(base_context=base_context, agent_outputs={})
    engine = AgentEngine # We'll instantiate per agent

    agents = [
        AgentProfile("SERP Analyst", "Competitor & Gap Analyst", "Reverse-engineer top 10 SERPs to find content gaps.", "Former Ahrefs data scientist. Expert in finding low-difficulty, high-intent gaps."),
        AgentProfile("GEO Specialist", "Generative Engine Optimization Expert", "Optimize for AI Overviews (SGE) via entity mapping.", "Pioneer in GEO. Knows how to structure content for AI citation."),
        AgentProfile("Topical Architect", "Semantic SEO Architect", "Build hub-and-spoke topical clusters.", "Semantic SEO expert. Builds knowledge graphs connecting gear, locations, and problems."),
        AgentProfile("E-E-A-T Auditor", "Trust & Experience Auditor", "Define unfakeable proof signals.", "Google Quality Rater veteran. Distinguishes AI fluff from genuine experience."),
        AgentProfile("Link Graph Designer", "Technical SEO Specialist", "Design PageRank-optimizing internal links.", "Treats internal linking as a mathematical graph to funnel authority."),
        AgentProfile("Conversion Strategist", "CRO & Affiliate Expert", "Maximize affiliate conversions ethically.", "CRO expert for affiliate blogs. Masters natural CTA and comparison table placement."),
        AgentProfile("Calendar Manager", "Editorial Director", "Create a seasonality-aware 24-month calendar.", "Veteran editorial director. Aligns content with travel seasons and product cycles."),
        AgentProfile("QA Synthesizer", "Executive Technical Editor", "Compile and polish the final strategy document.", "Meticulous editor. Eliminates redundancy and ensures perfect Markdown formatting.")
    ]

    tasks = [
        f"Analyze SERP landscape for {year_range}. Identify 5 major content gaps competitors miss (e.g., lack of real-world humidity testing).",
        "Based on SERP gaps, define GEO strategy. List 10 key entities to map. Provide 3 formatting rules for AI Overview citation.",
        "Design the Topical Map. Define 3 Core Hubs. For each, list 4-5 specific spoke articles to close the topical loop.",
        "Define the E-E-A-T checklist. Specify exact 'proof' elements (EXIF data, weather conditions, timestamped raw footage).",
        "Create Internal Linking Rules. Define anchor text strategies and mandatory link counts between hubs and spokes.",
        f"Define conversion strategy for {cameras}. Where do comparison tables go? What are micro-conversions?",
        f"Generate a high-level 24-month calendar for {year_range}. Group by Quarter. For each: 1 Comparison, 1 Destination Guide, 1 Tutorial.",
        "Synthesize all previous outputs into ONE master document: 'Advanced GEO & SEO Strategy 2026-2027'. Include Executive Summary, Insights, Topical Map, E-E-A-T Rules, Linking Graph, Conversion Tactics, Quarterly Calendar, and 'First 90 Days Plan'."
    ]

    # Execute Sequentially to build context
    for i, agent_profile in enumerate(agents):
        agent = AgentEngine(agent_profile)
        try:
            result = agent.execute(tasks[i], context.get_full_context())
            context.agent_outputs[agent_profile.name] = result
            logger.info(f"✅ {agent_profile.name} completed successfully.")
        except Exception as e:
            logger.error(f"❌ {agent_profile.name} failed: {e}")
            context.agent_outputs[agent_profile.name] = f"ERROR: {str(e)}"

    # Save Outputs
    final_report = context.agent_outputs.get("QA Synthesizer", "Synthesis failed.")
    calendar_report = context.agent_outputs.get("Calendar Manager", "Calendar generation failed.")

    with open("docs/advanced_seo_strategy_2026_2027.md", "w", encoding="utf-8") as f:
        f.write(final_report)
    
    with open("docs/advanced_content_calendar_2026_2027.md", "w", encoding="utf-8") as f:
        f.write(f"# 24-Month Editorial Calendar ({year_range})\n\n{calendar_report}")

    # Write Summary for GitHub Actions
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write("## ✅ Pipeline Completed\n")
        f.write(f"- **Model:** {DEEPSEEK_MODEL}\n")
        f.write(f"- **Strategy Doc:** `docs/advanced_seo_strategy_2026_2027.md`\n")
        f.write(f"- **Calendar Doc:** `docs/advanced_content_calendar_2026_2027.md`\n")
        f.write(f"- **Total Agents:** 8\n")

    logger.info("🎉 Pipeline finished. Files saved to /docs/")

if __name__ == "__main__":
    run_pipeline()
