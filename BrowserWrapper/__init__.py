from time import sleep
from random import randint
import logging
from dataclasses import dataclass, field
from selenium import webdriver
from selenium.common.exceptions import SeleniumExceptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from urllib3.connectionpool import log as urllibLogger

# https://packaging.python.org/tutorials/packaging-projects/

# Disable all of the connection logs from appearing.
seleniumLogger.setLevel(logging.WARNING)
urllibLogger.setLevel(logging.WARNING)

@dataclass
class BrowserWrapperConfiguration:
    """Model for scan configuration"""
    
    def __init__(self, BrowserType="Chrome", Remote=False, Headless=False, BrowserWidth=1920,
                 BrowserHeight=1080, SeleniumGridHost="", SeleniumGridPort=4444, Options=[], DesiredCapabilities={}):
        """BrowserWrapperConfiguration instances are used to standardize driver configuration when provided while creating a BrowserWrapper instance.
        
        Keyword Arguments:
            BrowserType {str} -- "Chrome" or "Firefox" (default: {"Chrome"})
            Remote {bool} -- Generates a remote grid browser when enabled, versus a local browser when false (default: {False})
            Headless {bool} -- When set to True, the browser will be headless (default: {False})
            BrowserWidth {int} -- Width to create the browser as (default: {1920})
            BrowserHeight {int} -- Height to create the browser as (default: {1080})
            SeleniumGridHost {str} -- If Remote is True, this is the host of the Selenium Grid Hub (default: {""})
            SeleniumGridPort {int} -- If Remote is True, this is the port of the Selenium Grid Hub (default: {4444})
            Options {list} -- Chrome or Firefox options to enable (default: {[]})
            DesiredCapabilities {dict} -- DesiredCapabilities to provide to the driver (default: {{}})
        """
        self.BrowserType = BrowserType
        self.Remote = Remote
        self.Headless = Headless
        self.BrowserWidth = BrowserWidth
        self.BrowserHeight = BrowserHeight
        self.SeleniumGridHost = SeleniumGridHost
        self.SeleniumGridPort = SeleniumGridPort
        self.Options = Options
        self.DesiredCapabilities = DesiredCapabilities
        
