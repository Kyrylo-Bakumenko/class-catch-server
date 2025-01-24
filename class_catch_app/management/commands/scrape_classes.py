import time
from django.core.management.base import BaseCommand
from class_catch_app.models import Class, Proxy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from class_catch_app.proxy_manager import ProxyManager
from django.db import transaction
from bs4 import BeautifulSoup
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning
from django.utils import timezone

warnings.simplefilter('ignore', InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Scrapes class data for Winter Term 2025 and updates the database'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_manager = ProxyManager()
        self.DEBUG = False

    def add_arguments(self, parser):
        # [change warning] --use-requests option removed since we'll always try requests first
        pass

    def create_driver(self, proxy=None):
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
            
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        driver.set_page_load_timeout(30)
        return driver

    def handle(self, *args, **options):
        start_time = time.time()

        # proxy refreshing is handled asynchronously via a separate cron job
        
        # time threshold for considering proxies as recently verified
        time_threshold = timezone.now() - timezone.timedelta(hours=1)

        # fetch working proxies for either requests or Selenium, 
        # annotate w/ most recent verification time
        proxies = Proxy.objects.filter(
            Q(is_working_requests=True, last_verified_requests__gte=time_threshold) |
            Q(is_working_selenium=True, last_verified_selenium__gte=time_threshold)
        ).annotate(
            max_last_verified=Greatest('last_verified_requests', 'last_verified_selenium')
        ).order_by('-max_last_verified')

        success = False

        for proxy in proxies:
            proxy_address = f"{proxy.ip}:{proxy.port}"
            if proxy.is_working_requests and proxy.last_verified_requests >= proxy.last_verified_selenium:
                # try scraping with requests
                try:
                    self.stdout.write(f"Attempting to scrape with requests using proxy {proxy_address}...")
                    self.scrape_with_requests(proxy_address)
                    success = True
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed with proxy {proxy_address}: {e}"))
                    # update proxy status
                    proxy.is_working_requests = False
                    proxy.save(update_fields=['is_working_requests'])
            elif proxy.is_working_selenium:
                # try scraping with Selenium
                try:
                    self.stdout.write(f"Attempting to scrape with Selenium using proxy {proxy_address}...")
                    driver = self.create_driver(proxy_address)
                    self.scrape_with_selenium(driver)
                    driver.quit()
                    success = True
                    break 
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed with proxy {proxy_address}: {e}"))
                    # update proxy status
                    proxy.is_working_selenium = False
                    proxy.save(update_fields=['is_working_selenium'])
            else:
                # if both fail, skip to the next proxy
                continue

        if not success:
            # try scraping without any proxy using requests
            self.stdout.write("Trying to scrape with requests without a proxy...")
            try:
                self.scrape_with_requests(None)
                success = True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed without proxy: {e}"))

        if not success:
            # if scraping with requests failed, fall back to Selenium (still, without a proxy)
            self.stdout.write("Trying to scrape with Selenium without a proxy...")
            try:
                driver = self.create_driver()
                self.scrape_with_selenium(driver)
                driver.quit()
                success = True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed without proxy: {e}"))

        if success:
            self.stdout.write(self.style.SUCCESS("Scraping completed successfully."))
        else:
            self.stdout.write(self.style.ERROR("Scraping failed with all methods."))

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(f"Total scraping time: {end_time - start_time:.2f} seconds"))


    def scrape_with_selenium(self, driver):
        # navigate to the timetable page
        driver.get("https://oracle-www.dartmouth.edu/dart/groucho/timetable.main")
        
        # wait for the Subject Area button to be clickable
        wait = WebDriverWait(driver, 10)
        subject_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Subject Area(s)']"))
        )
        subject_button.click()

        # wait for the term checkbox to be clickable
        winter_term_checkbox = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='202501']"))
        )
        if not winter_term_checkbox.is_selected():
            winter_term_checkbox.click()

        # click search button
        search_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Search for Courses']"))
        )
        search_button.click()

        # wait for the data table to load
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='data-table']/table"))
        )

        # load all data without scrolling
        self.load_all_data(driver)

        # scrape courses :)
        self.scrape_courses(driver.page_source)

    def load_all_data(self, driver):
        """
        Load all data on the page by scrolling to the bottom repeatedly until all data is loaded.
        """
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            # calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # if heights are the same, all data is loaded
                break
            last_height = new_height

    def scrape_with_requests(self, proxy):
        start_time = time.time()
        try:
            # payload and headers
            url = "https://oracle-www.dartmouth.edu/dart/groucho/timetable.display_courses"
            payload = {
                "distribradio": "alldistribs",
                "depts": "no_value",
                "periods": "no_value",
                "distribs": "no_value",
                "distribs_i": "no_value",
                "distribs_wc": "no_value",
                "distribs_lang": "no_value",
                "deliveryradio": "alldelivery",
                "deliverymodes": "no_value",
                "pmode": "public",
                "term": "",
                "levl": "",
                "fys": "n",
                "wrt": "n",
                "pe": "n",
                "review": "n",
                "crnl": "no_value",
                "classyear": "2008",
                "searchtype": "Subject Area(s)",
                "termradio": "selectterms",
                "terms": "202501",
                "subjectradio": "selectsubjects",
                "hoursradio": "allhours",
                "sortorder": "dept",
            }
            headers = self.proxy_manager.get_random_headers()
            headers["Referer"] = "https://oracle-www.dartmouth.edu/dart/groucho/timetable.subject_search"

            proxies_dict = None
            if proxy:
                proxies_dict = {
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}",
                }

            # POST request
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                proxies=proxies_dict,
                timeout=30,
                verify=False
            )

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("Request successful!"))
                html_content = response.text
                self.scrape_courses(html_content)
            else:
                raise Exception(f"Request failed with status code: {response.status_code}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during scraping with requests: {e}'))
            raise e

    def scrape_courses(self, html_content):
        start_time = time.time()
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # find the data table
            table = soup.find('div', class_='data-table').find('table')

            # headers
            header_cells = table.find('tr').find_all('th')
            headers = [cell.get_text(strip=True) for cell in header_cells]
            header_indices = {header: idx for idx, header in enumerate(headers)}

            # fetch existing classes for the term
            existing_classes = Class.objects.filter(term='202501')
            existing_classes_dict = {
                (cls.class_code, cls.course_number, cls.section): cls
                for cls in existing_classes
            }

            # lists for bulk operations
            classes_to_create = []
            classes_to_update = []

            data_rows = table.find_all('tr')[1:]  # Skip header row

            for row in data_rows:
                # skip separator rows
                if row.find('td', {'colspan': True}):
                    continue

                data_cells = row.find_all('td')
                cell_texts = [cell.get_text(strip=True) for cell in data_cells]

                data = {}
                for header, idx in header_indices.items():
                    data[header] = cell_texts[idx] if idx < len(cell_texts) else ''

                # row data
                class_key = (
                    data.get('Subj', ''),
                    data.get('Num', ''),
                    data.get('Sec', '')
                )

                class_data = {
                    'class_code': data.get('Subj', ''),
                    'course_number': data.get('Num', ''),
                    'section': data.get('Sec', ''),
                    'title': data.get('Title', ''),
                    'instructor': data.get('Instructor', ''),
                    'term': data.get('Term', ''),
                    'limit': int(data.get('Lim', '0') or '0'),
                    'enrollment': int(data.get('Enrl', '0') or '0'),
                    'distrib': data.get('Dist', ''),
                    'world_culture': data.get('WC', ''),
                    'period': data.get('Period', ''),
                    'period_code': data.get('Period Code', ''),
                    'status': data.get('Status', ''),
                    'text': data.get('Text', ''),
                    'xlist': data.get('Xlist', ''),
                    'crn': data.get('CRN', ''),
                }

                existing_class = existing_classes_dict.get(class_key)

                if existing_class:
                    # check if enrollment has changed
                    if existing_class.enrollment != class_data['enrollment']:
                        # update enrollment
                        existing_class.enrollment = class_data['enrollment']
                    
                    # update other fields
                    for field, value in class_data.items():
                        setattr(existing_class, field, value)
                    classes_to_update.append(existing_class)
                else:
                    new_class = Class(**class_data)
                    classes_to_create.append(new_class)

            # make bulk operations atomic
            with transaction.atomic():
                if classes_to_create:
                    Class.objects.bulk_create(classes_to_create)
                    self.stdout.write(self.style.SUCCESS(f'Added {len(classes_to_create)} new classes.'))

                if classes_to_update:
                    update_fields = [
                        'title', 'instructor', 'limit', 'enrollment', 'distrib', 'world_culture',
                        'period', 'period_code', 'status', 'text', 'xlist', 'crn', 'last_updated'
                    ]
                    Class.objects.bulk_update(classes_to_update, update_fields)
                    self.stdout.write(self.style.SUCCESS(f'Updated {len(classes_to_update)} existing classes.'))

            end_time = time.time()
            self.stdout.write(self.style.SUCCESS(f"TIME FOR SCRAPE: {end_time - start_time} seconds"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error while scraping courses: {e}'))
            raise e
