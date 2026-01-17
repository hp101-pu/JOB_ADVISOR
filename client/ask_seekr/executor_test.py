import asyncio

from client.ask_seekr.executor import run_pipeline



JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2OTc5MGI0YTc4ZTVhMTRjYmRkMzZmMjMiLCJlbWFpbCI6ImRhdmlkQGV4YW1wbGUuY29tIiwiZnVsbG5hbWUiOiJkYXZpZCIsImlhdCI6MTc2OTU0MDc3OCwiZXhwIjoxNzY5NjI3MTc4fQ.diKFpbHYb0TCn4GmeU5XAUL4QGcWak4mlEPQOfbzsK0"

PIPELINE_NAME = "email_sync"
ENDPOINT = "/pipelines/email-sync"
ARGS = {}



# -------------------------------------------------
# TEST
# -------------------------------------------------

async def test_executor():
    print("🚀 Testing executor...")
    print("Pipeline:", PIPELINE_NAME)
    print("Endpoint:", ENDPOINT)
    print("Args:", ARGS)
    print("-" * 50)

    result = await run_pipeline(
        pipeline_name=PIPELINE_NAME,
        endpoint=ENDPOINT,
        args=ARGS,
        jwt=JWT,
    )

    print("✅ EXECUTION RESULT")
    print(result)


if __name__ == "__main__":
    asyncio.run(test_executor())
