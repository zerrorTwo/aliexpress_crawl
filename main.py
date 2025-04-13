from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv


def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    return driver


def crawl_subcategory_details(driver, url):
    driver.get(url)
    time.sleep(5)  # Đợi trang tải hoàn toàn

    category_data = []

    try:
        # Đợi các category titles xuất hiện
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.Categoey--categoryTitle--_3bKGRN")
            )
        )
        category_titles = driver.find_elements(
            By.CSS_SELECTOR, "div.Categoey--categoryTitle--_3bKGRN"
        )

        for title in category_titles:
            try:
                if not title.is_displayed():
                    continue

                # Hover vào category title để hiển thị ul.Categoey--categoryList--2QES_k6
                ActionChains(driver).move_to_element(title).perform()
                time.sleep(1)

                # Tìm ul.Categoey--categoryList--2QES_k6
                category_lists = driver.find_elements(
                    By.CSS_SELECTOR, "ul.Categoey--categoryList--2QES_k6"
                )
                if not category_lists:
                    print(f"No category list found for {title.text}")
                    continue

                category_list = category_lists[0]

                # Tìm danh sách các li.Categoey--categoryItem--3hPv6R5 trong ul
                category_items = category_list.find_elements(
                    By.CSS_SELECTOR, "li.Categoey--categoryItem--3hPv6R5"
                )
                if not category_items:
                    print(f"No subcategory items found for {title.text}")
                    continue

                # Lặp qua từng li để hover
                for item in category_items:
                    try:
                        # In text của li.Categoey--categoryItem--3hPv6R5
                        item_text = item.text.strip() if item.text.strip() else "N/A"
                        print(f"Mục con trong {title.text}: {item_text}")

                        # Hover vào li để hiển thị div.Categoey--categoryRight--2uIfSd3
                        ActionChains(driver).move_to_element(item).perform()
                        time.sleep(1)

                        # Tìm div.Categoey--categoryRight--2uIfSd3 trong ul
                        right_divs = category_list.find_elements(
                            By.CSS_SELECTOR, "div.Categoey--categoryRight--2uIfSd3"
                        )
                        if not right_divs:
                            print(
                                f"No right div found for subcategory item in {title.text}"
                            )
                            continue

                        right_div = right_divs[0]

                        # Tìm tất cả span.Categoey--cateItem--2c4rOz trong div
                        cate_items = right_div.find_elements(
                            By.CSS_SELECTOR, "span.Categoey--cateItem--2c4rOz0"
                        )
                        if not cate_items:
                            print(f"No cate items found for {title.text}")
                            continue

                        for cate_item in cate_items:
                            try:
                                # Lấy text của Categoey--cateItemLv2Title--1tw0jft
                                lv2_title_elements = cate_item.find_elements(
                                    By.CSS_SELECTOR,
                                    "div.Categoey--cateItemLv2Title--1tw0jft",
                                )
                                lv2_title = (
                                    lv2_title_elements[0].text.strip()
                                    if lv2_title_elements
                                    else "N/A"
                                )

                                # Tìm tất cả thẻ <a>
                                a_elements = cate_item.find_elements(
                                    By.CSS_SELECTOR, "a"
                                )
                                for a_element in a_elements:
                                    try:
                                        # Lấy text của div.Categoey--cateItemLv3Title--1mjlI-5 trong thẻ <a>
                                        div_elements = a_element.find_elements(
                                            By.CSS_SELECTOR,
                                            "div.Categoey--cateItemLv3Title--1mjlI-5",
                                        )
                                        div_text = (
                                            div_elements[0].text.strip()
                                            if div_elements
                                            else "N/A"
                                        )
                                        a_href = (
                                            a_element.get_attribute("href")
                                            if a_element
                                            else "N/A"
                                        )

                                        category_data.append(
                                            {
                                                "category_title": (
                                                    title.text.strip()
                                                    if title.text.strip()
                                                    else "N/A"
                                                ),
                                                "subcategory_item": item_text,
                                                "lv2_title": lv2_title,
                                                "lv3_title": div_text,
                                                "lv3_href": a_href,
                                            }
                                        )
                                    except Exception as e:
                                        print(
                                            f"Error processing a element in cate item: {e}"
                                        )
                                        continue

                            except Exception as e:
                                print(
                                    f"Error processing cate item in {title.text}: {e}"
                                )
                                continue

                        # Di chuột ra khỏi li để reset hover
                        ActionChains(driver).move_by_offset(0, 0).perform()
                        time.sleep(0.5)

                    except Exception as e:
                        print(f"Error processing subcategory item in {title.text}: {e}")
                        continue

                # Di chuột ra khỏi category title
                ActionChains(driver).move_by_offset(0, 0).perform()
                time.sleep(0.5)

            except Exception as e:
                print(f"Error processing category {title.text}: {e}")
                continue

    except Exception as e:
        print(f"Error finding category titles: {e}")

    return category_data


def save_to_csv(data, filename="aliexpress_subcategory_details.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "category_title",
                "subcategory_item",
                "lv2_title",
                "lv3_title",
                "lv3_href",
            ],
        )
        writer.writeheader()
        for item in data:
            writer.writerow(item)
    print(f"Saved {len(data)} items to {filename}")


def main():
    url = "https://www.aliexpress.com/"
    driver = setup_driver()

    try:
        print("Crawling subcategory details...")
        data = crawl_subcategory_details(driver, url)

        if data:
            save_to_csv(data)
        else:
            print("No data was crawled.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
