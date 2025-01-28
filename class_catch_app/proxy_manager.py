# class_catch_app/proxy_manager.py

import requests
import concurrent.futures
import socket
import re
from class_catch_app.models import Proxy
from django.utils import timezone
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import time
import logging

# config logging
logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.lock = threading.Lock()
        self.requests_verified_proxies = []
        self.selenium_verified_proxies = []

    def validate_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def validate_port(self, port):
        if str(port).isdigit():
            port_num = int(port)
            return 0 < port_num <= 65535
        return False

    def get_random_headers(self):
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
        }
        return headers

    def fetch_proxies(self, limit=5, protocol='http', timeout=5000, country='all', ssl='yes', anonymity='elite'):
        """Fetch proxies from the ProxyScrape API with specified criteria."""
        url = 'https://api.proxyscrape.com/v2/'
        params = {
            'request': 'getproxies',
            'protocol': protocol,
            'timeout': timeout,
            'country': country,
            'ssl': ssl,
            'anonymity': anonymity
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                proxy_text = response.text.strip()
                for line in proxy_text.split('\n'):
                    if len(self.proxies) >= limit:
                        break
                    line = line.strip()
                    if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', line):
                        ip, port = line.split(':')
                        if self.validate_ip(ip) and self.validate_port(port):
                            self.proxies.append({'ip': ip, 'port': int(port)})
                if not self.proxies and ssl == 'yes':
                    print(f"No proxies found with ssl='{ssl}'. Trying ssl='no'.")
                    self.fetch_proxies(
                        limit=limit,
                        protocol=protocol,
                        timeout=timeout,
                        country=country,
                        ssl='no',
                        anonymity=anonymity
                    )
                elif not self.proxies and ssl == 'no':
                    print(f"No proxies found with ssl='{ssl}'. Trying ssl='all'.")
                    self.fetch_proxies(
                        limit=limit,
                        protocol=protocol,
                        timeout=timeout,
                        country=country,
                        ssl='all',
                        anonymity=anonymity
                    )
            else:
                print(f"Error fetching proxies: Status code {response.status_code}")
        except Exception as e:
            print(f"Error fetching proxies: {e}")

    def verify_proxy_on_test_url(self, proxy_info):
        """First-level proxy verification using a general test URL."""
        ip = proxy_info['ip']
        port = proxy_info['port']
        proxy = f"{ip}:{port}"
        try:
            test_url = 'https://httpbin.org/ip'
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}',
            }
            headers = self.get_random_headers()
            response = requests.get(
                test_url,
                proxies=proxies,
                headers=headers,
                timeout=10,
                verify=False
            )
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception:
            return False

    def verify_proxy_on_target_requests(self, proxy_info):
        """Second-level proxy verification on the target URL using requests."""
        ip = proxy_info['ip']
        port = proxy_info['port']
        proxy = f"{ip}:{port}"
        try:
            test_url = 'https://oracle-www.dartmouth.edu/dart/groucho/timetable.display_courses'
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}',
            }
            headers = self.get_random_headers()
            headers["Referer"] = "https://oracle-www.dartmouth.edu/dart/groucho/timetable.subject_search"

            payload = {
                "searchtype": "Subject Area(s)",
                "termradio": "selectterms",
                "terms": "202501",
            }

            response = requests.post(
                test_url,
                data=payload,
                headers=headers,
                proxies=proxies,
                timeout=10,
                verify=False
            )

            if response.status_code == 200 and "data-table" in response.text:
                # save or update the proxy in the database for requests
                Proxy.objects.update_or_create(
                    ip=ip,
                    port=port,
                    defaults={
                        'last_verified_requests': timezone.now(),
                        'is_working_requests': True
                    }
                )
                with self.lock:
                    self.requests_verified_proxies.append(proxy)
                return True
            else:
                Proxy.objects.update_or_create(
                    ip=ip,
                    port=port,
                    defaults={
                        'is_working_requests': False
                    }
                )
                return False
        except Exception:
            Proxy.objects.update_or_create(
                ip=ip,
                port=port,
                defaults={
                    'is_working_requests': False
                }
            )
            return False


    def verify_proxy_on_target_selenium(self, proxy_info):
        """Second-level proxy verification on the target URL using Selenium."""
        ip = proxy_info['ip']
        port = proxy_info['port']
        proxy = f"{ip}:{port}"
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument(f'--proxy-server={proxy}')
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(10)
            driver.get('https://oracle-www.dartmouth.edu/dart/groucho/timetable.main')
            driver.quit()
            # save or update the proxy in the database for Selenium
            Proxy.objects.update_or_create(
                ip=ip,
                port=port,
                defaults={
                    'last_verified_selenium': timezone.now(),
                    'is_working_selenium': True
                }
            )
            with self.lock:
                self.selenium_verified_proxies.append(proxy)
            return True
        except Exception:
            Proxy.objects.update_or_create(
                ip=ip,
                port=port,
                defaults={
                    'is_working_selenium': False
                }
            )
            return False

    def verify_proxies(self):
        """Verify proxies using the funnel system."""
        # first-level verification on a general test URL
        print("Starting first-level proxy verification...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {
                executor.submit(self.verify_proxy_on_test_url, proxy): proxy
                for proxy in self.proxies
            }
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result = future.result()
                    proxy['test_url_passed'] = result
                except Exception as e:
                    print(f"Error verifying proxy {proxy['ip']}:{proxy['port']} on test URL: {e}")
                    proxy['test_url_passed'] = False

        # filter proxies that passed the first-level verification
        verified_proxies = [proxy for proxy in self.proxies if proxy.get('test_url_passed')]

        if not verified_proxies:
            print("No proxies passed the first-level verification.")
            return

        # second-level verification on the target URL for requests
        print("Starting second-level proxy verification for requests...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.verify_proxy_on_target_requests, verified_proxies)

        # second-level verification on the target URL for Selenium
        print("Starting second-level proxy verification for Selenium...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.verify_proxy_on_target_selenium, verified_proxies)

    def get_working_proxies_requests(self):
        """Get proxies verified for requests within the last hour."""
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        working_proxies = Proxy.objects.filter(
            is_working_requests=True,
            last_verified_requests__gte=one_hour_ago
        )
        return [f"{proxy.ip}:{proxy.port}" for proxy in working_proxies]

    def get_working_proxies_selenium(self):
        """Get proxies verified for Selenium within the last hour."""
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        working_proxies = Proxy.objects.filter(
            is_working_selenium=True,
            last_verified_selenium__gte=one_hour_ago
        )
        return [f"{proxy.ip}:{proxy.port}" for proxy in working_proxies]

    def refresh_proxies(self):
        """Fetch and verify proxies."""
        self.proxies = []
        self.fetch_proxies(protocol='http', timeout=5000, country='all', ssl='yes', anonymity='elite')
        self.verify_proxies()

