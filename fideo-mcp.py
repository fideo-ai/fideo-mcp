from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os, sys, json, logging, asyncio

# Initialize FastMCP server
mcp = FastMCP("fideo-app")

# Constants
FIDEO_API_BASE = "https://api.fideo.ai"
LOCAL_API_BASE = "http://localhost:8888"
API_BASE = FIDEO_API_BASE
# Get the API key from the env variable
try:
    FIDEO_API_KEY = os.getenv("FIDEO_API_KEY", default="")
except KeyError:
    sys.exit("Missing required environment variable: FIDEO_API_KEY")

USER_AGENT = "fideo-app/1.0"

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
                   title: str = "", organization: str = "") -> str:
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
        "birthday": birthday,
        "ipAddress": ip_address,
        "title": title,
        "organization": organization
    }
    # Remove all empty string and dict elements from the req

    return json.dumps(clean_dict(req))


@mcp.tool()
async def get_verify(email: str, phone: str, first_name: str='', middle_name: str='', last_name: str='',
                     address_line1: str='', address_line2: str='', city: str='', region: str='',
                     region_code: str='', postal_code: str='', country: str='', country_code: str='',
                     birthday: str='', ip_address: str='', title: str='', organization: str = "",
                     ) -> str:
    """Objective: Verify accepts information about a person to perform a high level risk assessment.
    It's API docs are https://docs.fideo.ai/docs/verify, and provides a risk score (0-100, 0 being
    lowest) and granular check results based on the following checks:
    - Synthetic Identity Checks: Compare name, address, email, phone, birthday vs. age, and
    device/IP linkages against authoritative records. Flags mismatches (e.g. tangled names,
    mismatched address lines, birthday‑age conflict, excessive connectivity) that indicate
    fabricated or synthetic profiles.
    - Breached Identity Checks: Monitor identity exposure via known data breaches. Surface
    recently compromised identities for credential‑stuffing and takeover risk.
    - Digital Footprint Checks: Assess coherence and longevity of online signals—social profiles,
    connectivity patterns, device/IP relationships. Detect absent or anomalous digital presence
    tied to risk.
    - Email Checks: Evaluate email deliverability, domain risk, creation date, usage history,
    format, and account type (e.g. business vs disposable). Flags newly seen, invalid, disposable,
    or business emails (often fraud vectors).
    - Identity Checks: Perform coherence checks across identity fields and sanction-list
    screening (OFAC, EU, UN, UK, Canada). Identify over‑connected or internally
    inconsistent identities.
    - IP Address Checks: Classify IP type (TOR, VPN, data center, mobile, residential), check
    geolocation consistency vs. declared address, detect anonymizer use, cloud hosts, and proxy
    masking.
    - Location Checks: Validate street address formatting and existence, distinguish residential
    vs business/commercial (e.g. P.O. boxes, call centers, drop sites), and assess country-level
    fraud risk.
    - Phone Checks: Analyze phone number origin (first_seen), recency (last_seen), format validity,
    type (business vs personal), porting data, and location match. Detect freshly ported,
    long-dormant or burner lines.
    
    Response includes the risk score and an array of check results, each including:
    - id: the unique ID of the check that was run
    - name: the simple name of the check
    - description: a description of the check intended to be human readable
    - risk: general risk of the result, being none, low, medium or high
    - checkPackage: the package containing the check

    Inputs much include a minimum of: email or phone or name & address or ip address
    Args:
        email: clear text, md5 or sha256 email addressed to lookup representing a person
        phone: clear text, e.164 formatted phone number to lookup representing a person
        first_name: given, or first name of the person
        middle_name: middle name of the person
        last_name: family, or last name of the person
        birthday: Birthday in the form of yyyy-MM-dd, yyyy-MM, MM-dd, yyyy or MM
        ip_address: Current IP address of the person
        address_line1: street level address of the person
        address_line2: extended street level address of the person
        city: city of the person
        region: region, or state of the person in full text
        region_code: region, or state of the person in ISO 2 char code
        postal_code: postal code of the person's address
        country: country of the person
        country_code: country code of the person in ISO 2 char code
        title: title of the role that the person holds at the organization they work at
        organization: organization of where the person works
        profiles[]: SocialProfile with service and username and/or userid
    """
    url = f"{API_BASE}/verify"
    data = await make_fideo_request(url, format_request(email, phone, first_name, middle_name,
                                                        last_name, address_line1, address_line2,
                                                        city, region, region_code, postal_code,
                                                        country, country_code,
                                                        birthday, ip_address,
                                                        title, organization))
    if not data:
        return "Error fetching results for verify."

    return "\n---\n" + json.dumps(data)


@mcp.tool()
async def get_signals(email: str, phone: str='', first_name: str='', middle_name: str='', last_name: str='',
                      address_line1: str='', address_line2: str='', city: str='', region: str='',
                      region_code: str='', postal_code: str='', country: str='', country_code: str='',
                      birthday: str='', ip_address: str='', title: str='', organization: str = "",
                      ) -> str:
    """Get Fideo Signals (https://docs.fideo.ai/docs/signals) for a given email, or phone number,
       or name and address. Signals results can contain a variety of information including
       - social media profiles
       - connected emails
       - connected phone numbers
       - their name and potentially aliases
       - professional work history
       - location information of where they live or have lived
       - ip addresses associated with the person
       - economic information such as income brackets and net worth

    Args:
        email: clear text, md5 or sha256 email addressed to lookup representing a person
        phone: clear text, e.164 formatted phone number to lookup representing a person
        first_name: given, or first name of the person
        middle_name: middle name of the person
        last_name: family, or last name of the person
        birthday: Birthday in the form of yyyy-MM-dd, yyyy-MM, MM-dd, yyyy or MM
        ip_address: Current IP address of the person
        address_line1: street level address of the person
        address_line2: extended street level address of the person
        city: city of the person
        region: region, or state of the person in full text
        region_code: region, or state of the person in ISO 2 char code
        postal_code: postal code of the person's address
        country: country of the person
        country_code: country code of the person in ISO 2 char code
        title: title of the role that the person holds at the organization they work at
        organization: organization of where the person works
        profiles[]: SocialProfile with service and username and/or userid
    """
    url = f"{API_BASE}/signals"
    input_payload = format_request(email, phone, first_name, middle_name,
                   last_name, address_line1, address_line2,
                   city, region, region_code, postal_code,
                   country, country_code,
                   birthday, ip_address,
                   title, organization)
    data = await make_fideo_request(url, input_payload)
    if not data:
        return "Error fetching results for Signals."

    return "\n---\n" + json.dumps(data)


async def test():
    """Test function to run the get_signals tool."""
    result = await get_signals('ken.michie@gmail.com', '+19702151708')
    logging.info(result)
    result = await get_verify('ken.michie@gmail.com', '+19702151708')
    logging.info(result)


if __name__ == "__main__":
    # Initialize and run the server
    asyncio.run(test())

    logging.info("Starting fideo-app server")
    mcp.run(transport='stdio')
