import os

import requests
from dotenv import load_dotenv


load_dotenv()


def search_jobs(keyword, location):
    # Read credentials from .env
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    # Check that both credentials exist
    if not app_id or not app_key:
        raise ValueError("Missing Adzuna credentials in .env file")

    # Build the Adzuna endpoint URL
    country_code = "us"
    page_number = 1
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page_number}"

    # Build query parameters
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 10,
        "what": keyword,
    }
    # Add location only when provided
    if location:
        params["where"] = location
    # Send GET request with a timeout
    response = requests.get(url, params=params, timeout=10)
    # Check HTTP status
    response.raise_for_status()

    # Convert response to JSON
    data = response.json()
    # Normalizing the results to ensure consistent structure
    normalized_jobs = []
    for raw_job in data.get("results", []):
        normalized_job = {
            "external_id": raw_job.get("id"),
            "title": raw_job.get("title", "Untitled position"),

            # Nested company dictionary
            "company": raw_job.get("company", {}).get(
                "display_name",
                "Unknown company"
            ),

            # Nested location dictionary
            "location": raw_job.get("location", {}).get(
                "display_name",
                "Location unavailable"
            ),

            "description": raw_job.get("description", "No description provided"),
            "apply_url": raw_job.get("redirect_url", "None  "),
            "posted_at": raw_job.get("created", "Date not available")
        }
        normalized_jobs.append(normalized_job)

    # Return results
    return normalized_jobs