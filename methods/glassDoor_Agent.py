from urllib.parse import quote_plus, urljoin
from playwright.sync_api import (sync_playwright,TimeoutError as PlaywrightTimeoutError)
import re
DEBUGGING_URL = "http://127.0.0.1:9222"

def getGlassData(title, city, state):
    maximum_results = 10
    location_query = f"{city}, {state}"

    search_url = (
        "https://www.glassdoor.com/Job/jobs.htm"
        f"?sc.keyword={quote_plus(title.strip())}"
        f"&locKeyword={quote_plus(location_query)}"
    )

    job_card_selector = (
        'li[data-test="jobListing"], '
        'li[data-test="job-listing"], '
        '[data-test="job-card"], '
        'li[class*="JobsList_jobListItem"], '
        'article[id*="job"]'
    )

    description_selectors = [
        '[data-test="jobDescriptionContent"]',
        '[data-test="job-description"]',
        "#JobDescriptionContainer",
        ".jobDescriptionContent",
        '[class*="JobDetails_jobDescription"]',
        '[class*="JobDescription_jobDescription"]',
        '[class*="jobDescription"]',
    ]

    def normalize(value):
        return re.sub(
            r"[^a-z0-9]+",
            " ",
            value.lower(),
        ).strip()

    def title_matches(requested_title, result_title):
        requested_words = set(
            normalize(requested_title).split()
        )
        result_words = set(
            normalize(result_title).split()
        )

        return (
            bool(requested_words)
            and requested_words.issubset(result_words)
        )

    def first_text(parent, selectors):
        for selector in selectors:
            elements = parent.locator(selector)

            for index in range(elements.count()):
                element = elements.nth(index)

                try:
                    text = element.inner_text(
                        timeout=3_000
                    ).strip()

                    if text:
                        return text
                except Exception:
                    continue

        return ""

    def close_modal(page):
        close_selectors = [
            'button[data-test="modal-close-button"]',
            'button[aria-label="Close"]',
            'button[aria-label="close"]',
        ]

        for selector in close_selectors:
            buttons = page.locator(selector)

            for index in range(buttons.count()):
                button = buttons.nth(index)

                try:
                    if button.is_visible():
                        button.click()
                        page.wait_for_timeout(300)
                        return
                except Exception:
                    continue

    def expand_description(page):
        show_more_selectors = [
            (
                'button[data-test='
                '"show-more-job-description"]'
            ),
            (
                'button[aria-label*='
                '"show more description" i]'
            ),
            (
                'button[aria-label*='
                '"see more description" i]'
            ),
            '[class*="JobDetails_showMore"]',
        ]

        for selector in show_more_selectors:
            buttons = page.locator(selector)

            for index in range(buttons.count()):
                button = buttons.nth(index)

                try:
                    if button.is_visible():
                        button.click()
                        page.wait_for_timeout(500)
                        return
                except Exception:
                    continue

    def extract_description(page):
        candidates = []

        for selector in description_selectors:
            elements = page.locator(selector)

            for index in range(elements.count()):
                element = elements.nth(index)

                try:
                    if not element.is_visible():
                        continue

                    text = element.inner_text(
                        timeout=5_000
                    ).strip()

                    if len(text) < 100:
                        continue

                    html = element.inner_html(
                        timeout=5_000
                    ).strip()

                    candidates.append(
                        {
                            "text": text,
                            "html": html,
                        }
                    )

                except Exception:
                    continue

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda candidate: len(candidate["text"]),
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

        search_page = next(
            (
                page
                for page in context.pages
                if "glassdoor.com/Job/" in page.url
            ),
            None,
        )

        if search_page is None:
            search_page = context.new_page()

        search_page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        search_page.bring_to_front()
        close_modal(search_page)

        if (
            "/auth/" in search_page.url
            or "/profile/login" in search_page.url
        ):
            raise RuntimeError(
                "Glassdoor requires authentication. Log in manually "
                "in Chrome and run the function again."
            )

        try:
            search_page.locator(
                job_card_selector
            ).first.wait_for(
                state="attached",
                timeout=30_000,
            )
        except PlaywrightTimeoutError:
            return []

        matches = []
        seen_jobs = set()

        for _ in range(12):
            job_cards = search_page.locator(
                job_card_selector
            )

            for index in range(job_cards.count()):
                card = job_cards.nth(index)

                job_title = first_text(
                    card,
                    [
                        'a[data-test="job-title"]',
                        'a[id^="job-title"]',
                        '[data-test="job-title"]',
                        'a[href*="/job-listing/"]',
                        "h2",
                    ],
                )

                if not job_title:
                    continue

                if not title_matches(title, job_title):
                    continue

                company = first_text(
                    card,
                    [
                        '[data-test="employer-name"]',
                        '[data-test="employerName"]',
                        (
                            '[class*="EmployerProfile_'
                            'employerName"]'
                        ),
                        (
                            '[class*="EmployerProfile_'
                            'compactEmployerName"]'
                        ),
                    ],
                )

                company = re.sub(
                    r"\s+\d(?:\.\d+)?\s*$",
                    "",
                    company,
                ).strip()

                job_location = first_text(
                    card,
                    [
                        '[data-test="emp-location"]',
                        '[data-test="job-location"]',
                        '[class*="JobCard_location"]',
                    ],
                )

                salary = first_text(
                    card,
                    [
                        '[data-test="detailSalary"]',
                        '[data-test="job-salary"]',
                        '[class*="salaryEstimate"]',
                    ],
                )

                description_preview = first_text(
                    card,
                    [
                        '[data-test="job-description"]',
                        (
                            '[class*="JobCard_'
                            'jobDescriptionSnippet"]'
                        ),
                    ],
                )

                job_link = card.locator(
                    'a[data-test="job-title"], '
                    'a[href*="/job-listing/"], '
                    'a[href*="/partner/jobListing"]'
                ).first

                job_url = ""

                if job_link.count() > 0:
                    href = job_link.get_attribute("href")

                    if href:
                        job_url = urljoin(
                            "https://www.glassdoor.com",
                            href,
                        )

                unique_key = (
                    job_url
                    or (
                        f"{normalize(company)}:"
                        f"{normalize(job_title)}:"
                        f"{normalize(job_location)}"
                    )
                )

                if unique_key in seen_jobs:
                    continue

                seen_jobs.add(unique_key)

                matches.append(
                    {
                        "title": job_title,
                        "company": company,
                        "location": job_location,
                        "salary": salary,
                        "url": job_url,
                        "description": description_preview,
                        "description_html": "",
                    }
                )

                if len(matches) >= maximum_results:
                    break

            if len(matches) >= maximum_results:
                break

            search_page.mouse.wheel(0, 1800)
            search_page.wait_for_timeout(1_000)

        if not matches:
            return []

        detail_page = context.new_page()

        try:
            for number, job in enumerate(matches, start=1):
                job_url = job["url"]

                if not job_url:
                    job["description_error"] = (
                        "The job did not have a usable URL."
                    )
                    continue

                print(
                    f"Collecting Glassdoor description "
                    f"{number}/{len(matches)}: {job['title']}"
                )

                try:
                    detail_page.goto(
                        job_url,
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )

                    close_modal(detail_page)

                    try:
                        detail_page.locator(
                            ", ".join(description_selectors)
                        ).first.wait_for(
                            state="attached",
                            timeout=20_000,
                        )
                    except PlaywrightTimeoutError:
                        pass

                    expand_description(detail_page)

                    full_description = extract_description(
                        detail_page
                    )

                    if full_description:
                        job["description"] = (
                            full_description["text"]
                        )
                        job["description_html"] = (
                            full_description["html"]
                        )
                    elif not job["description"]:
                        job["description_error"] = (
                            "The description element was not found."
                        )

                except Exception as error:
                    job["description_error"] = str(error)

        finally:
            detail_page.close()

        return matches


