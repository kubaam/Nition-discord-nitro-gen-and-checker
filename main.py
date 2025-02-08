"""
Nitro Generator and Checker - With Per-Endpoint Rate Limit Handling,
Automatic Redemption, and Live Console Status
Made by: Ambry (Modified by ChatGPT)
License: MIT
"""

import os
import sys
import time
import string
import ctypes
import logging
import random
from typing import Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('debug.log'), logging.StreamHandler()]
)

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    logging.critical("Missing required 'requests' module. Install with: pip install requests")
    sys.exit(1)

WEBHOOK_ENABLED = False
try:
    from discord_webhook import DiscordWebhook
    WEBHOOK_ENABLED = True
except ImportError:
    logging.warning("Webhook functionality disabled (install discord_webhook to enable)")

# Configuration Constants
ENDPOINTS = (
    "https://discord.com/api/v10/entitlements/gift-codes/",
    "https://discord.com/api/v9/entitlements/gift-codes/",
    "https://discord.com/api/v8/entitlements/gift-codes/",
    "https://canary.discord.com/api/v10/entitlements/gift-codes/",
    "https://ptb.discord.com/api/v10/entitlements/gift-codes/",
)
QUERY_PARAMS = "?with_application=false&with_subscription_plan=true"
REQUEST_TIMEOUT = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
CHECK_INTERVAL = 1.2           # Seconds between generating/checking codes
RATE_LIMIT_DELAY = (300, 900)  # 5-15 minutes in seconds

class ConsoleManager:
    """Handles console operations and visual effects."""
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def set_title(text: str):
        if os.name == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW(text)
        else:
            sys.stdout.write(f'\33]0;{text}\a')
            sys.stdout.flush()
    
    @staticmethod
    def slow_print(text: str, speed: float = 0.03, newline: bool = True):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(speed)
        if newline:
            print()

