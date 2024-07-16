import asyncio
import time
from ..api.dravid_api import call_dravid_api_with_pagination
from ..api.dravid_parser import extract_and_parse_xml
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


async def process_single_file(filename, content, project_context, folder_structure):
    metadata_query = get_file_metadata_prompt(
        filename, content, project_context, folder_structure)
    try:
        async with rate_limiter.semaphore:
            await rate_limiter.acquire()
            response = call_dravid_api_with_pagination(
                metadata_query, include_context=True)

        root = extract_and_parse_xml(response)
        type_elem = root.find('.//type')
        desc_elem = root.find('.//description')
        exports_elem = root.find('.//exports')

        file_type = type_elem.text.strip(
        ) if type_elem is not None and type_elem.text else "unknown"
        description = desc_elem.text.strip(
        ) if desc_elem is not None and desc_elem.text else "No description available"
        exports = exports_elem.text.strip(
        ) if exports_elem is not None and exports_elem.text else ""

        print_success(f"Processed: {filename}")
        return filename, file_type, description, exports
    except Exception as e:
        print_error(f"Error processing {filename}: {e}")
        return filename, "unknown", f"Error: {e}", ""


async def process_files(files, project_context, folder_structure):
    total_files = len(files)
    print_info(
        f"Processing {total_files} files to construct metadata per file")
    print_info(f"LLM call to be made: {total_files}")

    tasks = [process_single_file(filename, content, project_context, folder_structure)
             for filename, content in files]

    results = []
    for completed in asyncio.as_completed(tasks):
        result = await completed
        results.append(result)
        print_info(f"Progress: {len(results)}/{total_files} files processed")

    return results