def checkJob(
    company_name: str,
    position_title: str,
) -> list[dict]:
    maximum_results = 10

    def normalize(value):
        return re.sub(
            r"[^a-z0-9]+",
            " ",
            value.lower(),
        ).strip()

    def words_match(requested, actual):
        requested_words = set(normalize(requested).split())
        actual_words = set(normalize(actual).split())

        return bool(requested_words) and requested_words.issubset(
            actual_words
        )

    def first_text(parent, selectors):
        for selector in selectors:
            elements = parent.locator(selector)

            for index in range(elements.count()):
                element = elements.nth(index)

                try:
                    text = element.inner_text(
                        timeout=3_000
                    ).strip()

                    if text:
                        return text
                except Exception:
                    continue

        return ""

    query = quote_plus(
        f"{position_title.strip()} {company_name.strip()}"
    )

    search_url = (
        "https://www.glassdoor.com/Job/jobs.htm"
        f"?sc.keyword={query}"
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
                if "glassdoor.com/Job/" in current_page.url
            ),
            None,
        )

        if page is None:
            page = context.new_page()

        page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.bring_to_front()

        if (
            "/auth/" in page.url
            or "/profile/login" in page.url
        ):
            raise RuntimeError(
                "Glassdoor requires authentication. Log in manually "
                "in the opened Chrome window and run the function again."
            )

        modal_close_selectors = [
            'button[data-test="modal-close-button"]',
            'button[aria-label="Close"]',
            'button[aria-label="close"]',
        ]

        for selector in modal_close_selectors:
            buttons = page.locator(selector)

            for index in range(buttons.count()):
                button = buttons.nth(index)

                try:
                    if button.is_visible():
                        button.click()
                        page.wait_for_timeout(300)
                        break
                except Exception:
                    continue

        job_card_selector = (
            'li[data-test="jobListing"], '
            'li[data-test="job-listing"], '
            '[data-test="job-card"], '
            'li[class*="JobsList_jobListItem"], '
            'article[id*="job"]'
        )

        try:
            page.locator(job_card_selector).first.wait_for(
                state="attached",
                timeout=30_000,
            )
        except PlaywrightTimeoutError:
            return []

        matches = []
        seen_jobs = set()


        for _ in range(12):
            job_cards = page.locator(job_card_selector)

            for index in range(job_cards.count()):
                card = job_cards.nth(index)

                title = first_text(
                    card,
                    [
                        'a[data-test="job-title"]',
                        'a[id^="job-title"]',
                        '[data-test="job-title"]',
                        'a[href*="/job-listing/"]',
                        "h2",
                    ],
                )

                company = first_text(
                    card,
                    [
                        '[data-test="employer-name"]',
                        '[data-test="employerName"]',
                        (
                            '[class*="EmployerProfile_'
                            'employerName"]'
                        ),
                        (
                            '[class*="EmployerProfile_'
                            'compactEmployerName"]'
                        ),
                    ],
                )

                if not title or not company:
                    continue


                company = re.sub(
                    r"\s+\d(?:\.\d+)?\s*$",
                    "",
                    company,
                ).strip()

                if not words_match(position_title, title):
                    continue

                if not words_match(company_name, company):
                    continue

                job_link = card.locator(
                    'a[data-test="job-title"], '
                    'a[href*="/job-listing/"], '
                    'a[href*="/partner/jobListing"]'
                ).first

                job_url = ""

                if job_link.count() > 0:
                    href = job_link.get_attribute("href")

                    if href:
                        job_url = urljoin(
                            "https://www.glassdoor.com",
                            href,
                        )

                location = first_text(
                    card,
                    [
                        '[data-test="emp-location"]',
                        '[data-test="job-location"]',
                        '[class*="JobCard_location"]',
                    ],
                )

                salary = first_text(
                    card,
                    [
                        '[data-test="detailSalary"]',
                        '[data-test="job-salary"]',
                        '[class*="salaryEstimate"]',
                    ],
                )

                description_preview = first_text(
                    card,
                    [
                        '[data-test="job-description"]',
                        (
                            '[class*="JobCard_'
                            'jobDescriptionSnippet"]'
                        ),
                    ],
                )

                unique_key = (
                    job_url
                    or f"{normalize(company)}:{normalize(title)}"
                )

                if unique_key in seen_jobs:
                    continue

                seen_jobs.add(unique_key)

                matches.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": salary,
                        "url": job_url,
                        "description": description_preview,
                    }
                )

                if len(matches) >= maximum_results:
                    break

            if len(matches) >= maximum_results:
                break

            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(1_000)

        return matches


if __name__ == "__main__":
    testTitle = "Amicis Global"
    testCity = "Atlanta"
    testState = "Georgia"
    getGlassData(testTitle,testCity,testState)
    

