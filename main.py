from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import pandas as pd
import os
import psutil


def cleanup_chromedriver():
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] in ["chromedriver.exe", "chromedriver"]:
            try:
                proc.kill()
                print(f"Killed existing chromedriver process: {proc.pid}")
            except:
                pass


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--start-maximized")  # Mở trình duyệt toàn màn hình
    try:
        cleanup_chromedriver()
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
        print("Chrome driver initialized successfully!")
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        raise


def save_product_to_csv(data, filename="aliexpress_product_details.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "lv3_title",
                "product_price",
                "original_price",
                "discount",
                "product_title",
                "sku_properties",
                "sku_variants",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def crawl_product_details(driver, lv3_href, lv3_title):
    product_data = []

    try:
        # Đảm bảo chỉ có 1 tab
        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()
        driver.switch_to.window(driver.window_handles[0])

        driver.get(lv3_href)
        time.sleep(10)
        print(f"Number of tabs after loading {lv3_href}: {len(driver.window_handles)}")

        # Đóng tab pop-up
        if len(driver.window_handles) > 1:
            print(f"Detected extra tabs, closing them...")
            while len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # Đợi product cards
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a.search-card-item")
                )
            )
            product_cards = driver.find_elements(By.CSS_SELECTOR, "a.search-card-item")
            if not product_cards:
                print(f"No product cards found for {lv3_href}")
                return product_data
        except Exception as e:
            print(f"Error waiting for product cards at {lv3_href}: {e}")
            return product_data

        main_window = driver.current_window_handle

        for card in product_cards[:5]:
            try:
                product_url = card.get_attribute("href")
                if not product_url:
                    print(f"No href found for product card at {lv3_href}")
                    continue

                # Đảm bảo chỉ có 1 tab
                if len(driver.window_handles) > 1:
                    print(
                        f"Unexpected tabs before opening {product_url}, closing extras..."
                    )
                    while len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                        driver.close()
                    driver.switch_to.window(main_window)

                # Mở trang sản phẩm
                driver.execute_script(f"window.open('{product_url}', '_blank');")
                time.sleep(2)

                # Đợi tab mới
                try:
                    current_tabs = len(driver.window_handles)
                    print(f"Number of tabs before waiting: {current_tabs}")
                    WebDriverWait(driver, 15).until(
                        EC.number_of_windows_to_be(current_tabs)
                    )
                    new_window = [w for w in driver.window_handles if w != main_window][
                        0
                    ]
                    driver.switch_to.window(new_window)
                    time.sleep(2)
                except Exception as e:
                    print(f"Error switching to new tab for {product_url}: {e}")
                    print(f"Number of tabs after error: {len(driver.window_handles)}")
                    driver.close()
                    driver.switch_to.window(main_window)
                    continue

                # Thử tải trang
                for attempt in range(2):
                    try:
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                        )
                        break
                    except:
                        if attempt == 1:
                            print(
                                f"Error waiting for product page to load at {product_url}"
                            )
                            print(f"Page source: {driver.page_source[:1000]}...")
                            driver.close()
                            driver.switch_to.window(main_window)
                            continue
                        time.sleep(5)

                # Thu thập dữ liệu
                data = {
                    "lv3_title": lv3_title,
                    "product_price": "",
                    "original_price": "",
                    "discount": "",
                    "product_title": "",
                    "sku_properties": "",
                    "sku_variants": "",
                }

                # Lấy product-price-value
                try:
                    price = driver.find_element(
                        By.CSS_SELECTOR, "span.product-price-value"
                    )
                    if price.text.strip():
                        data["product_price"] = price.text.strip()
                except:
                    pass

                # Lấy price--originalText--gxVO5_d
                try:
                    original_price = driver.find_element(
                        By.CSS_SELECTOR, "span.price--originalText--gxVO5_d"
                    )
                    if original_price.text.strip():
                        data["original_price"] = original_price.text.strip()
                except:
                    pass

                # Lấy price--discount--Y9uG2LK
                try:
                    discount = driver.find_element(
                        By.CSS_SELECTOR, "span.price--discount--Y9uG2LK"
                    )
                    if discount.text.strip():
                        data["discount"] = discount.text.strip()
                except:
                    pass

                # Lấy product-title
                try:
                    title = driver.find_element(
                        By.CSS_SELECTOR, "div.title--wrap--UUHae_g h1"
                    )
                    if title.text.strip():
                        data["product_title"] = title.text.strip()
                except:
                    try:
                        title = driver.find_element(By.CSS_SELECTOR, "h1")
                        if title.text.strip():
                            data["product_title"] = title.text.strip()
                    except:
                        pass

                # Lấy sku properties và sku variants
                try:
                    sku_properties_list = []
                    sku_variants_dict = {}
                    property_elements = driver.find_elements(
                        By.CSS_SELECTOR, "div.sku-item--property--HuasaIz"
                    )
                    for prop in property_elements:
                        try:
                            title_span = prop.find_element(
                                By.CSS_SELECTOR, "div.sku-item--title--Z0HLO87"
                            )
                            prop_name = driver.execute_script(
                                "return arguments[0].childNodes[0].textContent.trim().replace(/:$/, '')",
                                title_span,
                            )
                            if prop_name:
                                sku_properties_list.append(prop_name)
                            sku_row = prop.find_element(
                                By.CSS_SELECTOR, "div.sku-item--skus--StEhULs"
                            )
                            variants = []
                            image_variants = sku_row.find_elements(
                                By.CSS_SELECTOR, "div.sku-item--image--jMUnnGA img"
                            )
                            for img in image_variants:
                                alt_text = img.get_attribute("alt")
                                if alt_text and alt_text.strip():
                                    variants.append(alt_text.strip())
                            text_variants = sku_row.find_elements(
                                By.CSS_SELECTOR, "div.sku-item--text--hYfAukP span"
                            )
                            for text in text_variants:
                                if text.text.strip():
                                    variants.append(text.text.strip())
                            if prop_name and variants:
                                sku_variants_dict[prop_name] = variants
                        except:
                            continue

                    if sku_properties_list:
                        data["sku_properties"] = str(sku_properties_list)
                    if sku_variants_dict:
                        data["sku_variants"] = ", ".join(
                            f"{key}: {str(value)}"
                            for key, value in sku_variants_dict.items()
                        )
                except:
                    pass

                save_product_to_csv(data)
                print(f"Saved product data for {product_url}")

                product_data.append(data)

                driver.close()
                driver.switch_to.window(main_window)
                time.sleep(1)

            except Exception as e:
                print(f"Error processing product card for {lv3_href}: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                driver.switch_to.window(main_window)
                time.sleep(1)
                continue

    except Exception as e:
        print(f"Error processing link {lv3_href}: {e}")

    return product_data


def main():
    csv_file = "aliexpress_subcategory_details.csv"
    if not os.path.isfile(csv_file):
        print(
            f"File {csv_file} not found. Please create it with 'lv3_href' and 'lv3_title' columns."
        )
        return

    try:
        df = pd.read_csv(csv_file)
        if df.empty or "lv3_href" not in df.columns or "lv3_title" not in df.columns:
            print(
                f"File {csv_file} is empty or missing required columns ('lv3_href', 'lv3_title')."
            )
            return
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return

    driver = None
    all_data = []

    try:
        driver = setup_driver()
        for index, row in df.iterrows():
            lv3_href = row["lv3_href"]
            lv3_title = row["lv3_title"]
            if pd.isna(lv3_href) or lv3_href == "N/A":
                print(f"Skipping invalid href for {lv3_title}")
                continue

            print(f"Processing {lv3_href}")
            try:
                data = crawl_product_details(driver, lv3_href, lv3_title)
                all_data.extend(data)
            except Exception as e:
                print(f"Session error for {lv3_href}: {e}")
                driver.quit()
                driver = setup_driver()
                continue

    except Exception as e:
        print(f"Main loop error: {e}")
    finally:
        if driver is not None:
            driver.quit()
        cleanup_chromedriver()

    print(f"Total {len(all_data)} products saved to aliexpress_product_details.csv")


if __name__ == "__main__":
    main()
