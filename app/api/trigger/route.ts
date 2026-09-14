import { NextResponse } from 'next/server';
import { Octokit } from "@octokit/rest";

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

const OWNER = "dawidmillenium-design";
const REPO = "VideoCameraHoliday";
const WORKFLOW_ID = "deepseek-seo-generator.yml";

export async function POST(req: Request) {
  try {
    const { camera, destination } = await req.json();

    if (!process.env.GITHUB_TOKEN) {
      // Mock Mode for development without keys
      return NextResponse.json({ success: true, message: "Mock trigger sent successfully." });
    }

    await octokit.request('POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches', {
      owner: OWNER,
      repo: REPO,
      workflow_id: WORKFLOW_ID,
      ref: 'main', // or 'master'
      inputs: {
        camera_gear: camera,
        destination: destination
      }
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("GitHub Trigger Error:", error);
    return NextResponse.json({ error: "Failed to trigger workflow" }, { status: 500 });
  }
}
