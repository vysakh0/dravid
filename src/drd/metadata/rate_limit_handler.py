import functools
import sys
import asyncio
import time
from ..api.main import call_dravid_api_with_pagination
from ..utils.parser import extract_and_parse_xml
from ..prompts.file_metada_desc_prompts import get_file_metadata_prompt
from ..utils.utils import print_info, print_error, print_success, print_warning

MAX_CONCURRENT_REQUESTS = 10
MAX_CALLS_PER_MINUTE = 100
RATE_LIMIT_PERIOD = 60  # seconds


class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = asyncio.Queue(maxsize=max_calls)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def acquire(self):
        while True:
            if self.calls.full():
                oldest_call = await self.calls.get()
                time_since_oldest_call = time.time() - oldest_call
                if time_since_oldest_call < self.period:
                    await asyncio.sleep(self.period - time_since_oldest_call)
            await self.calls.put(time.time())
            return


rate_limiter = RateLimiter(MAX_CALLS_PER_MINUTE, RATE_LIMIT_PERIOD)


def to_thread(func, *args, **kwargs):
    if sys.version_info >= (3, 9):
        return asyncio.to_thread(func, *args, **kwargs)
    else:
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


async def process_single_file(filename, content, project_context, folder_structure):
    metadata_query = get_file_metadata_prompt(
        filename, content, project_context, folder_structure)
    try:
        async with rate_limiter.semaphore:
            await rate_limiter.acquire()
            response = await to_thread(call_dravid_api_with_pagination, metadata_query, include_context=True)
        root = extract_and_parse_xml(response)
        type_elem = root.find('.//type')
        summary_elem = root.find('.//summary')
        exports_elem = root.find('.//exports')
        imports_elem = root.find('.//imports')  # Added imports_elem
        file_type = type_elem.text.strip(
        ) if type_elem is not None and type_elem.text else "unknown"
        summary = summary_elem.text.strip(
        ) if summary_elem is not None and summary_elem.text else "No summary available"
        exports = exports_elem.text.strip(
        ) if exports_elem is not None and exports_elem.text else ""
        imports = imports_elem.text.strip(
        ) if imports_elem is not None and imports_elem.text else ""  # Added imports
        print_success(f"Processed: {filename}")
        # Added imports to return tuple
        return filename, file_type, summary, exports, imports
    except Exception as e:
        print_error(f"Error processing {filename}: {e}")
        # Added empty string for imports in error case
        return filename, "unknown", f"Error: {e}", "", ""


async def process_files(files, project_context, folder_structure):
    total_files = len(files)
    print_info(
        f"Processing {total_files} files to construct metadata per file")
    print_info(f"LLM calls to be made: {total_files}")

    async def process_batch(batch):
        tasks = [process_single_file(filename, content, project_context, folder_structure)
                 for filename, content in batch]
        return await asyncio.gather(*tasks)

    batch_size = MAX_CONCURRENT_REQUESTS
    results = []
    for i in range(0, total_files, batch_size):
        batch = files[i:i+batch_size]
        batch_results = await process_batch(batch)
        results.extend(batch_results)
        print_info(f"Progress: {len(results)}/{total_files} files processed")

    return results
