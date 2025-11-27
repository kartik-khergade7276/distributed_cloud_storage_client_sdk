
import asyncio, random, string, time
from sdk.gcs_client import StorageClient


def random_payload_kb(size_kb: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=size_kb * 1024))


async def run_benchmark(num_objects: int = 50, size_kb: int = 32) -> None:
    client = StorageClient(max_retries=2, backoff_factor=0.1)
    await client.create_bucket("benchmark-bucket")
    start = time.perf_counter()
    for i in range(num_objects):
        payload = random_payload_kb(size_kb)
        await client.put_object("benchmark-bucket", f"sample-{i}", payload)
    elapsed = time.perf_counter() - start
    throughput_mb_s = (num_objects * size_kb / 1024) / elapsed
    print(f"Uploaded {num_objects} objects of {size_kb}KB in {elapsed:.2f}s")
    print(f"Throughput: {throughput_mb_s:.2f} MB/s")
    print("Metrics:", client.summarize_metrics())
    await client.close()


if __name__ == "__main__":
    asyncio.run(run_benchmark())
