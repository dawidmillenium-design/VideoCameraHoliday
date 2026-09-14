import { NextResponse } from 'next/server';
import { Octokit } from "@octokit/rest";

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });

const OWNER = "dawidmillenium-design";
const REPO = "VideoCameraHoliday";

// Mock data for when GITHUB_TOKEN is missing
const MOCK_RUNS = [
  { id: 1, name: "Sony A7IV in Kyoto", status: "completed", conclusion: "success", created_at: "2023-10-27T10:00:00Z" },
  { id: 2, name: "DJI Osmo in Iceland", status: "in_progress", conclusion: null, created_at: "2023-10-27T09:30:00Z" },
  { id: 3, name: "Fuji XT5 in Alps", status: "completed", conclusion: "failure", created_at: "2023-10-26T14:00:00Z" },
];

export async function GET() {
  try {
    if (!process.env.GITHUB_TOKEN) {
      return NextResponse.json(MOCK_RUNS);
    }

    const { data } = await octokit.request('GET /repos/{owner}/{repo}/actions/runs', {
      owner: OWNER,
      repo: REPO,
      per_page: 5,
    });

    const runs = data.workflow_runs.map(run => ({
      id: run.id,
      name: run.display_title || run.name,
      status: run.status,
      conclusion: run.conclusion,
      created_at: run.created_at,
    }));

    return NextResponse.json(runs);
  } catch (error) {
    console.error("Activity Fetch Error:", error);
    return NextResponse.json({ error: "Failed to fetch activity" }, { status: 500 });
  }
}
