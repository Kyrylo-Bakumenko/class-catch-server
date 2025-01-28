# class_catch_app/management/commands/refresh_proxies.py

from django.core.management.base import BaseCommand
from class_catch_app.proxy_manager import ProxyManager
import time
import warnings
from urllib3.exceptions import InsecureRequestWarning

# suppress only the specific warning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Fetches and verifies proxies asynchronously'

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write("Starting proxy refresh...")

        proxy_manager = ProxyManager()
        proxy_manager.refresh_proxies()

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(f"Proxy refresh completed in {end_time - start_time} seconds"))
