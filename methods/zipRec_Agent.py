from urllib.parse import quote_plus, urljoin
from playwright.sync_api import (sync_playwright,TimeoutError as PlaywrightTimeoutError)


def getData(title, city, state):
    results = []

    location = f"{city}, {state}"

    search_url = (
        "https://www.ziprecruiter.com/jobs-search"
        "?form=jobs-landing"
        f"&search={quote_plus(title)}"
        f"&location={quote_plus(location)}"
    )

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(
            "http://**.*.*.*:9222"
        )

        if not browser.contexts:
            raise RuntimeError(
                "Chrome is connected, but no browser context was found."
            )

        context = browser.contexts[0]
        search_page = None

        for current_page in context.pages:
            if current_page.url.startswith(
                "https://www.ziprecruiter.com/jobs-search"
            ):
                search_page = current_page
                break

        if search_page is None:
            search_page = context.new_page()

        search_page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60_000
        )

        search_page.bring_to_front()

        job_card_selector = (
            'section[aria-label="Job listings"] '
            'article[id^="job-card-"]'
        )

        description_selector = (
            'div.text-primary.whitespace-pre-line.wrap-anywhere'
        )

        company_selector = (
            'a[href^="/co/"][aria-label]'
        )

        try:
            search_page.wait_for_selector(
                job_card_selector,
                timeout=30_000
            )

        except PlaywrightTimeoutError:
            print("Could not find any job cards.")
            return results

        job_cards = search_page.locator(job_card_selector)
        card_count = job_cards.count()

        print(f"Job-card elements found: {card_count}")

        processed_card_ids = set()

        for index in range(card_count):
            if len(results) >= 20:
                break


            job_cards = search_page.locator(job_card_selector)

            if index >= job_cards.count():
                break

            card = job_cards.nth(index)
            card_id = card.get_attribute("id")

            if card_id and card_id in processed_card_ids:
                continue

            if card_id:
                processed_card_ids.add(card_id)

            title_element = card.locator(
                'h2[aria-label]'
            ).first

            if title_element.count() == 0:
                continue

            job_title = title_element.get_attribute(
                "aria-label"
            )

            if not job_title:
                job_title = title_element.inner_text()

            job_title = job_title.strip()

            job_url = ""

            job_link = card.locator(
                'a[href]'
            ).first

            if job_link.count() > 0:
                href = job_link.get_attribute("href")

                if href:
                    job_url = urljoin(
                        "https://www.ziprecruiter.com",
                        href
                    )

            old_description = ""

            existing_descriptions = search_page.locator(
                description_selector
            )

            if existing_descriptions.count() > 0:
                try:
                    old_description = (
                        existing_descriptions
                        .last
                        .inner_text()
                        .strip()
                    )
                except Exception:
                    old_description = ""

            view_button = card.locator(
                'button[aria-label^="View "]'
            ).first

            if view_button.count() == 0:
                if job_link.count() > 0:
                    clickable_element = job_link
                else:
                    print(
                        f"No clickable element found for: "
                        f"{job_title}"
                    )
                    continue
            else:
                clickable_element = view_button

            print(
                f"Gathering {len(results) + 1}/20: "
                f"{job_title}"
            )

            try:
                clickable_element.scroll_into_view_if_needed()
                clickable_element.click(
                    timeout=15_000
                )

            except PlaywrightTimeoutError:
                print(f"Could not click: {job_title}")
                continue

            description = ""
            description_html = ""
            company = ""

            try:
                search_page.wait_for_function(
                    """
                    ({ selector, oldText }) => {
                        const elements =
                            document.querySelectorAll(selector);

                        if (!elements.length) {
                            return false;
                        }

                        const visibleElements =
                            Array.from(elements).filter(
                                element => {
                                    const style =
                                        window.getComputedStyle(
                                            element
                                        );

                                    return (
                                        style.display !== "none" &&
                                        style.visibility !== "hidden" &&
                                        element
                                            .getBoundingClientRect()
                                            .height > 0
                                    );
                                }
                            );

                        if (!visibleElements.length) {
                            return false;
                        }

                        const currentElement =
                            visibleElements[
                                visibleElements.length - 1
                            ];

                        const currentText =
                            currentElement.innerText.trim();

                        return (
                            currentText.length > 100 &&
                            (
                                oldText.length === 0 ||
                                currentText !== oldText
                            )
                        );
                    }
                    """,
                    arg={
                        "selector": description_selector,
                        "oldText": old_description
                    },
                    timeout=15_000
                )

            except PlaywrightTimeoutError:
                print(
                    f"Description may not have updated for: "
                    f"{job_title}"
                )

            description_elements = search_page.locator(
                description_selector
            )

            for element_index in range(
                description_elements.count() - 1,
                -1,
                -1
            ):
                element = description_elements.nth(
                    element_index
                )

                try:
                    if not element.is_visible():
                        continue

                    candidate_text = (
                        element.inner_text().strip()
                    )

                    if len(candidate_text) > 100:
                        description = candidate_text
                        description_html = (
                            element.inner_html().strip()
                        )
                        break

                except Exception:
                    continue

            company_elements = search_page.locator(
                company_selector
            )

            for company_index in range(
                company_elements.count() - 1,
                -1,
                -1
            ):
                company_element = company_elements.nth(
                    company_index
                )

                try:
                    if not company_element.is_visible():
                        continue

                    company = (
                        company_element.get_attribute(
                            "aria-label"
                        )
                        or company_element.inner_text()
                    )

                    if company:
                        company = company.strip()
                        break

                except Exception:
                    continue

            if description:
                print(
                    f"Collected {len(description)} "
                    f"description characters."
                )
            else:
                print(
                    f"Description not found for: "
                    f"{job_title}"
                )

            if company:
                print(f"Company: {company}")
            else:
                print(
                    f"Company not found for: "
                    f"{job_title}"
                )

            results.append({
                "title": job_title,
                "company": company,
                "url": job_url,
                "description": description,
                "description_html": description_html
            })

    return results


if __name__ == "__main__":
    results = getData(
        "Software Engineer",
        "Atlanta",
        "GA"
    )

    print(
        f"\nTotal jobs collected: "
        f"{len(results)}"
    )

    for number, job in enumerate(
        results,
        start=1
    ):
        print(f"\nJOB {number}")
        print("Title:", job["title"])
        print("Company:", job["company"])
        print("URL:", job["url"])
        print("Description:")
        print(job["description"])
        print("=" * 80)
