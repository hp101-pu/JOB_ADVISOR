import asyncio
from client.mcp.client import get_mcp_client


async def main():
    print("🔌 Creating MCP client...")
    mcp_client = get_mcp_client()

    print("📡 Discovering tools...")
    tools = await mcp_client.get_tools()

    print(f"✅ Found {len(tools)} tool(s):")
    for t in tools:
        print(f" - {t.name}")

    # ---- MANUAL TOOL CALL ----
    # Adjust tool name if needed
    gmail_tool = next(
        t for t in tools if t.name =="draft_reply"
    )

    # print("\n📨 Calling get_recent_job_emails...")
    # result = await gmail_tool.ainvoke(
    #     {
    #         "lookback_days": 3,
    #         "max_results": 5
    #     }
    # )
    print("\n Calling draft_reply tool")
    result=await gmail_tool.ainvoke({
        "message_id":"19b5e0fed9c5c1a1",
        "tone":"professional"

    })

    print("\n🎉 TOOL RESULT:")

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
