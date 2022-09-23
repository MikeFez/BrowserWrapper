# BrowserWrapper

## What is BrowserWrapper?
BrowserWrapper is a python3 package designed to simplify the management and usage of selenium webdrivers, and the elements it may interact with. BrowserWrapper takes care of installing & maintaining webdrivers by wrapping [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager), and furthermore wraps many common selenium commands in order to simplify web-based activities.

It's as simple as `Browser = BrowserWrapper()`!

BrowserWrapper documentation can be found [here](https://mikefez.github.io/BrowserWrapper/).

## Installation
```bash
$ pip install BrowserWrapper
```

## The Browser Object (aka BrowserWrapper)
The `BrowserWrapper` class wraps the core functionality of the selenium webdriver, allowing us to add functionality which simplifies interactions with the Selenium WebDriver object. Core selenium functionality is still accessible via Browser.CORE.{Webdriver_Function_Here}. Examples below:

```python
from BrowserWrapper import BrowserWrapper

Browser = BrowserWrapper()

element = (By.CSS_SELECTOR, '#firstName')

# BrowserWrapper 'wrapped' functions:
Browser.navigate("https://google.com")
if not Browser.elementIsVisible(element):
    Browser.waitForElementPresent(element, timeout=3)  # timeout is optional as the default is 5
Browser.click(element)
Browser.quit()

# Selenium WebDriver 'raw' functions:
Browser.CORE.delete_all_cookies()
```

More advanced browser configuration can be managed through a BrowserWrapperConfiguration() object.
```python
from BrowserWrapper import BrowserWrapper, BrowserWrapperConfiguration

browser_config = BrowserWrapperConfiguration(
    BrowserType="Chrome", # Or Firefox
    Remote=False,
    SeleniumGridHost="192.168.1.150",
    SeleniumGridPort=4444,
    Headless=True,
    BrowserWidth=1920,
    BrowserHeight=1080,
    Options=[],  # https://chromedriver.chromium.org/capabilities#h.p_ID_106
    DesiredCapabilities={} # https://chromedriver.chromium.org/capabilities#h.p_ID_52
)
Browser = BrowserWrapper(config=browser_config)
```

## Element declarations for use within the BrowserWrapper
Interacting with elements requires them to be declared in a standardized format, tuples with the first element being the locater method and the second being the locator string. This requires the import `from selenium.webdriver.common.by import By`. [Link to selenium's reference](https://www.selenium.dev/selenium/docs/api/py/webdriver/selenium.webdriver.common.by.html).

```python
from selenium.webdriver.common.by import By

class_name_example = (By.CLASS_NAME, 'content')
css_selector_example = (By.CSS_SELECTOR, '#lastName')
xpath_example = (By.XPATH, '//tagname[@attribute="value"]')
id_example = (By.ID, 'session_key')
link_text_example = (By.LINK_TEXT, 'https://www.google.com')
partial_link_text_example = (By.PARTIAL_LINK_TEXT, 'google.com')
name_example = (By.NAME, 'password')
tag_name_example = (By.TAG_NAME, 'input')
```

The methods within the BrowserWrapper class format this tuple for use with core selenium functionality.

## BrowserWrapper Method Parameters
BrowserWrapper methods tend to be self explanatory, such as when using .navigate(), a URL is expected to be provided. However, many methods have optional parameters. These parameters are not provided via positional arguments, and therefore must be provided via keyword and value. This is enforced - you'll receive an exception if you attempt to override a parameter with a default value via the positional arguments instead of keyword arguments. This is done to enhance readability.

Note the use of the `timeout=10` parameter in `waitForElementPresent()` - any optional parameters (parameters which default to a value if not called) are **required** to be called via keyword if you plan on overriding the default value. That being said, if you're fine with the default value, you can skip specifying the keyword completely.

```python
# Below is an example of a function in which the arguments being passed are not easily identifiable. Are we stating that the alert is indeed present to the Browser? What does True mean here?
Browser.alertIsPresent(True)

# Ah, we're checking to see if an alert is present and accepting it if so!
Browser.alertIsPresent(accept_if_present=True)

# Here we're waiting for an element to be present, but what does 10 indicate? (alright, it's probably the timeout, but still!)
Browser.waitForElementPresent(self, submit_button, 10)

# Providing timeout=10 vs just 10 provides clarity in code as to what 10's purpose is
Browser.waitForElementPresent(self, submit_button, timeout=10)
```

## Accessing typical webdriver functionality
While BrowserWrapper simplifies common interactions, all core selenium functionality can be accessed via the `Browser.CORE` attribute.

```python
from BrowserWrapper import BrowserWrapper
from selenium.webdriver.common.by import By

Browser = BrowserWrapper()

Browser.CORE.delete_all_cookies()
Browser.CORE.get("http://www.python.org")
assert "Python" in Browser.CORE.title
elem = Browser.CORE.find_element(By.NAME, "q")
elem.clear()
Browser.CORE.send_keys("pycon")
Browser.CORE.send_keys(Keys.RETURN)
assert "No results found." not in Browser.CORE.page_source
Browser.CORE.close()
```