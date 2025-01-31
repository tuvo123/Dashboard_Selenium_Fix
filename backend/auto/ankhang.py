from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
import psycopg2
import datetime
from dotenv import load_dotenv
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys
import codecs
import logging


if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
# Cấu hình ghi log
log_filename = 'app.log'
logging.basicConfig(filename=log_filename, level=logging.ERROR, format='%(asctime)s [%(levelname)s] - %(message)s')

chromedriver_autoinstaller.install()
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(options=chrome_options)
url = "https://www.nhathuocankhang.com/"
load_dotenv()

try:
# Kết nối đến cơ sở dữ liệu PostgreSQL
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS thuocsi_vn (
                title TEXT,
                giacu TEXT,
                ngaycu DATE,
                giamoi TEXT,
                ngaymoi DATE,
                month_1 TEXT,
                month_2 TEXT,
                month_3 TEXT,
                month_4 TEXT,
                month_5 TEXT,
                month_6 TEXT,
                month_7 TEXT,
                month_8 TEXT,
                month_9 TEXT,
                month_10 TEXT,
                month_11 TEXT,
                month_12 TEXT,
                photo TEXT,
                nha_san_xuat TEXT,
                nuoc_san_xuat TEXT,
                hamluong_thanhphan TEXT,
                thong_tin_san_pham TEXT,
                link TEXT primary key,
                nguon TEXT DEFAULT 'an_khang'
            )
        ''')
        wait = WebDriverWait(driver, 1)

    link_lists = [
        # Thuốc
        "thuoc-bo-va-vitamin",
        # "tim-mach-tieu-duong",
        # "giam-dau-ha-sot-khang-viem",
        # "mat-tai-mui-hong",
        # "ho-hap",
        # "khang-sinh-khang-nam",
        # "tiet-nieu-sinh-duc",
        # "than-kinh-nao-bo",
        # "tieu-hoa-gan-mat"
        # "co-xuong-khop-gut",
        # "dau-cao-xoa-mieng-dan",
        # "da-lieu-di-ung",

        # # TPCN
        # "bo-gan-thanh-nhiet",
        # "vitamin-va-khoang-chat",
        # "dau-ca-bo-mat",
        # "ho-tro-tieu-hoa",
        # "keo-ngam-vien-ngam",
        # "vien-uong-bo-nao",
        # "bo-phe-ho-tro-ho-hap",
        # "ho-tro-lam-dep-giam-can",
        # "tang-cuong-sinh-ly-bo-than",
        # "bo-xuong-khop",
        # "ho-tro-tim-mach",
        # "ho-tro-tieu-duong",
        # "ho-tro-tri-tao-bon-tri",

        # # Chăm sóc cá nhân
        # "sua-bot",
        # "cham-soc-mat-tai-mui-hong",
        # "cham-soc-rang-mieng",
        # "cham-soc-toan-than",
        # "cham-soc-vung-kin",
        # "thuc-pham-do-uong",
        # "cham-soc-toc",
        # "bao-cao-su",
        # "ho-tro-dieu-tri-ung-thu",
        # "sua-rua-mat",

        # "my-pham",
        # "dung-cu-y-te",
        # "cham-soc-tre-em",
    ]

    base_url = "https://www.nhathuocankhang.com"
    all_links = []

    for url_suffix in link_lists:
        full_url = f"{base_url}/{url_suffix}"
        driver.get(full_url)

        try:
            active_button = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-wrapper > .active")))
            active_button.click()
        except (ElementNotInteractableException, NoSuchElementException, TimeoutException):
            pass

        while True:
            try:
                view_more_button = driver.find_element(By.CSS_SELECTOR, ".view-more > a")
                if view_more_button.is_displayed():
                    view_more_button.click()
                    sleep(1)
                else:
                    break
            except NoSuchElementException:
                break

        link_elements = driver.find_elements(By.CSS_SELECTOR, "ul.listing-prod > li a")
        links = [link.get_attribute('href') for link in link_elements]
        all_links.extend(links)


        def extract_product_info():
            product_name_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.detail-title")))
            product_name = product_name_element.text
            return product_name

        def check_product_exist(cursor, product_name):
            cursor.execute("SELECT EXISTS(SELECT 1 FROM thuocsi_vn WHERE title = %s)", (product_name,))
            return cursor.fetchone()[0]

        for a in links:
            driver.get(a)
            sleep(1)
            try:
                product_name = ""

                try:
                    html = driver.page_source
                    product_name = extract_product_info()
                except NoSuchElementException:
                    pass
                try:
                    ten = driver.find_element(By.CSS_SELECTOR, "h1.detail-title").text

                    try:
                        gia_sales_element = driver.find_element(By.CSS_SELECTOR, ".list-price-tracking:nth-child(3) b")
                    except NoSuchElementException:
                        try:
                            gia_sales_element = driver.find_element(By.CSS_SELECTOR, ".list-price-tracking:nth-child(2) b")
                        except NoSuchElementException:
                            try:
                                gia_sales_element = driver.find_element(By.CSS_SELECTOR, ".box-price b")
                            except NoSuchElementException:
                                gia_sales_element = 0

                    if gia_sales_element:
                        gia_sales_text = gia_sales_element.text.replace("₫", "").replace(".", "").replace(" ", "")
                        gia_sales = int(gia_sales_text)
                    else:
                        gia_sales = 0
                except NoSuchElementException:
                    gia_sales = 0
                nha_san_xuat = driver.find_element(By.CSS_SELECTOR, ".des-infor > li:nth-child(4)").text
                if "Hãng sản xuất" in nha_san_xuat:
                    nha_san_xuat = nha_san_xuat.replace("Hãng sản xuất", "").strip()
                elif "Nơi sản xuất" in nha_san_xuat:
                    nha_san_xuat = nha_san_xuat.replace("Nơi sản xuất", "").strip()
                else:
                    nha_san_xuat_alt = driver.find_element(By.CSS_SELECTOR, ".des-infor > li:nth-child(5)").text
                    if "Hãng sản xuất" in nha_san_xuat_alt:
                        nha_san_xuat = nha_san_xuat_alt.replace("Hãng sản xuất", "").strip()
                    elif "Nơi sản xuất" in nha_san_xuat_alt:
                        nha_san_xuat = nha_san_xuat_alt.replace("Nơi sản xuất", "").strip()
                    else:
                        nha_san_xuat = "Không đề cập"

                nuoc_san_xuat = driver.find_element(By.CSS_SELECTOR, ".des-infor > li:nth-child(5)").text
                if "Nơi sản xuất" in nuoc_san_xuat:
                    nuoc_san_xuat = nuoc_san_xuat.replace("Nơi sản xuất", "").strip()
                else:
                    nuoc_san_xuat_alt = driver.find_element(By.CSS_SELECTOR, ".des-infor > li:nth-child(6)").text
                    if "Nơi sản xuất" in nuoc_san_xuat_alt:
                        nuoc_san_xuat = nuoc_san_xuat_alt.replace("Nơi sản xuất", "").strip()
                    else:
                        nuoc_san_xuat = "Không đề cập"

                thanhphan_hamluong = driver.find_element(By.CSS_SELECTOR, ".des-infor > li:nth-child(2)").text
                thanhphan_hamluong = thanhphan_hamluong.replace("Thành phần chính", "").strip()
                thong_tin_san_pham = driver.find_element(By.CSS_SELECTOR, ".des-infor > li:nth-child(1)").text
                thong_tin_san_pham = thong_tin_san_pham.replace("Công dụng", "").strip()
                photo = driver.find_element(By.CSS_SELECTOR, ".active > .item-img > img").get_attribute("src")
                ngay = datetime.datetime.now().date()
                current_month = datetime.datetime.now().month

                with connection.cursor() as cursor:
                    cursor.execute(f'''
                        INSERT INTO thuocsi_vn (title, giamoi, ngaymoi, month_{current_month}, photo, nha_san_xuat,
                        nuoc_san_xuat, hamluong_thanhphan, thong_tin_san_pham, link, nguon, giacu, ngaycu)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL)
                        ON CONFLICT (link) DO UPDATE
                            SET month_{current_month} = excluded.month_{current_month},
                            thong_tin_san_pham = excluded.thong_tin_san_pham,
                            nha_san_xuat = excluded.nha_san_xuat,
                            nuoc_san_xuat = excluded.nuoc_san_xuat,
                            hamluong_thanhphan = excluded.hamluong_thanhphan,
                            photo = excluded.photo,
                            giacu = thuocsi_vn.giamoi,
                            ngaycu = thuocsi_vn.ngaymoi,
                            giamoi='{gia_sales}',
                            ngaymoi='{ngay}';
                    ''', (
                        product_name, gia_sales, ngay, gia_sales, photo, nha_san_xuat, nuoc_san_xuat, thanhphan_hamluong, thong_tin_san_pham, a, 'ankhang.com'))
                    connection.commit()
            except Exception as e:
                logging.error(f"Error scraping product: {str(e)}")

        driver.quit()

except Exception as e:
    logging.error(f"Unhandled Exception: {str(e)}")