class BrowserWrapper:
    """Wrapper for driver functionality"""

    def __init__(self, Config=BrowserWrapperConfiguration(), Driver=None, Log=None):
        if Config is None and Driver is None:
            raise EnvironmentError("Neither config nor existing driver was provided, one of which is required")
        self._provided_config = Config
        self.action_logging_enabled = True  # If False, prevents logs from being added on wrapped function calls
        self._previous_action_logging_setting = None  # Used to store the last state of logging for use in toggling
        self._log = Log

        if Driver is not None:
            self.CORE = Driver
        elif self._provided_config.BrowserType == "Chrome":
            self.CORE = create_chrome_instance(self._provided_config)
        elif self._provided_config.BrowserType == "Firefox":
            self.CORE = create_firefox_instance(self._provided_config)
        else:
            raise EnvironmentError(f"{self._provided_config.BrowserType} is not a supported browser type")

    ############################################################################################################################################
    ##### Core Functions #######################################################################################################################
    ############################################################################################################################################
    def log_info(self, msg, *args, **kwargs):
        """Wraps info logging functionality so that it can skipped if needed"""
        if self.action_logging_enabled and self._log is not None:
            self._log.info(msg, *args, **kwargs)
        return

    def log_warning(self, msg, *args, **kwargs):
        """Wraps warning logging functionality so that it can skipped if needed"""
        if self.action_logging_enabled and self._log is not None:
            self._log.warning(msg, *args, **kwargs)
        return

    def _disable_logging(self):
        """Used to temporarily disable action logging"""
        if self._previous_action_logging_setting is None:
            self._previous_action_logging_setting = self.action_logging_enabled
            self.action_logging_enabled = False
        return

    def _revert_logging(self):
        """Reverting action logging to original settings"""
        if self._previous_action_logging_setting is not None:
            self.action_logging_enabled = self._previous_action_logging_setting
            self._previous_action_logging_setting = None
        return

    def is_alive(self):
        """Determine the current state of the driver object, useful when needing to detect if the browser crashed

        Returns:
            [bool] -- True if the browser is still alive, False otherwise
        """
        try:
            _ = self.CORE.title
            return True
        except SeleniumExceptions.WebDriverException:
            return False

    def _change_monitor(self, *, previous_data=None):
        """Determines changes due to actions by providing a snapshot of the current state before the action, and comparing to that snapshot afterwards."""
        snapshot = {'URL': self.CORE.current_url}
        if previous_data is None:
            return snapshot
        else:
            for comparison_type, comparison_data in snapshot.items():
                if previous_data[comparison_type] != comparison_data:
                    self._log_info(f"Browser: {comparison_type} changed from {previous_data[comparison_type]} to {comparison_data}")
            return None

    def _format_element(self, element):
        """Changes an element tuple into the format required for unpacking by stripping all items other than locator method and locator string.
        This should be used to interact with CORE functionality, by unpacking the output of this function.

        Arguments:
            element {element tuple} -- Element tuples as defined in PageObjects

        Returns:
            locate_method, locator
        """
        return element[0], element[1]

    ############################################################################################################################################
    ##### Element Status Functions #############################################################################################################
    ############################################################################################################################################
    def elementIsClickable(self, element_tuple):
        """Determine the clickability of an element.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.

        Returns:
            Boolean -- True if element is clickable, False otherwise
        """
        result = self.CORE.find_element(*self._format_element(element_tuple)).is_enabled()
        self._log_info(f"Browser.elementIsClickable: {element_tuple} is {'' if result else 'not '}clickable")
        return result

    def elementIsPresent(self, element_tuple):
        """Determine the current presence of an element.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.

        Returns:
            Boolean -- True if element is present, False otherwise
        """
        try:
            self.CORE.find_element(*self._format_element(element_tuple))
            result = True
        except SeleniumExceptions.NoSuchElementException:
            result = False
        self._log_info(f"Browser.elementIsPresent: {element_tuple} is {'' if result else 'not '}present")
        return result

    def elementIsVisible(self, element_tuple):
        """Determine the current visibility of an element
        Note: An exception will be raised if the element is not present.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.

        Returns:
            Boolean -- True if element is visible, False otherwise
        """
        result = self.CORE.find_element(*self._format_element(element_tuple)).is_displayed()
        self._log_info(f"Browser.elementIsVisible: {element_tuple} is {'' if result else 'not '}present")
        return result

    def elementIsChecked(self, element_tuple):
        """Determine if a checkbox element is checked or unchecked
        Note: An exception will be raised if the element is not present.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.

        Returns:
            Boolean -- True if element is checked, False otherwise
        """
        result = self.CORE.find_element(*self._format_element(element_tuple)).is_selected()
        self._log_info(f"Browser.elementIsChecked: {element_tuple} is {'' if result else 'not '}checked")
        return result

    def alertIsPresent(self, *, accept_if_present=False):
        """Determines if an alert is present

        Arguments:
            accept_if_present {bool} -- If set to True will accept the alert after determining that it is present

        Returns:
            Boolean -- True if alert is present, False if not
        """
        self._disable_logging()
        result = self.waitForAlertPresent(timeout=0)
        if accept_if_present and result:
            self.acceptAlert()
            self._revert_logging()
            self._log_info(f"Browser.alertIsPresent: Alert is present, and has been accepted as accept_if_present=True")
        else:
            self._revert_logging()
            self._log_info(f"Browser.alertIsPresent: Alert is {'' if result else 'not '}present")
        return result

    ############################################################################################################################################
    ##### Wait Functions #######################################################################################################################
    ############################################################################################################################################

    def waitForElementVisible(self, element_tuple, *, timeout=5):
        """Wait a configurable period of time for an element to be visible.
        Note: An exception will be raised if the element is not present

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            timeout {int, defaults to 5} -- Max length of time to wait for the condition

        Returns:
            Boolean -- True if element is initially visible or becomes visible during the wait period, False otherwise
        """
        try:
            WebDriverWait(self.CORE, timeout).until(EC.visibility_of_element_located(self._format_element(element_tuple)))  # Don't unpack, use function to parse out first 2 items
            self._log_info(f"Browser.waitForElementVisible: {element_tuple} is visible within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForElementVisible: {element_tuple} did not become visible after {timeout} seconds")
            return False

    def waitForElementNotVisible(self, element_tuple, *, timeout=5):
        """Wait a configurable period of time for an element to be invisible.
        Note: An exception will be raised if the element is not present

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            timeout {int, defaults to 5} -- Max length of time to wait for the condition

        Returns:
            Boolean -- True if element is initially invisible or becomes invisible during the wait period, False otherwise
        """
        try:
            WebDriverWait(self.CORE, timeout).until(EC.invisibility_of_element_located(self._format_element(element_tuple)))  # Don't unpack, use function to parse out first 2 items
            self._log_info(f"Browser.waitForElementNotVisible: {element_tuple} is invisible within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForElementNotVisible: {element_tuple} did not become invisible after {timeout} seconds")
            return False

    def waitForElementPresent(self, element_tuple, *, timeout=5):
        """Wait a configurable period of time for an element to be present.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            timeout {int, defaults to 5} -- Max length of time to wait for the condition

        Returns:
            Boolean -- True if element is initially present or becomes present wait period, False otherwise
        """
        try:
            WebDriverWait(self.CORE, timeout).until(EC.presence_of_element_located(self._format_element(element_tuple)))  # Don't unpack, use function to parse out first 2 items
            self._log_info(f"Browser.waitForElementPresent: {element_tuple} is present within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForElementPresent: {element_tuple} did not become present after {timeout} seconds")
            return False

    def waitForElementNotPresent(self, element_tuple, *, timeout=5):
        """Wait a configurable period of time for an element to not be present.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            timeout {int, defaults to 5} -- Max length of time to wait for the condition

        Returns:
            Boolean -- True if element is initially not present or becomes not present during the wait period, False otherwise
        """
        try:

            self._disable_logging()
            if self.waitForElementNotVisible(element_tuple, timeout=timeout) is False or self.elementIsPresent(element_tuple) is True:
                self._revert_logging()
                raise SeleniumExceptions.TimeoutException()
            self._revert_logging()
            self._log_info(f"Browser.waitForElementNotPresent: {element_tuple} is present within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForElementNotPresent: {element_tuple} did not become not present after {timeout} seconds")
            return False

    def waitForAlertPresent(self, *, timeout=5):
        """Wait a configurable period of time for an element to be present.

        Arguments:
            timeout {int, defaults to 5} -- Max length of time to wait for the condition

        Returns:
            Boolean -- True if alert is initially present or becomes present during the wait period, False otherwise
        """
        try:
            WebDriverWait(self.CORE, timeout).until(EC.alert_is_present())
            self._log_info(f"Browser.waitForAlertPresent: Alert is present within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForAlertPresent: Alert did not become present after {timeout} seconds")
            return False

    def waitForElementClickable(self, element_tuple, *, timeout=5):
        """Wait a configurable period of time for an element to be clickable.
        Note: An exception will be raised if the element is not present.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            timeout {int, defaults to 5} -- Max length of time to wait for the condition

        Returns:
            Boolean -- True if element is initially clickable or becomes clickable during the wait period, False otherwise
        """
        try:
            WebDriverWait(self.CORE, timeout).until(EC.element_to_be_clickable(self._format_element(element_tuple)))  # Don't unpack, use function to parse out first 2 items
            self._log_info(f"Browser.waitForElementClickable: {element_tuple} is clickable within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForElementClickable: {element_tuple} did not become clickable after {timeout} seconds")
            return False

    def waitForURLToContain(self, url_portion, *, timeout=5):
        """Wait a configurable period of time for the current URL to contain a given string.

        Arguments:
            url_portion {string} -- The string you want to check that the URL contains
            timeout {int} -- Max length of time to wait for the condition
        """
        try:
            WebDriverWait(self.CORE, timeout).until(lambda self: url_portion in self.current_url)
            self._log_info(f"Browser.waitForURLToContain: {self.CORE.current_url} contains {url_portion} within {timeout} seconds")
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForURLToContain: {self.CORE.current_url} does not contain {url_portion} after {timeout} seconds")
            # We're going to capture the timeout as it doesn't matter - the return statement is the bool
        return url_portion in self.CORE.current_url

    def waitForElementTextChange(self, element_tuple, original_text, *, timeout=5):
        """Wait a configurable period of time for an element's text to change
        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            original_text {string} -- The original text you want to see change
            timeout {int} -- Max length of time to wait for the condition
        """
        self.waitForElementVisible(element_tuple, timeout=timeout)
        try:
            self._disable_logging()
            WebDriverWait(self, timeout).until(lambda self: self.getText(element_tuple) != original_text)
            self._revert_logging()
            self._log_info(f"Browser.waitForElementTextChange: {element_tuple} text changed from {original_text} within {timeout} seconds")
            return True
        except SeleniumExceptions.TimeoutException:
            self._log_warning(f"Browser.waitForElementTextChange: {element_tuple} text did not changefrom {original_text} after {timeout} seconds")
            return False

    ############################################################################################################################################
    ##### Action Functions #####################################################################################################################
    ############################################################################################################################################

    def navigate(self, url, *, disable_optimizely=True):
        """Navigate to a url

        Arguments:
            url {string} -- Url to navigate to
        """
        if disable_optimizely:
            url = self.utilities.disable_optimizely(url)
        self._log_info(f"Browser.navigate: Navigating to {url} [disable_optimizely={disable_optimizely}]")
        self.CORE.get(url)
        return

    def getText(self, element_tuple):
        """Get the text of an element.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.

        Returns:
            string -- Text within the element
        """
        result = self.CORE.find_element(*self._format_element(element_tuple)).text
        self._log_info(f"Browser.getText: {element_tuple} text is {result}")
        return result

    def setText(self, element_tuple, text):
        """Clear an element, then sends keys to it. Typically used for form inputs.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            text {string} -- String to type into the element
        """
        self._log_info(f"Browser.setText: Setting text of {element_tuple} to {text}")

        self._disable_logging()
        self.clearText(element_tuple)
        self._revert_logging()

        self.CORE.find_element(*self._format_element(element_tuple)).send_keys(text)
        return

    def clearText(self, element_tuple):
        """Clear the text of an element, typically an input field

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        self._log_info(f"Browser.clearText: Clearing the text of {element_tuple}")
        self.CORE.find_element(*self._format_element(element_tuple)).clear()
        return

    def click(self, element_tuple):
        """Click on an element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        current_state = self._change_monitor()
        self._log_info(f"Browser.click: Clicking {element_tuple}")
        self.CORE.find_element(*self._format_element(element_tuple)).click()
        self._change_monitor(previous_data=current_state)
        return

    def mouseOver(self, element_tuple):
        """Move the mouse over an element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        self._log_info(f"Browser.mouseOver: Moving mouse over {element_tuple}")
        ActionChains(self.CORE).move_to_element(self.CORE.find_element(*self._format_element(element_tuple))).perform()
        return

    def scrollToElement(self, element_tuple):
        """Scroll to an element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        self._log_info(f"Browser.scrollToElement: Scrolling to {element_tuple}")
        self._disable_logging()
        self.mouseOver(element_tuple)
        self._revert_logging()
        return

    def selectOptionByValue(self, element_tuple, select_value):
        """Select an option by value for a select element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            select_value {string} -- Value of the option to select
        """
        self._log_info(f"Browser.selectOptionByValue: Setting {element_tuple} to {select_value}")
        Select(self.CORE.find_element(*self._format_element(element_tuple))).select_by_value(select_value)
        return

    def selectOptionByLabel(self, element_tuple, select_label):
        """Select an option by label (visible text) for a select element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            select_label {string} -- Label (visible text) of the option to select
        """
        self._log_info(f"Browser.selectOptionByLabel: Setting {element_tuple} to {select_label}")
        Select(self.CORE.find_element(*self._format_element(element_tuple))).select_by_visible_text(select_label)
        return

    def selectRandomOption(self, element_tuple):
        """Select an random option for a select element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        self._log_info(f"Browser.selectRandomOption: Selecting random option for {element_tuple}")
        select = Select(self.CORE.find_element(*self._format_element(element_tuple)))
        select.select_by_index(randint(0, len(select.options) - 1))
        _ = self.getSelectedOption(element_tuple)  # To log what was chosen
        return

    def getSelectedOption(self, element_tuple):
        """Get the currently selected option in select element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        select = Select(self.CORE.find_element(*self._format_element(element_tuple)))
        result = select.first_selected_option
        self._log_info(f"Browser.getSelectedOption: {element_tuple} is currently set to {result}")
        return result

    def check(self, element_tuple, *, wrapper_element_tuple=None):
        """Check a checkbox if it's not already. For checkboxes which can't be interacted with directly (hidden but toggled via JS detecting a click on a different object),
        provide a wrapper element in addition for the click instead.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            wrapper_element_tuple {PageObject Element} -- Default is None, tuple representation of element to be used for locating the wrapper, if needed. Wrappers are clicked in
                                                          place of the checkbox element when it is unreachable.
        """
        self._log_info(f"Browser.check: Setting {element_tuple} checkbox to checked")
        checkbox = self.CORE.find_element(*self._format_element(element_tuple))
        if not checkbox.is_selected():
            if wrapper_element_tuple is not None:
                self._log_info(f"Browser.check: Wrapper element was provided, clicking {wrapper_element_tuple} instead")
                self.click(wrapper_element_tuple)
            else:
                self.click(element_tuple)
        else:
            self._log_info(f"Browser.check: Skipping action as {element_tuple} is already checked")
        return

    def uncheck(self, element_tuple, *, wrapper_element_tuple=None):
        """Uncheck a checkbox if it's not already. For checkboxes which can't be interacted with directly (hidden but toggled via JS detecting a click on a different object),
        provide a wrapper element in addition for the function to click instead.

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            wrapper_element_tuple {PageObject Element} -- Default is None, tuple representation of element to be used for locating the wrapper, if needed. Wrappers are clicked in
                                                          place of the checkbox element when it is unreachable.
        """
        self._log_info(f"Browser.uncheck: Setting {element_tuple} checkbox to unchecked")
        checkbox = self.CORE.find_element(*self._format_element(element_tuple))
        if checkbox.is_selected():
            if wrapper_element_tuple is not None:
                self._log_info(f"Browser.check: Wrapper element was provided, clicking {wrapper_element_tuple} instead")
                self.click(wrapper_element_tuple)
            else:
                self.click(element_tuple)
        else:
            self._log_info(f"Browser.check: Skipping action as {element_tuple} is already unchecked")
        return

    def delay(self, length):
        """Delay for a specified period of time. Should be used as a last resort if no other wait function works.

        Arguments:
            length {int} -- Length of time to delay
        """
        self._log_info(f"Browser.delay: Sleeping for {length} seconds")
        return sleep(length)

    def getAttribute(self, element_tuple, attribute):
        """Get the value of an element's attribute

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            attribute {string} -- Attribute to collect the value of

        Returns:
            string -- Value of the provided attribute
        """
        result = self.CORE.find_element(*self._format_element(element_tuple)).get_attribute(attribute)
        self._log_info(f"Browser.getAttribute: {attribute} attribute of {element_tuple} is {result}")
        return result

    def sendKeys(self, element_tuple, keys):
        """Send keys to an element

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
            keys {string} -- Keys to send to the element
        """
        self._log_info(f"Browser.sendKeys: Sending {keys} to {element_tuple}")
        self.CORE.find_element(*self._format_element(element_tuple)).send_keys(*keys)
        return

    def getUrl(self):
        """Get URL of the current window.

        Returns:
            string -- Current URL
        """
        result = self.CORE.current_url
        self._log_info(f"Browser.getUrl: Current URL is {result}")
        return result

    def refresh(self):
        """Refresh the current window."""
        self._log_info(f"Browser.refresh: Refreshing the page")
        self.CORE.refresh()
        return

    def switchToFrame(self, element_tuple):
        """Switches to the specified iframe in the DOM

        Arguments:
            element_tuple {PageObject Element} -- Tuple representation of element typically defined on PageObjects used for locating the element.
        """
        self._log_info(f"Browser.switchToFrame: Switching to iframe {element_tuple}")
        self.CORE.switch_to.frame(self.CORE.find_element(*self._format_element(element_tuple)))
        return

    def switchToDefaultContent(self):
        """Switches from iframe to default content in the DOM"""
        self._log_info(f"Browser.switchToDefaultContent: Switching to default content")
        self.CORE.switch_to.default_content()
        return

    def switchToWindowByIndex(self, index):
        """Switches to window with provided index

        Arguments:
            index {int} -- Zero-based index of window to switch to.
        """
        self._log_info(f"Browser.switchToWindowByIndex: Switching to window at index {index}")
        self.CORE.switch_to.window(self.CORE.window_handles[index])
        return

    def deleteAllCookies(self):
        """Deletes all cookies"""
        self.CORE.delete_all_cookies()
        return

    def acceptAlert(self):
        """Accepts an active alert on a page"""
        self._log_info(f"Browser.acceptAlert: Accepting alert")
        alert = self.CORE.switch_to.alert
        alert.accept()
        return

    def back(self):
        """Uses the browser back functionality to go to the previous page."""
        self._log_info(f"Browser.back: Telling browser to return to previous page")
        self.CORE.back()
        return


