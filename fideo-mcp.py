import json
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fideo-mcp")

DEFAULT_API_BASE = "https://api.fideo.ai"
API_BASE = os.getenv("FIDEO_API_BASE", DEFAULT_API_BASE)
FIDEO_API_KEY = os.getenv("FIDEO_API_KEY", "")
USER_AGENT = "fideo-mcp/1.0"

logger = logging.getLogger("fideo_mcp")


def build_request(
    email: str = "",
    phone: str = "",
    first_name: str = "",
    middle_name: str = "",
    last_name: str = "",
    address_line1: str = "",
    address_line2: str = "",
    city: str = "",
    region: str = "",
    region_code: str = "",
    postal_code: str = "",
    country: str = "",
    country_code: str = "",
    birthday: str = "",
    ip_address: str = "",
    title: str = "",
    organization: str = "",
    profiles: list[dict[str, Any]] | None = None,
    social_network: str = "",
    social_id: str = "",
    social_handle: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "email": email,
        "phone": phone,
        "name": {
            "given": first_name,
            "middle": middle_name,
            "family": last_name,
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
        "profiles": profiles or [],
        "birthday": birthday,
        "ipAddress": ip_address,
        "title": title,
        "organization": organization,
    }

    if social_network or social_id or social_handle:
        payload.setdefault("profiles", []).append(
            {
                "service": social_network,
                "userid": social_id,
                "username": social_handle,
            }
        )

    return payload


async def make_fideo_request(url: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {FIDEO_API_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.info("POST %s", url)
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            logger.info("Response status: %s", response.status_code)

            if response.status_code == 204:
                return {"message": "No data found"}

            if response.status_code == 401:
                return {"message": "Authorization expired or invalid API key"}

            if response.status_code not in (200, 201):
                logger.warning("Request failed: %s", response.text)

            response.raise_for_status()
            return response.json()
        except Exception:
            logger.exception("Error making request to %s", url)
            return None


@mcp.tool()
async def get_verify(
    email: str = "",
    phone: str = "",
    first_name: str = "",
    middle_name: str = "",
    last_name: str = "",
    address_line1: str = "",
    address_line2: str = "",
    city: str = "",
    region: str = "",
    region_code: str = "",
    postal_code: str = "",
    country: str = "",
    country_code: str = "",
    birthday: str = "",
    ip_address: str = "",
    job_title: str = "",
    org_name: str = "",
    profiles: list[dict[str, str]] | None = None,
    social_network: str = "",
    social_id: str = "",
    social_handle: str = "",
) -> str:
    """Call Fideo Verify for a risk score and check-by-check findings.

    Use this tool when you need a fraud or compliance risk assessment about an individual. Supply
    any identifiers you have; at least one of email, phone, name plus address, IP address, or social
    profile is required for Verify to run a search. Additional context improves match accuracy.

    Args describe clear-text values unless noted (emails may also be MD5/SHA256 hashes, phones must
    be E.164). Optional identity, address, employment, and social profile fields help Verify link
    the correct person. The response is returned as a JSON string prefixed with ``---`` so clients
    can stream the raw payload.
    """

    payload = build_request(
        email=email,
        phone=phone,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        region=region,
        region_code=region_code,
        postal_code=postal_code,
        country=country,
        country_code=country_code,
        birthday=birthday,
        ip_address=ip_address,
        title=job_title,
        organization=org_name,
        profiles=profiles,
        social_network=social_network,
        social_id=social_id,
        social_handle=social_handle,
    )

    data = await make_fideo_request(f"{API_BASE}/verify", payload)
    if data is None:
        return "Error fetching results for Verify."

    return "\n---\n" + json.dumps(data)


@mcp.tool()
async def get_signals(
    email: str = "",
    phone: str = "",
    first_name: str = "",
    middle_name: str = "",
    last_name: str = "",
    address_line1: str = "",
    address_line2: str = "",
    city: str = "",
    region: str = "",
    region_code: str = "",
    postal_code: str = "",
    country: str = "",
    country_code: str = "",
    birthday: str = "",
    ip_address: str = "",
    job_title: str = "",
    org_name: str = "",
    profiles: list[dict[str, str]] | None = None,
    social_network: str = "",
    social_id: str = "",
    social_handle: str = "",
) -> str:
    """Retrieve Fideo Signals profile intelligence about a person.

    Provide whichever identifiers are available (email, phone, name + address, IP, or social
    profile). Signals enriches the person with linked identities, locations, work history, and
    digital footprint information. Returns a JSON string prefixed with ``---`` containing the API
    response.
    """

    payload = build_request(
        email=email,
        phone=phone,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        region=region,
        region_code=region_code,
        postal_code=postal_code,
        country=country,
        country_code=country_code,
        birthday=birthday,
        ip_address=ip_address,
        title=job_title,
        organization=org_name,
        profiles=profiles,
        social_network=social_network,
        social_id=social_id,
        social_handle=social_handle,
    )

    data = await make_fideo_request(f"{API_BASE}/signals", payload)
    if data is None:
        return "Error fetching results for Signals."

    return "\n---\n" + json.dumps(data)


if __name__ == "__main__":
    logger.info("Starting fideo-mcp server")
    mcp.run(transport="stdio")
