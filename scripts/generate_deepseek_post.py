import os
import yaml
from datetime import datetime
from slugify import slugify
from openai import OpenAI

# --- Configuration ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
TARGET_CAMERA = os.environ.get("TARGET_CAMERA", "Travel Camera")
TARGET_DESTINATION = os.environ.get("TARGET_DESTINATION", "Travel Destination")

if not DEEPSEEK_API_KEY:
    raise ValueError("Missing DEEPSEEK_API_KEY environment variable.")

# Initialize DeepSeek Client (OpenAI Compatible)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

def generate_content():
    system_prompt = """
    You are an expert SEO content writer and professional travel videographer. 
    Your goal is to write high-ranking blog posts that help travelers capture better footage.
    
    CRITICAL CONSTRAINTS:
    1. DO NOT invent specific camera specs (like max ISO or shutter speeds) if you aren't 100% sure. Use phrases like "adjust ISO according to lighting" instead of fake numbers.
    2. Focus on practical videography tips: stabilization, frame rates, color profiles.
    3. Tone: Adventurous, authoritative, yet accessible.
    4. Format: Valid Markdown only. No introductory text like "Here is the article".
    """

    user_prompt = f"""
    Write a comprehensive, 2,000-word blog post about using the "{TARGET_CAMERA}" for a holiday trip to "{TARGET_DESTINATION}".
    
    Required Sections:
    1. Introduction: Why this combo is great for travel.
    2. Key Features of {TARGET_CAMERA} for this location.
    3. Best Camera Settings for {TARGET_DESTINATION} (Lighting conditions, terrain).
    4. Essential Lenses/Accessories needed.
    5. Videography Tips for this specific location (Permits, best times of day).
    6. Conclusion.
    
    SEO Keywords to include naturally: "{TARGET_CAMERA} review", "filming in {TARGET_DESTINATION}", "travel videography gear".
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

def create_post_file(markdown_content):
    # Create a clean slug: "Sony-A7IV-Iceland" -> "sony-a7iv-iceland"
    base_slug = slugify(f"{TARGET_CAMERA}-{TARGET_DESTINATION}")
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename_slug = f"{date_str}-{base_slug}.md"
    
    # YAML Frontmatter tailored for Jekyll (matching VideoCameraHoliday structure)
    frontmatter = {
        "title": f"The Ultimate Guide to Filming in {TARGET_DESTINATION} with the {TARGET_CAMERA}",
        "date": datetime.now().isoformat(),
        "layout": "post",  # Ensures Jekyll renders it correctly
        "draft": True,     # SAFETY: Set to False only after you review the PR
        "tags": [
            slugify(TARGET_CAMERA), 
            slugify(TARGET_DESTINATION), 
            "Travel Videography", 
            "SEO",
            "Gear Guide"
        ],
        "description": f"Discover the best camera settings, gear, and videography tips for traveling to {TARGET_DESTINATION} with the {TARGET_CAMERA}.",
        "author": "LensRanker AI Assistant"
    }
    
    # Ensure _posts directory exists
    output_dir = "_posts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.join(output_dir, filename_slug)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        # Use safe_dump to ensure valid YAML
        f.write(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False))
        f.write("---\n\n")
        f.write(markdown_content)
        
    print(f"✅ Successfully generated post: {filename}")

if __name__ == "__main__":
    print(f"🚀 LensRanker AI: Generating content for {TARGET_CAMERA} in {TARGET_DESTINATION}...")
    try:
        content = generate_content()
        create_post_file(content)
        print("✨ Done! Ready for PR creation.")
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        exit(1)
