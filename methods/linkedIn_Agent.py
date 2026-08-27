import asyncio
import socket
import subprocess
import time
import os
import re
from urllib.parse import quote_plus, urljoin
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import urllib.parse
from urllib.parse import quote_plus, urljoin
from playwright.sync_api import (sync_playwright,TimeoutError as PlaywrightTimeoutError)

from playwright.async_api import (
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

CHROME_PATH = (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
CHROME_PROFILE = (r"C:\Users\Acey\Downloads\Dove Agent Build"
                  r"\Agent Modules\Chrome_Agent"
)
DEBUGGING_HOST = "127.0.0.1"
DEBUGGING_PORT = 9222
DEBUGGING_URL = f"http://{DEBUGGING_HOST}:{DEBUGGING_PORT}"

linkArray = {
        "atlanta, georgia": "90000052",
        "new york, new york": "102571732",
        "chicago, illinois": "103112676",
        "dallas, texas": "104194190"
    }


cityCoordsMap = {
        "atlanta, georgia": (33.7489, -84.3903),
        "new york, new york": (40.7128, -74.0060),
        "chicago, illinois": (41.8781, -87.6298),
        "dallas, texas": (32.7767, -96.7970)
    }
username = 'datasetprepper@gmail.com'
password = 'one2three!'

def getLinkedData(city, state, title):
    geolocator = Nominatim(user_agent="my_application")
    address = f"{city}, {state}".strip().lower()
    location = geolocator.geocode(address)

    if not location:
        return None

    if address in cityCoordsMap:
        user_city = address
    else:
        user_city, _, _ = findLoc(location)

    return runLinkedScraper(title, user_city)


def findLoc(location):
    user_coords = (location.latitude, location.longitude)
    minimum_distance = float("inf")
    closest_city = None

    for city_name, coordinates in cityCoordsMap.items():
        distance = geodesic(user_coords, coordinates).miles

        if distance < minimum_distance:
            minimum_distance = distance
            closest_city = city_name

    return (
        closest_city,
        linkArray[closest_city],
        minimum_distance,
    )

def runLinkedScraper(title, userCity):
    def debugging_port_is_open():
        try:
            with socket.create_connection(
                (DEBUGGING_HOST, DEBUGGING_PORT),
                timeout=1,
            ):
                return True
        except OSError:
            return False

    if not debugging_port_is_open():
        subprocess.Popen(
            [
                CHROME_PATH,
                f"--remote-debugging-address={DEBUGGING_HOST}",
                f"--remote-debugging-port={DEBUGGING_PORT}",
                f"--user-data-dir={CHROME_PROFILE}",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + 20

        while time.time() < deadline:
            if debugging_port_is_open():
                break

            time.sleep(0.25)
        else:
            raise RuntimeError(
                f"Chrome did not open debugging port {DEBUGGING_PORT}."
            )

    normalized_city = userCity.strip().lower()

    if normalized_city not in linkArray:
        available_locations = ", ".join(linkArray.keys())

        raise ValueError(
            f'No LinkedIn geoId is configured for "{userCity}". '
            f"Available locations: {available_locations}"
        )

    geo_id = linkArray[normalized_city]
    query = quote_plus(title.strip())

    jobs_url = (
        "https://www.linkedin.com/jobs/search/"
        f"?geoId={geo_id}"
        f"&keywords={query}"
        "&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON"
        "&refresh=true"
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(
            DEBUGGING_URL
        )

        if not browser.contexts:
            raise RuntimeError(
                "Chrome is connected, but no browser context was found."
            )

        context = browser.contexts[0]

        page = next(
            (
                current_page
                for current_page in context.pages
                if "linkedin.com" in current_page.url
            ),
            None,
        )

        if page is None:
            page = context.new_page()

        page.goto(
            "https://www.linkedin.com/feed/",
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        username_input = page.locator("input#username")

        login_required = (
            "/login" in page.url
            or (
                username_input.count() > 0
                and username_input.first.is_visible()
            )
        )

        if login_required:
            username = 'datasetprepper@gmail.com'
            password = 'one2three!'

            if not username or not password:
                raise RuntimeError(
                    "LinkedIn login is required. Set LINKEDIN_USERNAME "
                    "and LINKEDIN_PASSWORD before running the script."
                )

            page.goto(
                "https://www.linkedin.com/login",
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            page.locator("input#username").fill(username)
            page.locator("input#password").fill(password)
            page.locator('button[type="submit"]').click()

            try:
                page.wait_for_url(
                    re.compile(
                        r"https://(?:www\.)?linkedin\.com/(?!login).*"
                    ),
                    timeout=60_000,
                )
            except PlaywrightTimeoutError:
                pass

            page.wait_for_timeout(1_000)

            if "/checkpoint/" in page.url or "/challenge/" in page.url:
                raise RuntimeError(
                    "LinkedIn requires manual verification. Complete "
                    "the verification in Chrome and run the script again."
                )

            if "/login" in page.url:
                raise RuntimeError(
                    "LinkedIn login failed. Check your credentials."
                )

        page.goto(
            jobs_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.bring_to_front()

        try:
            page.locator(
                'a[href*="/jobs/view/"]'
            ).first.wait_for(
                state="attached",
                timeout=20_000,
            )
        except PlaywrightTimeoutError:
            pass

        print(f"LinkedIn search opened: {page.url}")
        return page.url
    
    
def collectInfo():
    maximum_jobs = 10

    def first_visible_text(page, selectors):
        for selector in selectors:
            matches = page.locator(selector)

            for index in range(matches.count()):
                element = matches.nth(index)

                try:
                    if element.is_visible():
                        text = element.inner_text(
                            timeout=5_000
                        ).strip()

                        if text:
                            return text
                except Exception:
                    continue

        return None

    def click_show_more(page):
        selectors = [
            'button[aria-label*="see more description" i]',
            'button[aria-label*="show more" i]',
            ".jobs-description__footer-button",
        ]

        for selector in selectors:
            buttons = page.locator(selector)

            for index in range(buttons.count()):
                button = buttons.nth(index)

                try:
                    if button.is_visible():
                        button.click()
                        page.wait_for_timeout(500)
                        return True
                except Exception:
                    continue

        return False

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(
            DEBUGGING_URL
        )

        if not browser.contexts:
            raise RuntimeError(
                "Chrome is connected, but no browser context was found."
            )

        context = browser.contexts[0]

        search_page = next(
            (
                page
                for page in reversed(context.pages)
                if "linkedin.com/jobs/search" in page.url
            ),
            None,
        )

        if search_page is None:
            raise RuntimeError(
                "No LinkedIn search page was found. "
                "Call runLinkedScraper() first."
            )

        search_page.bring_to_front()
        search_page.wait_for_load_state("domcontentloaded")

        try:
            search_page.locator(
                'a[href*="/jobs/view/"]'
            ).first.wait_for(
                state="attached",
                timeout=20_000,
            )
        except PlaywrightTimeoutError:
            pass

        results_container = None

        container_selectors = [
            ".jobs-search-results-list",
            ".scaffold-layout__list-container",
            ".jobs-search-results-list__list",
        ]

        for selector in container_selectors:
            locator = search_page.locator(selector)

            try:
                if (
                    locator.count() > 0
                    and locator.first.is_visible()
                ):
                    results_container = locator.first
                    break
            except Exception:
                continue

        job_entries = []
        seen_job_ids = set()

        for _ in range(15):
            if results_container is not None:
                job_links = results_container.locator(
                    'a[href*="/jobs/view/"]'
                )
            else:
                job_links = search_page.locator(
                    'a[href*="/jobs/view/"]'
                )

            for index in range(job_links.count()):
                link = job_links.nth(index)

                try:
                    href = link.get_attribute("href")

                    if not href:
                        continue

                    match = re.search(
                        r"/jobs/view/(?:[^/?]*-)?(\d+)",
                        href,
                    )

                    if not match:
                        continue

                    job_id = match.group(1)

                    if job_id in seen_job_ids:
                        continue

                    seen_job_ids.add(job_id)

                    title = link.inner_text().strip()

                    job_entries.append(
                        {
                            "job_id": job_id,
                            "job_title": title,
                            "job_url": (
                                "https://www.linkedin.com/jobs/view/"
                                f"{job_id}/"
                            ),
                        }
                    )

                    if len(job_entries) >= maximum_jobs:
                        break

                except Exception:
                    continue

            if len(job_entries) >= maximum_jobs:
                break

            if results_container is not None:
                results_container.evaluate(
                    """
                    element => {
                        element.scrollTop = element.scrollHeight;
                    }
                    """
                )
            else:
                search_page.mouse.wheel(0, 1500)

            search_page.wait_for_timeout(1_000)

        if not job_entries:
            raise RuntimeError(
                "No job entries were found on the LinkedIn search page."
            )

        job_entries = job_entries[:maximum_jobs]
        collected_information = []
        detail_page = context.new_page()

        try:
            for position, job in enumerate(
                job_entries,
                start=1,
            ):
                try:
                    detail_page.goto(
                        job["job_url"],
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )

                    try:
                        detail_page.locator(
                            "#job-details, "
                            ".jobs-box__html-content, "
                            ".jobs-description-content__text, "
                            ".jobs-description__content, "
                            ".description__text, "
                            'main p[dir="ltr"], '
                            'p[dir="ltr"]'
                        ).first.wait_for(
                            state="attached",
                            timeout=20_000,
                        )
                    except PlaywrightTimeoutError:
                        pass

                    click_show_more(detail_page)

                    company_name = first_visible_text(
                        detail_page,
                        [
                            (
                                ".job-details-jobs-unified-top-card"
                                "__company-name a"
                            ),
                            (
                                ".job-details-jobs-unified-top-card"
                                "__company-name"
                            ),
                            (
                                ".jobs-unified-top-card"
                                "__company-name a"
                            ),
                            (
                                ".jobs-unified-top-card"
                                "__company-name"
                            ),
                            ".topcard__org-name-link",
                            "main a[href*='/company/']",
                        ],
                    )

                    job_title = first_visible_text(
                        detail_page,
                        [
                            (
                                ".job-details-jobs-unified-top-card"
                                "__job-title h1"
                            ),
                            (
                                ".job-details-jobs-unified-top-card"
                                "__job-title"
                            ),
                            (
                                ".jobs-unified-top-card"
                                "__job-title"
                            ),
                            ".top-card-layout__title",
                            "main h1",
                        ],
                    )

                    job_description = extract_job_description(
                        detail_page
                    )

                    collected_information.append(
                        {
                            "position": position,
                            "job_title": (
                                job_title
                                or job["job_title"]
                                or None
                            ),
                            "company_name": company_name,
                            "job_description": job_description,
                            "job_url": job["job_url"],
                        }
                    )

                except Exception as error:
                    collected_information.append(
                        {
                            "position": position,
                            "job_title": (
                                job["job_title"] or None
                            ),
                            "company_name": None,
                            "job_description": None,
                            "job_url": job["job_url"],
                            "error": str(error),
                        }
                    )

        finally:
            detail_page.close()

        return collected_information
    
def extract_job_description(page):
    description_selectors = [
        "#job-details",
        ".jobs-box__html-content",
        ".jobs-description-content__text",
        ".jobs-description__content",
        ".description__text",
        'main p[dir="ltr"]',
        'p[dir="ltr"]',
    ]

    candidates = []

    for selector in description_selectors:
        elements = page.locator(selector)

        for index in range(elements.count()):
            element = elements.nth(index)

            try:
                text = element.inner_text(
                    timeout=5_000
                ).strip()

                if len(text) >= 200:
                    text = re.sub(
                        r"\n{3,}",
                        "\n\n",
                        text,
                    )
                    candidates.append(text)

            except Exception:
                continue

    if not candidates:
        return None

    return max(candidates, key=len)   
    
    
if __name__ == "__main__":
    runLinkedScraper("Software Engineer","Atlanta, Georgia",)

    jobs = collectInfo()

