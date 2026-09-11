import os
import sys
import logging
import openai
from dataclasses import dataclass
from typing import Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Insta360_Pipeline")

# --- DeepSeek Client Initialization ---
client = openai.OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
)
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# --- Data Structures ---
@dataclass
class AgentProfile:
    name: str
    role: str
    goal: str
    backstory: str

class AgentEngine:
    def __init__(self, profile: AgentProfile):
        self.profile = profile

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10),
           retry=retry_if_exception_type(openai.RateLimitError))
    def execute(self, task: str, context: str) -> str:
        prompt = f"""
        # ROLE: {self.profile.name} ({self.profile.role})
        # GOAL: {self.profile.goal}
        # EXPERTISE: {self.profile.backstory}
        
        # CONTEXT:
        {context}
        
        # TASK:
        {task}
        
        # STRICT RULES:
        1. Output MUST be in clean, structured Markdown.
        2. Focus strictly on REAL-WORLD field testing. No lab specs, no generic fluff.
        3. Emphasize E-E-A-T: mention specific weather, lighting, crowd levels, and handling techniques.
        4. Be highly specific about the "Invisible Stick" mechanics (e.g., stitching lines, parallax errors, wind resistance).
        """
        logger.info(f"🧠 Executing: {self.profile.name}")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096
        )
        return response.choices[0].message.content

def run_pipeline():
    camera = os.getenv("CAMERA_MODEL", "Insta360 X4")
    locations = os.getenv("TEST_LOCATIONS", "Bangkok Night Market, Santorini Cliffside, Swiss Alps, Miami Beach")
    focus = os.getenv("SERIES_FOCUS", "Proving the invisible stick works in extreme, crowded, and challenging real-world holiday scenarios")
    
    base_context = f"""
    BLOG: Holiday Video Camera (Real-world travel camera reviews).
    SERIES TOPIC: Real-world test scenarios of the {camera} Invisible Stick.
    LOCATIONS TO TEST: {locations}
    CORE FOCUS: {focus}
    RULE: Every claim must be backed by a specific, plausible field-test scenario (e.g., "tested at 28°C, 80% humidity in a crowded market").
    """

    agents = [
        AgentProfile("Scenario Architect", "Travel Videography Director", "Design 4 distinct, highly specific real-world test scenarios.", "Veteran travel filmmaker. You know exactly where and how the invisible stick fails or shines in the real world."),
        AgentProfile("Technical E-E-A-T Director", "Camera Gear Expert", "Define exact camera settings, handling techniques, and 'proof' elements for each scenario.", "You know the {camera} inside out. You specify exact resolution, framerate, ISO limits, and how to hold the stick to avoid stitching errors."),
        AgentProfile("GEO SEO Writer", "Search & AI Optimization Expert", "Write the SEO-optimized Series Landing Page introduction and structure.", "You structure content to be cited by Google AI Overviews. You use clear H2/H3s, direct answers, and entity-rich language."),
        AgentProfile("Media Asset Planner", "Video Production Manager", "List the exact B-roll, YouTube embeds, and comparison shots needed.", "You know that text isn't enough. You specify exactly what visual proof is needed (e.g., 'Side-by-side: Stick at arm's length vs. extended in crowded market')."),
        AgentProfile("Master Editor", "Executive Content Polisher", "Compile all outputs into a single, pristine, ready-to-publish Series Master Document.", "You eliminate redundancy, ensure perfect Markdown formatting, and add a clear 'Shooting Checklist' for the author.")
    ]

    tasks = [
        f"Design 4 distinct real-world test scenarios for the {camera} invisible stick based on these locations: {locations}. For each, define: The Challenge, The Setup, and The Expected Invisible Stick Behavior.",
        "For each of the 4 scenarios, provide exact technical specs: Resolution/Framerate, ISO limits, specific handling technique (e.g., 'hold at 45-degree angle to avoid drone propeller stitching'), and E-E-A-T proof markers (e.g., 'mention wind speed').",
        "Write the Series Landing Page content (approx. 400 words). Include a strong H1, an engaging intro hook about the 'magic' of the invisible stick, a direct-answer FAQ block for AI Overviews (e.g., 'Does the invisible stick work in crowds?'), and an intro to the 4 scenarios.",
        "Create a 'Required Media Assets' checklist for the author. Specify exact YouTube embed placeholders, before/after stitching comparison shots, and EXIF data captions needed for each of the 4 scenarios.",
        "Compile EVERYTHING above into ONE master Markdown document titled: 'Series Master: {camera} Invisible Stick Real-World Tests'. Include: Series Intro, The 4 Scenarios (with technical specs), Media Checklist, and a final 'Pre-Shoot Checklist'."
    ]

    context = base_context
    final_output = ""

    for i, agent_profile in enumerate(agents):
        engine = AgentEngine(agent_profile)
        try:
            result = engine.execute(tasks[i], context)
            context += f"\n\n### [{agent_profile.name} Output]\n{result}"
            if i == len(agents) - 1:
                final_output = result
            logger.info(f"✅ {agent_profile.name} completed.")
        except Exception as e:
            logger.error(f"❌ {agent_profile.name} failed: {e}")
            final_output = f"Error in pipeline: {str(e)}"

    # Save Output
    safe_camera_name = camera.replace(" ", "_").lower()
    filename = f"content/series/{safe_camera_name}_invisible_stick_master.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_output)

    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(f"## ✅ Insta360 Series Generated\n")
        f.write(f"- **Camera:** {camera}\n")
        f.write(f"- **Locations:** {locations}\n")
        f.write(f"- **Output File:** `{filename}`\n")
        f.write(f"- **Status:** Ready for review and shooting.\n")

    logger.info(f"🎉 Pipeline finished. Saved to {filename}")

if __name__ == "__main__":
    if not os.getenv("DEEPSEEK_API_KEY"):
        logger.error("DEEPSEEK_API_KEY not found!")
        sys.exit(1)
    run_pipeline()
