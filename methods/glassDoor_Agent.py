from urllib.parse import quote_plus, urljoin
from playwright.sync_api import (sync_playwright,TimeoutError as PlaywrightTimeoutError)

def getData(title,city,state):
    search_url = ("https://www.glassdoor.com/Reviews/index.htm")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        if not browser.contexts:
            raise RuntimeError("Error in Debugging Browser//Line 10")
        context = browser.contexts[0]
        page = context.new_page()
        page.goto(search_url,wait_until="domcontentloaded",timeout=60_000)
        searchBox = page.locator('input[data-test="employer-autocomplete-input"]')
        searchBox.fill(title)
        #searchButton = page.get_by_role("button", name="Search")
        #searchButton.click()
        #locationInput = page.locator('input[data-test="location-search-input"]')
        #locationInput.fill(f"{city}, {state}")
        #titleInput = page.locator('input[data-test="keyword-search-input"]')
        #titleInput.fill(title)
        searchBox.press("Enter")
        viewMore = page.get_by_text('View more companies', exact = True)
        viewMore.click()
        
        #loop of all companies with similiar names
        elements = page.locator('[data-test="employer-card"]')
        elementCount = elements.count()
        #we don't want to check every company in the worlkd so limit the threshold
        if elementCount > 5:
            elementCount = 5
        
        choices = []
        choicesLink = []
        for element in range(elementCount):
            card = elements.nth(element)
            tempName = card.locator('[data-test="employer-short-name"]').inner_text().strip()
            choices.append(card)
            reviewButton = card.get_by_text("reviews", exact = True)
            #reviewButton.click()
            reviewLink = card.locator('a[data-test="cell-Reviews-url"]')
            choicesLink.append(reviewLink)
            
            #end the loop early if we find the exact match
            if tempName == title:
                break
        
        for review in reviewLink:
            tempReview = context.new_page()
            tempReview.goto(review)
            score = tempReview.locator('a[data-test="RatingHeadline_rating__jChhZ"]')
            
            


if __name__ == "__main__":
    testTitle = "Amicis Global"
    testCity = "Atlanta"
    testState = "Georgia"
    getData(testTitle,testCity,testState)