def create_chrome_instance(provided_config=None):
    """Generates a ChromeDriver instance in compliance with configured settings

    Returns:
        [ChromeDriver Instance] -- Configured Local or Remote ChromeDriver
    """
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents use of dev/shm, preventing memory shortages in containers
    chrome_options.add_argument(f"--window-size={BrowserWrapper.BrowserWidth},{BrowserWrapper.BrowserHeight}")
    for option in provided_config.Options:
        chrome_options.add_argument(option)
        
    if provided_config.Headless:
        chrome_options.add_argument("--headless")

    # Enable Browser Console Log Collection
    capabilities = chrome_options.to_capabilities()
    desired_capabilities = DesiredCapabilities.CHROME
    capabilities.update(Browser.DesiredCapabilities)
    desired_capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}

    if provided_config.Remote is False:
        from webdriver_manager.chrome import ChromeDriverManager
        return webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options, desired_capabilities=desired_capabilities)
    else:
        return webdriver.Remote(command_executor=f"{provided_config.SeleniumGridHost}:{provided_config.SeleniumGridPort}/wd/hub", desired_capabilities=capabilities)


def create_firefox_instance(provided_config=None):
    """Generates a GeckoDriver instance in compliance with configured settings

    Returns:
        [GeckoDriver Instance] -- Configured Local or Remote GeckoDriver
    """
    firefox_options = FirefoxOptions()
    firefox_options.add_argument(f"--width={provided_config.BrowserWidth}")
    firefox_options.add_argument(f"--height={provided_config.BrowserHeight}")
    for option in provided_config.Options:
        firefox_options.add_argument(option)
        
    if provided_config.Headless:
        firefox_options.headless = True
        
    
    capabilities = firefox_options.to_capabilities()
    capabilities.update(provided_config.DesiredCapabilities)

    if provided_config.Remote is False:
        from webdriver_manager.firefox import GeckoDriverManager
        return webdriver.Firefox(executable_path=f'{GeckoDriverManager().install()}', desired_capabilities=firefox_options)
    else:
        return webdriver.Remote(command_executor=f"{provided_config.SeleniumGridHost}:{provided_config.SeleniumGridPort}/wd/hub", desired_capabilities=capabilities)
    
if __name__ == '__main__':
    config = BrowserWrapperConfiguration(ho)