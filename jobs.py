import os

import requests
from dotenv import load_dotenv


class JobSearchError(Exception):
    """Raised when the job search service cannot complete a request."""


load_dotenv()


def search_jobs(keyword, location, page_number=1):
    # Read credentials from .env
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    # Check that both credentials exist
    if not app_id or not app_key:
        raise JobSearchError("Internship search is not configured right now.")

    # Build the Adzuna endpoint URL
    country_code = "us"
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

    # Send GET request with a timeout and check HTTP status
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.Timeout as error:
        raise JobSearchError(
            "The internship search took too long. Please try again."
        ) from error
    except requests.ConnectionError as error:
        raise JobSearchError(
            "Could not connect to the internship search service."
        ) from error
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else None

        if status_code in [401, 403]:
            message = (
                "Internship search is temporarily unavailable because "
                "the service could not authorize the request."
            )
        elif status_code == 429:
            message = "Too many searches were made. Please wait and try again."
        elif status_code is not None and 500 <= status_code < 600:
            message = (
                "The internship search service is temporarily unavailable. "
                "Please try again shortly."
            )
        else:
            message = "The internship search service returned an error."

        raise JobSearchError(message) from error
    except requests.RequestException as error:
        raise JobSearchError(
            "Something went wrong while searching for internships."
        ) from error

    # Convert response to JSON
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise JobSearchError(
            "The internship search service returned an invalid response."
        ) from error
    total_results = data.get("count", 0)

    # Normalizing the results to ensure consistent structure
    normalized_jobs = []
    for raw_job in data.get("results", []):
        external_id = raw_job.get("id")
        if external_id is None or not str(external_id).strip():
            continue

        normalized_job = {
            "external_id": str(external_id).strip(),
            "title": raw_job.get("title", "Untitled position"),
            # Nested company dictionary
            "company": raw_job.get("company", {}).get(
                "display_name", "Unknown company"
            ),
            # Nested location dictionary
            "location": raw_job.get("location", {}).get(
                "display_name", "Location unavailable"
            ),
            "description": raw_job.get("description", "No description provided"),
            "apply_url": raw_job.get("redirect_url") or None,
            "posted_at": raw_job.get("created", "Date not available"),
        }
        normalized_jobs.append(normalized_job)

    # Return results
    return normalized_jobs, total_results
