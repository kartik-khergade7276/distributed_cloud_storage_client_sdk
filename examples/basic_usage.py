
import asyncio
from sdk.gcs_client import StorageClient


async def main() -> None:
    client = StorageClient()
    print("Health:", await client.health())
    await client.create_bucket("demo-bucket")
    print("Buckets:", await client.list_buckets())
    await client.put_object("demo-bucket", "hello.txt", "Hello, Distributed Cloud Storage!")
    print("Objects:", await client.list_objects("demo-bucket"))
    data = await client.get_object("demo-bucket", "hello.txt")
    print("Downloaded:", data)
    print("Metrics:", client.summarize_metrics())
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
