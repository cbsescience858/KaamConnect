import time
import logging
from typing import Dict, List, Any

import requests

# Prefer a static generated mapping when available
try:
    from app.services.india_districts import STATE_DISTRICTS as STATIC_DISTRICTS
except Exception:
    STATIC_DISTRICTS = None

logger = logging.getLogger(__name__)

REMOTE_STATES_URL = "https://igod.gov.in/sg/district/states"
_CACHE: Dict[str, Any] = {"data": None, "ts": 0.0}
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours

# Minimal local fallback. Extend as needed.
LOCAL_DISTRICTS: Dict[str, List[str]] = {
    "Maharashtra": [
        "Mumbai", "Mumbai Suburban", "Pune", "Nagpur", "Thane", "Nashik", "Aurangabad", "Kolhapur"
    ],
    "Karnataka": [
        "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru", "Belagavi", "Hubballi-Dharwad"
    ],
    "Delhi": [
        "New Delhi", "South Delhi", "North Delhi", "West Delhi", "East Delhi"
    ],
    "Uttar Pradesh": [
        "Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Ghaziabad", "Noida", "Agra"
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"
    ],
    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"
    ],
    "West Bengal": [
        "Kolkata", "Howrah", "Darjeeling", "Siliguri"
    ],
    "Rajasthan": [
        "Jaipur", "Jodhpur", "Udaipur", "Kota"
    ],
    "Bihar": [
        "Patna", "Gaya", "Bhagalpur"
    ],
    "Telangana": [
        "Hyderabad", "Warangal", "Nalgonda"
    ],
    "Kerala": [
        "Thiruvananthapuram", "Kochi", "Kozhikode"
    ],
    "Madhya Pradesh": [
        "Bhopal", "Indore", "Jabalpur", "Gwalior"
    ],
    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur"
    ],
    "Punjab": [
        "Amritsar", "Ludhiana", "Jalandhar"
    ],
    "Haryana": [
        "Gurugram", "Faridabad", "Panipat"
    ],
}


def _normalize_payload(data: Any) -> Dict[str, List[str]]:
    """Try to normalize remote payload into {state: [districts..]} mapping."""
    mapping: Dict[str, List[str]] = {}
    try:
        if isinstance(data, dict):
            # Direct mapping
            for k, v in data.items():
                if isinstance(v, list):
                    mapping[str(k)] = [str(x) for x in v]
            # Nested list under 'states'
            if not mapping and isinstance(data.get("states"), list):
                for item in data["states"]:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("state") or item.get("state_name") or item.get("name")
                    if not isinstance(name, str):
                        continue
                    dlist = item.get("districts") or item.get("district") or item.get("children") or []
                    districts: List[str] = []
                    for d in dlist:
                        if isinstance(d, dict):
                            nm = d.get("name") or d.get("district_name") or d.get("district")
                            if nm:
                                districts.append(str(nm))
                        else:
                            districts.append(str(d))
                    mapping[name] = districts
        elif isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                name = item.get("state") or item.get("state_name") or item.get("name")
                if not isinstance(name, str):
                    continue
                dlist = item.get("districts") or item.get("district") or item.get("children") or []
                districts: List[str] = []
                for d in dlist:
                    if isinstance(d, dict):
                        nm = d.get("name") or d.get("district_name") or d.get("district")
                        if nm:
                            districts.append(str(nm))
                    else:
                        districts.append(str(d))
                mapping[name] = districts
    except Exception as e:
        logger.warning(f"Failed to normalize districts payload: {e}")
    return mapping


def _fetch_remote_map(timeout: int = 10) -> Dict[str, List[str]]:
    try:
        resp = requests.get(REMOTE_STATES_URL, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        mapping = _normalize_payload(data)
        return mapping
    except Exception as e:
        logger.warning(f"Fetching remote districts failed: {e}")
        return {}


def get_state_districts_map(force_refresh: bool = False) -> Dict[str, List[str]]:
    # If a static snapshot exists, always use it
    if isinstance(STATIC_DISTRICTS, dict) and STATIC_DISTRICTS:
        return STATIC_DISTRICTS

    now = time.time()
    data = _CACHE.get("data")
    ts = _CACHE.get("ts", 0.0)
    if force_refresh or not isinstance(data, dict) or (now - ts) > CACHE_TTL_SECONDS:
        mapping = _fetch_remote_map()
        if mapping:
            _CACHE["data"] = mapping
            _CACHE["ts"] = now
            return mapping
        # Remote failed, keep existing cache if valid
        if isinstance(data, dict):
            return data
        return LOCAL_DISTRICTS
    return data


def get_districts(state: str, force_refresh: bool = False) -> List[str]:
    if not isinstance(state, str) or not state.strip():
        return []
    mapping = get_state_districts_map(force_refresh=force_refresh)
    # Case-insensitive state match
    s_norm = state.strip().lower()
    for k, v in mapping.items():
        if isinstance(k, str) and k.strip().lower() == s_norm and isinstance(v, list):
            return [str(x) for x in v]
    # Fallback if not found
    return []