class NitroGenerator:
    """Main application logic for generating, checking, and redeeming Nitro codes."""
    def __init__(self):
        # Stats
        self.valid_codes = set()
        self.invalid_count = 0
        self.checked_count = 0
        
        # Configuration
        self.output_file = "valid_codes.txt"
        self.token: Optional[str] = None  # Discord token for auto redemption

        # Setup
        self.session = self._create_session()
        self.char_pool = string.ascii_letters + string.digits
        # Track per-endpoint rate-limit expiry times (0 == not rate-limited)
        self.endpoint_rate_limited_until = {ep: 0.0 for ep in ENDPOINTS}

        ConsoleManager.clear()
        self.display_banner()

    def _create_session(self) -> requests.Session:
        """Configure HTTP session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.headers.update({'User-Agent': USER_AGENT})
        return session

    def display_banner(self):
        banner = r"""
         _   _ _ _   _              
        | \ | (_) | (_)             
        |  \| |_| |_ _  ___  _ __   
        | . ` | | __| |/ _ \| '_ \  
        | |\  | | |_| | (_) | | | | 
        |_| \_|_|\__|_|\___/|_| |_| 
        """
        print(banner)
        ConsoleManager.slow_print("Created by: Ambry", 0.03)

    def validate_webhook(self, url: str) -> bool:
        """Verify Discord webhook URL format."""
        parsed = urlparse(url)
        return (
            parsed.netloc in {"discord.com", "canary.discord.com", "ptb.discord.com"}
            and "/api/webhooks/" in parsed.path
        )

    def generate_code(self) -> str:
        """Generate a 16-character Discord gift code."""
        return "".join(random.choices(self.char_pool, k=16))

    def is_endpoint_available(self, endpoint: str) -> bool:
        """
        Check if a given endpoint is not currently in a rate-limit cooldown.
        """
        return time.time() >= self.endpoint_rate_limited_until[endpoint]

    def mark_endpoint_rate_limited(self, endpoint: str):
        """
        Mark an endpoint as rate-limited for a random amount of time
        between RATE_LIMIT_DELAY (e.g., 5 to 15 minutes).
        """
        wait_time = random.randint(*RATE_LIMIT_DELAY)
        until_time = time.time() + wait_time
        self.endpoint_rate_limited_until[endpoint] = until_time

        msg = (f"Endpoint {endpoint} is now rate-limited. "
               f"It will be available again in {wait_time} seconds.")
        logging.warning(msg)
        # Print a colored warning in the console (red text).
        print(f"\033[91m{msg}\033[0m")

    def wait_for_earliest_endpoint(self):
        """
        If all endpoints are rate-limited, wait (with a countdown) for
        the earliest endpoint to become available.
        """
        earliest = min(self.endpoint_rate_limited_until, key=self.endpoint_rate_limited_until.get)
        wait_seconds = self.endpoint_rate_limited_until[earliest] - time.time()

        if wait_seconds <= 0:
            return  # Already expired.

        logging.warning(f"All endpoints are currently rate-limited. "
                        f"Waiting {int(wait_seconds)}s for earliest endpoint to become available.")

        for remaining in range(int(wait_seconds), 0, -1):
            status = f"Rate-limited! Cooling down for {remaining} seconds..."
            ConsoleManager.set_title(status)
            sys.stdout.write("\r" + status)
            sys.stdout.flush()
            time.sleep(1)

    def test_code(self, code: str, webhook_url: Optional[str] = None) -> bool:
        """
        Check a single code against one or more endpoints (randomly),
        but only among those that are currently available (not rate-limited).

        If an endpoint returns 429, we mark that endpoint as rate-limited
        and try another available endpoint. If no endpoints remain,
        we wait for the earliest one to come out of cooldown and exit.
        """
        full_url = f"https://discord.gift/{code}"

        # Start with a local list of all endpoints that are currently available.
        available_endpoints = [ep for ep in ENDPOINTS if self.is_endpoint_available(ep)]

        # If we have no available endpoints at all, we must wait for one to be free.
        if not available_endpoints:
            self.wait_for_earliest_endpoint()
            return False

        # We'll keep trying endpoints (in random order) until we find
        # a definitive result (valid or invalid) or exhaust them.
        random.shuffle(available_endpoints)

        for endpoint in available_endpoints:
            try:
                response = self.session.get(
                    f"{endpoint}{code}{QUERY_PARAMS}",
                    timeout=REQUEST_TIMEOUT
                )
            except requests.RequestException as e:
                logging.warning(f"Endpoint {endpoint} failed: {e}")
                # If request failed outright, skip this endpoint.
                continue

            if response.status_code == 200:
                # Valid code found!
                logging.info(f"Valid code found: {full_url}")
                self._handle_valid_code(full_url, webhook_url)
                return True
            elif response.status_code == 429:
                # This endpoint is individually rate-limited now.
                self.mark_endpoint_rate_limited(endpoint)
                # We remove it from the list and try the next one in the loop.
                continue
            else:
                # If the endpoint says it's invalid (or any other non-429 code),
                # we consider the code invalid right away and stop checking.
                logging.debug(f"Invalid code: {full_url} (Response Code: {response.status_code})")
                return False

        # If we tried all available endpoints and only got rate-limited responses,
        # we have no more endpoints to try this code on.
        # We must wait for the earliest endpoint to become free, then stop (return False).
        self.wait_for_earliest_endpoint()
        return False

    def _handle_valid_code(self, code: str, webhook_url: Optional[str]):
        """Process valid code discovery: save, notify, and redeem."""
        self.valid_codes.add(code)
        self._save_code(code)
        
        if webhook_url and WEBHOOK_ENABLED:
            self._trigger_webhook(code, webhook_url)
        
        if self.token:
            redeemed = self.redeem_code(code, self.token)
            if redeemed:
                logging.info("Nitro code redeemed successfully!")
            else:
                logging.error("Failed to redeem Nitro code.")

    def _save_code(self, code: str):
        """Save valid code to output file."""
        try:
            with open(self.output_file, 'a') as f:
                f.write(f"{code}\n")
        except IOError as e:
            logging.error(f"File write error: {e}")

    def _trigger_webhook(self, code: str, url: str):
        """Send notification to Discord webhook."""
        try:
            webhook = DiscordWebhook(
                url=url,
                content=f"🚀 Valid Nitro Code Found! @everyone\n{code}"
            )
            response = webhook.execute()
            if response.status_code != 200:
                logging.error(f"Webhook failed with status {response.status_code}")
        except Exception as e:
            logging.error(f"Webhook error: {e}")

    def redeem_code(self, code: str, token: str) -> bool:
        """
        Attempt to redeem a valid Nitro code using the provided Discord token.
        This sends a POST request to the Discord API redemption endpoint.
        """
        redemption_url = f"https://discord.com/api/v9/entitlements/gift-codes/{code}/redeem"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }
        try:
            response = self.session.post(
                redemption_url, headers=headers, json={}, timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                logging.info(f"Successfully redeemed Nitro code: {code}")
                return True
            else:
                logging.error(f"Failed to redeem Nitro code: {code}. "
                              f"Status Code: {response.status_code}. Response: {response.text}")
        except Exception as e:
            logging.error(f"Exception during code redemption: {e}")
        return False

    def run(self):
        """Main application loop."""
        # Prompt for Discord token (required for redeeming Nitro codes)
        ConsoleManager.slow_print("\nEnter your Discord token for redeeming Nitro codes: ", newline=False)
        token_input = input().strip()
        if not token_input:
            logging.critical("A valid token is required to redeem Nitro codes. Exiting...")
            sys.exit(1)
        self.token = token_input

        # Optionally prompt for webhook URL if enabled
        webhook_url = None
        if WEBHOOK_ENABLED:
            ConsoleManager.slow_print("\nEnter webhook URL (or press Enter to skip): ", newline=False)
            url_input = input().strip()
            if url_input and self.validate_webhook(url_input):
                webhook_url = url_input
            elif url_input:
                logging.warning("Invalid webhook URL format - notifications disabled")

        ConsoleManager.slow_print("\nStarting continuous check... (Ctrl+C to exit)\n")
        try:
            while True:
                code = self.generate_code()
                self.checked_count += 1

                if self.test_code(code, webhook_url):
                    # Valid code found; processed in _handle_valid_code.
                    pass
                else:
                    self.invalid_count += 1

                # Prepare and display a dynamic status message.
                status = (f"Checked: {self.checked_count} | "
                          f"Valid: {len(self.valid_codes)} | "
                          f"Invalid: {self.invalid_count}")
                ConsoleManager.set_title(status)
                sys.stdout.write("\r" + status)
                sys.stdout.flush()
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            print()  # Move to a new line.
            logging.info("\nProcess interrupted by user")
            self._display_summary()

    def _display_summary(self):
        """Show final results before exit."""
        summary = (
            f"\n{' Results Summary ':=^40}\n"
            f"• Valid Codes Found: {len(self.valid_codes)}\n"
            f"• Invalid Checks: {self.invalid_count}\n"
            f"• Total Codes Checked: {self.checked_count}\n"
        )
        if self.valid_codes:
            summary += "\nValid Codes:\n" + "\n".join(self.valid_codes)
        print(summary)
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    generator = NitroGenerator()
    generator.run()
