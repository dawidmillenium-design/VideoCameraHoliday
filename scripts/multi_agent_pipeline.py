import os
import openai

# Initialize OpenAI client pointed at DeepSeek's API
client = openai.OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

class Agent:
    def __init__(self, name, goal, backstory):
        self.name = name
        self.goal = goal
        self.backstory = backstory

    def run(self, task_description, context=""):
        prompt = f"""
        You are {self.name}. 
        Your goal: {self.goal}
        Your backstory: {self.backstory}
        
        Context from previous steps:
        {context}
        
        Task: {task_description}
        
        Rules:
        - Provide a detailed, professional, and highly actionable output in Markdown format.
        - Focus on real-world testing, E-E-A-T, and practical travel scenarios.
        - Do not include generic fluff; be specific to travel videography and camera gear.
        """
        response = client.chat.completions.create(
            model="deepseek-chat",  # DeepSeek's chat model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content

def main():
    year_range = os.getenv("YEAR_RANGE", "2026-2027")
    destinations = os.getenv("FOCUS_DESTINATIONS", "Bangkok, Santorini, Alps, Lisbon, Finland")
    cameras = os.getenv("FOCUS_CAMERAS", "DJI Osmo Pocket 3, GoPro Hero 13 Black, Sony ZV-1 II, Insta360 X5")

    print("🚀 Starting Multi-Agent SEO & Content Pipeline (DeepSeek)...")

    # 1. SEO Researcher Agent
    seo_researcher = Agent(
        name="Senior SEO Researcher",
        goal="Identify high-value, low-competition keyword clusters and search intent for travel videography and camera reviews.",
        backstory="You are an expert SEO analyst specializing in consumer electronics and travel niches. You know how to find keyword gaps for blogs like 'Holiday Video Camera', focusing on long-tail queries."
    )
    
    print("🔍 Agent 1: SEO Researcher is analyzing the niche...")
    seo_context = seo_researcher.run(f"""
        Analyze the SEO landscape for a travel camera review blog for {year_range}.
        Target cameras: {cameras}
        Target destinations: {destinations}
        Deliverable: A list of 15-20 high-intent keyword clusters, categorized by 'Buying Guides', 'How-To/Tutorials', and 'Destination-Specific Gear'. Include estimated search intent and difficulty.
    """)

    with open("docs/seo_strategy_2026_2027.md", "w", encoding="utf-8") as f:
        f.write(f"# SEO Strategy & Keyword Research ({year_range})\n\n")
        f.write(seo_context)

    # 2. Strategy Planner Agent
    strategy_planner = Agent(
        name="Content Strategy Director",
        goal="Synthesize SEO research into a cohesive content strategy, defining content pillars, target audience personas, and internal linking strategies.",
        backstory="You are a veteran content strategist who has scaled travel and tech blogs. You prioritize E-E-A-T, ensuring content reflects real-world field testing."
    )

    print("🧠 Agent 2: Strategy Planner is building the master strategy...")
    strategy_context = strategy_planner.run(f"""
        Based on the SEO research, create an extensive SEO & Content Strategy document.
        Include:
        1. Target Audience Personas.
        2. 4 Core Content Pillars.
        3. Internal Linking Strategy.
        4. E-E-A-T enhancement tactics (e.g., adding EXIF data, location timestamps, and raw footage samples to posts).
    """, context=seo_context)

    with open("docs/seo_strategy_2026_2027.md", "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n# Master Content Strategy\n\n")
        f.write(strategy_context)

    # 3. Calendar Generator Agent
    calendar_generator = Agent(
        name="Editorial Calendar Manager",
        goal="Create a detailed, month-by-month content calendar for 2026-2027 based on the strategy, accounting for seasonality.",
        backstory="You are a meticulous editorial manager. You know that 'best waterproof cameras' should be published in spring, and 'ski cameras' in autumn. You format everything in clean Markdown tables."
    )

    print("📅 Agent 3: Calendar Manager is drafting the schedule...")
    calendar_output = calendar_generator.run(f"""
        Create a month-by-month content calendar for {year_range}.
        For each month, provide:
        - 1 Flagship Review or Buying Guide (timed to seasonality).
        - 1 How-To or Editing Tutorial.
        - 1 Destination-Specific Gear Guide (rotate through: {destinations}).
        Format the output as a clean Markdown table with columns: Month, Article Title, Target Keyword, Content Pillar, and Status.
    """, context=strategy_context)

    with open("docs/content_calendar_2026_2027.md", "w", encoding="utf-8") as f:
        f.write(f"# Editorial Content Calendar ({year_range})\n\n")
        f.write(calendar_output)

    print("✅ Pipeline completed successfully! Files saved to /docs/")

if __name__ == "__main__":
    main()
