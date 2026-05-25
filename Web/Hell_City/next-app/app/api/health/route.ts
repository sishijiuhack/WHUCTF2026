import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    ok: true,
    service: "hell-city-next",
    pid: process.pid,
    hostname: process.env.HOSTNAME ?? "unknown",
    note: "Internal service only",
  });
}
