from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os, sys, json, logging, asyncio

# Initialize FastMCP server
mcp = FastMCP("fideo-app")

# Constants
FIDEO_API_BASE = "https://api.fideo.ai"
API_BASE = FIDEO_API_BASE
# Get the API key from the env variable
try:
    # Get a Free Trial for Verify: https://app.fideo.ai/register/offer/github
    # Contact sales for Signals access: https://fideo.ai/contact-us
    FIDEO_API_KEY = os.getenv("FIDEO_API_KEY")
except KeyError:
    sys.exit("Missing required environment variable: FIDEO_API_KEY")

USER_AGENT = "fideo-mcp/1.0"

LOG_PATH = "/tmp/fideo-mcp.log"
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


async def make_fideo_request(url: str, body: str) -> dict[str, Any] | None:
    """Make a request to the Fideo API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {FIDEO_API_KEY}",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            logging.info(f"Making request to {url} with body: {body}")
            response = await client.post(url, headers=headers, data=body, timeout=15.0)
            logging.info(f"Response status: {response.status_code}")

            if response.status_code == 204:
                # No content, no data to return
                return {'message':'No data found'}

            if response.status_code == 401:
                return {'message':'Authorization expired or invalid API key'}

            if response.status_code not in [200, 201]:
                logging.warning(f"Request failed request to {url} with body: {body}")
            response.raise_for_status()

            return response.json()
        except Exception:
            logging.exception(f"Error making request to {url}, {Exception}")
            return None

def clean_dict(d):
    """Recursively remove empty strings, None, and empty dicts from a dictionary."""
    if not isinstance(d, dict):
        return d
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, dict):
            nested = clean_dict(v)
            if nested:  # only keep if not empty
                cleaned[k] = nested
        elif isinstance(v, list):
            nested_list = [clean_dict(i) if isinstance(i, dict) else i for i in v]
            nested_list = [i for i in nested_list if i not in ("", None, {}, [])]
            if nested_list:
                cleaned[k] = nested_list
        elif v not in ("", None, {}, []):
            cleaned[k] = v
    return cleaned


def format_request(email: str = "", phone: str = "",
                   first_name: str = "", middle_name: str = "", last_name: str = "",
                   address_line1: str = "", address_line2: str = "", city: str = "",
                   region: str = "", region_code: str = "", postal_code: str = "",
                   country: str = "", country_code: str = "",
                   birthday: str = "", ip_address: str = "",
                   title: str = "", organization: str = "",
                   social_network: str = "", social_id: str = "", social_handle: str = "") -> str:
    """Format the request data for the Fideo Signals API."""
    req = {
        "email": email,
        "phone": phone,
        "name": {
            "given": first_name,
            "middle": middle_name,
            "family": last_name
        },
        "location": {
            "addressLine1": address_line1,
            "addressLine2": address_line2,
            "city": city,
            "region": region,
            "regionCode": region_code,
            "postalCode": postal_code,
            "country": country,
            "countryCode": country_code,
        },
        "profiles": [
            {
                "service": social_network,
                "username": social_handle,
                "userid": social_id
            }
        ],
        "birthday": birthday,
        "ipAddress": ip_address,
        "title": title,
        "organization": organization
    }
    # Remove all empty string and dict elements from the req

    return json.dumps(clean_dict(req))


@mcp.tool()
async def get_verify(email: str='', phone: str='', first_name: str='', middle_name: str='', last_name: str='',
                     address_line1: str='', address_line2: str='', city: str='', region: str='',
                     region_code: str='', postal_code: str='', country: str='', country_code: str='',
                     birthday: str='', ip_address: str='', job_title: str= '', org_name: str = '',
                     social_network: str = '', social_id: str = '', social_handle: str = '') -> str:
    """Call Fideo Verify for a risk score and finegrained check-by-check findings each which
    contributed to the overall risk decision. Checks include email, phone, name, address,
    synthetic identity, and device/IP analysis.

    Use this tool when you need a fraud or compliance risk assessment about an individual. Supply
    any identifiers you have; at least one of the following is required for Fideo to run a search:
    email, phone, name + address, or IP address. More context improves match accuracy.

    Args describe clear-text values unless noted (emails may also be MD5/SHA256 hashes, phones must
    be E.164). Optional identity, address, and employment fields help Verify link the correct
    person. The response is returned as a JSON string prefixed with `---` so clients can stream the
    raw payload.
    """
    url = f"{API_BASE}/verify"
    data = await make_fideo_request(url, format_request(email, phone, first_name, middle_name,
                                                        last_name, address_line1, address_line2,
                                                        city, region, region_code, postal_code,
                                                        country, country_code,
                                                        birthday, ip_address,
                                                        job_title, org_name,
                                                        social_network, social_id, social_handle))
    if not data:
        return "Error fetching results for verify."

    return "\n---\n" + json.dumps(data)


@mcp.tool()
async def get_signals(email: str='', phone: str='', first_name: str='', middle_name: str='', last_name: str='',
                      address_line1: str='', address_line2: str='', city: str='', region: str='',
                      region_code: str='', postal_code: str='', country: str='', country_code: str='',
                      birthday: str='', ip_address: str='', job_title: str= '', org_name: str = "",
                      social_network: str = '', social_id: str = '', social_handle: str = '') -> str:
    """Retrieve Fideo Signals profile intelligence about a person. Use cases are investigations,
    ossint, link analysis, and profile enrichment. Supply any identifiers you have; at least one
    of the following is required for Fideo to run a search: email, phone, name + address, or
    social media id/username. More context improves match accuracy.

    Signals enriches the individual with social profiles, linked identities, locations, work
    history, and other attributes. Provide hashed emails or E.164 phones when you cannot share
    clear-text data. Returns a JSON string prefixed with `---` containing the API response.
    """
    url = f"{API_BASE}/signals"
    input_payload = format_request(email, phone, first_name, middle_name,
                                   last_name, address_line1, address_line2,
                                   city, region, region_code, postal_code,
                                   country, country_code,
                                   birthday, ip_address,
                                   job_title, org_name,
                                   social_network, social_id, social_handle)
    data = await make_fideo_request(url, input_payload)
    if not data:
        return "Error fetching results for Signals."

    return "\n---\n" + json.dumps(data)


async def test():
    """Test function to run the get_signals tool."""
    result = await get_signals(social_network='linkedin', social_handle='kenmichie')
    logging.info(result)
    result = await get_verify(email='')
    logging.info(result)


if __name__ == "__main__":
    # Initialize and run the server
    asyncio.run(test())

    logging.info("Starting fideo-app server")
    mcp.run(transport='stdio')
