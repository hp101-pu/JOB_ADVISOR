import asyncio
import base64
from client.mcp.client import get_mcp_client

async def main():
    print("🔌 Creating MCP client...")
    mcp_client = get_mcp_client()

    print("📡 Discovering tools...")
    tools = await mcp_client.get_tools()

    print("✅ Tools found:")
    for t in tools:
        print(" -", t.name)

    resume_tool = next(t for t in tools if t.name == "parse_resume")

    with open("sample_resume.pdf", "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    print("\n📄 Calling parse_resume...\n")
    result = await resume_tool.ainvoke({
        "file_b64": pdf_b64
    })

    print("🎉 RESULT:\n")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
