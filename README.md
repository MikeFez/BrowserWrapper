# BrowserWrapper

## What is BrowserWrapper?
BrowserWrapper is a python3 package designed to simplify the management and usage of selenium webdrivers, and the elements it may interact with. BrowserWrapper takes care of installing & maintaining webdrivers by wrapping [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager), and furthermore wraps many common selenium commands in order to simplify web-based activities.

It's as simple as `Browser = BrowserWrapper()`!

BrowserWrapper documentation can be found [here](https://mikefez.github.io/BrowserWrapper/BrowserWrapper/).

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

## Element declarations for use within the BrowserWrapper
Interacting with elements requires them to be declared in a standardized format, tuples with the first element being the locater method and the second being the locator string. This requires the import `from selenium.webdriver.common.by import By`.

```python
from selenium.webdriver.common.by import By

first_name_input = (By.CSS_SELECTOR, '#firstName')
last_name_input = (By.CSS_SELECTOR, '#lastName')
email_input = (By.CSS_SELECTOR, 'input[name="Email"')
country_select = (By.CSS_SELECTOR, 'select[name="Country"]')
submit_button = (By.CSS_SELECTOR, '#submit')
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
