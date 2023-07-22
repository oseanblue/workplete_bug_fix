import time
import json
import pdfx
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QFileDialog, QLineEdit, QMainWindow, QWidget, QInputDialog
from playwright.sync_api import Page, Browser, sync_playwright
import openai
import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pymupdf import PyPDF
import math
from typing import List, Dict, Tuple
import playwright.sync_api._generated.playwright as playwright
import playwright.sync_api
import os

class Crawler:
    def __init__(self):
        self.browser = sync_playwright().start()
        self.page = None

    def crawl(self):
        # Define the visible DOM and the iframe list
        visibledom = []
        iframe_list = []
        self.page = self.browser.new_page()

        # Callback to handle the DOMContentLoaded event
        def handle_dom_content(event):
            nonlocal visibledom, iframe_list
            visibledom = self.page.inner_text("html").split("\n")
            iframe_list = self.get_iframe_list(self.page.frames)

        self.page.on("domcontentloaded", handle_dom_content)

        # Navigate to the page and wait for the DOMContentLoaded event
        self.page.goto("https://newchip.com/", timeout=0)
        self.page.wait_for_load_state()

        # Remove the callback to avoid handling future events
        self.page.remove_listener("domcontentloaded", handle_dom_content)

        return visibledom, self.get_xpath_dict(self.page), iframe_list

    @staticmethod
    def get_iframe_list(frames: List[Page.Frame]) -> List[Tuple[int, Page.Frame]]:
        iframe_list = []
        for frame in frames:
            iframe_id = frame.url.rsplit("/", 1)[-1]  # Extract the iframe_id from the URL
            if iframe_id.isdigit():
                iframe_list.append((int(iframe_id), frame))
        return sorted(iframe_list, key=lambda x: x[0])

    @staticmethod
    def get_xpath_dict(page: Page) -> Dict[str, Dict[str, str]]:
        # Recursive function to extract the XPath of each visible element in the page
        def get_xpath_recursively(element: playwright.ElementHandle) -> Dict[str, Dict[str, str]]:
            xpath_dict = {}
            if element.is_visible():
                tag_name = element.tag_name().lower()
                inner_text = element.inner_text()
                attributes = element.get_attributes()
                if tag_name not in ["script", "style"] and inner_text.strip() != "":
                    xpath = element.locator()
                    xpath_dict[xpath] = {"tag": tag_name, "text": inner_text, "attributes": attributes}

            for child_element in element.query_selector_all("*"):
                xpath_dict.update(get_xpath_recursively(child_element))

            return xpath_dict

        # Start the recursive function from the document root
        return get_xpath_recursively(page)

    def get_xpath_by_id(self, id, xpath_dict):
        for xpath, attrs in xpath_dict.items():
            if attrs.get('id') == id:
                return xpath
        return None

    def get_iframe_by_xpath(self, xpath, iframes_list):
        iframe_id = xpath.split("/")[0]  # Extract the iframe_id from the xpath
        if iframe_id:  # Check if iframe_id is not an empty string
            for id, frame in iframes_list:
                if id == int(iframe_id):
                    return frame
        return None

    def click_element(self, id, xpath_dict, iframes_list):
        xpath = self.get_xpath_by_id(id, xpath_dict)
        frame = self.get_iframe_by_xpath(xpath, iframes_list)
        if frame:
            # Remove the iframe_id from the xpath
            xpath = re.sub(r'^\d+/', '/', xpath)
            if xpath.split('/')[-1].startswith('option'):
                # If the element is an option, get its parent select element and select the option
                select_xpath = '/'.join(xpath.split('/')[:-1])
                select_element = frame.query_selector(f'xpath={select_xpath}')
                option_element = frame.query_selector(f'xpath={xpath}')
                value = option_element.get_attribute('value')
                select_element.select_option(value)
            else:
                frame.click(f'xpath={xpath}')
        else:
            if xpath.split('/')[-1].startswith('option'):
                # If the element is an option, get its parent select element and select the option
                select_xpath = '/'.join(xpath.split('/')[:-1])
                select_element = self.page.query_selector(f'xpath={select_xpath}')
                option_element = self.page.query_selector(f'xpath={xpath}')
                value = option_element.get_attribute('value')
                select_element.select_option(value)
            else:
                self.page.click(f'xpath={xpath}')

    def type_into_element(self, id, xpath_dict, iframes_list, text):
        xpath = self.get_xpath_by_id(id, xpath_dict)
        frame = self.get_iframe_by_xpath(xpath, iframes_list)
        if frame:
            # Remove the iframe_id from the xpath
            xpath = re.sub(r'^\d+/', '/', xpath)
            frame.fill(f'xpath={xpath}', text)
        else:
            self.page.fill(f'xpath={xpath}', text)

    def type_and_submit(self, xpath_dict, iframes_list, id, text):
        xpath = self.get_xpath_by_id(id, xpath_dict)
        frame = self.get_iframe_by_xpath(xpath, iframes_list)
        if frame:
            # Remove the iframe_id from the xpath
            xpath = re.sub(r'^\d+/', '/', xpath)
            frame.fill(f'xpath={xpath}', text)
            frame.press(f'xpath={xpath}', 'Enter')
        else:
            self.page.fill(f'xpath={xpath}', text)
            self.page.press(f'xpath={xpath}', 'Enter')

    def scroll_up(self):
        current_scroll_position = self.page.evaluate('window.pageYOffset')
        viewport_height = self.page.viewport_size['height']
        new_scroll_position = max(current_scroll_position - viewport_height, 0)
        self.page.evaluate(f'window.scrollTo(0, {new_scroll_position})')

    def scroll_down(self):
        current_scroll_position = self.page.evaluate('window.pageYOffset')
        viewport_height = self.page.viewport_size['height']
        new_scroll_position = current_scroll_position + viewport_height
        self.page.evaluate(f'window.scrollTo(0, {new_scroll_position})')

    def go_to_url(self, url):
        try:
            response = self.page.goto(url=url, timeout=0)
            self.page.wait_for_load_state()
            status = response.status if response else "unknown"
            print(f"Navigating to {url} returned status code {status}")
        except playwright._impl._api_types.TimeoutError:
            print("Navigation to the URL took too long!")

    def go_page_back(self):
        try:
            response = self.page.go_back(timeout=60000)
            self.page.wait_for_load_state()
            if response:
                print(
                    f"Navigated back to the previous page with URL '{response.url}'."
                    f" Status code {response.status}"
                )
            else:
                print("No previous page to navigate back to.")
        except playwright._impl._api_types.TimeoutError:
            print("Navigation back took too long!")

    def go_page_forward(self):
        try:
            response = self.page.go_forward(timeout=60000)
            self.page.wait_for_load_state()
            if response:
                print(
                    f"Navigated forward to the next page with URL '{response.url}'."
                    f" Status code {response.status}"
                )
            else:
                print("No next page to navigate forward to.")
        except playwright._impl._api_types.TimeoutError:
            print("Navigation forward took too long!")

    def close(self):
        self.browser.close()


def get_gpt_command(string_text):
    # Use GPT-3 to generate commands based on the visible DOM text
    # Your GPT-3 integration code here...
    # For illustration purposes, let's assume a dummy command is returned.
    return "{'button1': 'Click me'}"


def gpt_for_text_summarization(text):
    # Use GPT-3 to summarize the text
    # Your GPT-3 integration code here...
    # For illustration purposes, let's assume a dummy summarized text is returned.
    return "This is a summarized version of the text."


def gpt_for_drop_down(optiondata_str, text):
    # Use GPT-3 to select the correct option based on the available options and the summarized text
    # Your GPT-3 integration code here...
    # For illustration purposes, let's assume a dummy command is returned.
    return "{'option2': 'Select me'}"


def pdf_call():
    # Your PDF generation code here...
    # For illustration purposes, let's assume a dummy PDF file is generated.
    pdf_file = "example.pdf"
    print(f"PDF generated: {pdf_file}")


def load_file():
    options = QFileDialog.Options()
    options |= QFileDialog.ReadOnly
    options |= QFileDialog.ExistingFile
    file_name, _ = QFileDialog.getOpenFileName(window, "Open File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
    return file_name


def on_submit_clicked():
    url = url_input.text()  # Get the URL from the input box
    if url:
        _crawler.go_to_url(url)
    file_path = load_file()
    if file_path:
        # Execute functions that require the URL and file
        gpt_cmd = ""
        while True:
            start = time.time()
            visibledom, xpath_dict, iframes_list = _crawler.crawl()
            print("iframes_list", iframes_list)
            xpath_dict = {k: v for k, v in xpath_dict.items() if v is not None}
            string_text = "\n".join(visibledom)
            print("string_text", string_text)
            gpt_cmd = get_gpt_command(string_text)
            print("gpt command: ", gpt_cmd)
            gpt_cmd = gpt_cmd.strip()
            clicked = False
            data = {}
            if len(gpt_cmd) > 0:
                try:
                    data = eval(gpt_cmd)
                except Exception as e:
                    print(f"Error in evaluating gpt_cmd: {e}")
                    _crawler.scroll_down()
                if 'Powered by Typeform' in data:
                    del data['Powered by Typeform']
                swapped_data = {}

                for key, value in data.items():
                    if isinstance(key, int):
                        swapped_data[str(value)] = key
                    else:
                        swapped_data[key] = value
                previous_llmaanswer = ''
                for key, value in data.items():
                    print("key", key)
                    result = file_path({"query": key})
                    llmaanswer = result['result']
                    Text_summarized = gpt_for_text_summarization(llmaanswer)
                    print("llmaanswer", llmaanswer)
                    print("Text_summarized", Text_summarized)
                    clicked = False
                    sub_mappings = {}
                    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                        optiondata_str = json.dumps(value)
                        similarity_check = gpt_for_drop_down(optiondata_str, Text_summarized)
                        print("similarity_check", similarity_check)
                        if similarity_check is not None and 'None' not in similarity_check:
                            data = eval(similarity_check)
                            for key, value in data.items():
                                _crawler.click_element(value, xpath_dict, iframes_list)
                                if key.lower() in ['submit', 'subscribe']:
                                    clicked = True
                                    pdf_call()
                        else:
                            user_input, ok_pressed = QInputDialog.getText(window, "Popup Window",
                                                                        f"Enter input for {key} with optionIDs {value}: ")
                            if ok_pressed:
                                print("User input:", user_input)
                                llmaanswer = user_input
                                print(type(llmaanswer))
                                _crawler.click_element(llmaanswer, xpath_dict, iframes_list)
                    else:
                        try:
                            keywords = ["don't know", "don't", "unsure"]
                            if any(keyword in Text_summarized for keyword in keywords):
                                user_input, ok_pressed = QInputDialog.getText(window, "Popup Window",
                                                                                f"Enter input for {key}: ")
                                if ok_pressed:
                                    print("User input:", user_input)
                                    Text_summarized = user_input
                            if key.lower() in ['submit', 'subscribe']:
                                _crawler.type_and_submit(xpath_dict, iframes_list, key, Text_summarized)
                            else:
                                _crawler.type_into_element(value, xpath_dict, iframes_list, Text_summarized)
                        except:
                            if key.lower() in ['submit', 'subscribe']:
                                _crawler.click_element(key, xpath_dict, iframes_list)
                                clicked = True
                                pdf_call()
                            else:
                                _crawler.click_element(value, xpath_dict, iframes_list)

                if not clicked:
                    _crawler.scroll_down()
                time.sleep(5)


# Create the application
app = QApplication([])

# Create the main window
window = QMainWindow()
window.setWindowTitle("Form Filler")
window.setGeometry(100, 100, 800, 600)

# Create the main widget
main_widget = QWidget(window)
window.setCentralWidget(main_widget)

# Create input elements
url_label = QLabel("URL:")
url_input = QLineEdit(main_widget)
url_input.setText("https://newchip.com/")  # Set a default URL for testing purposes

# Create buttons
submit_button = QPushButton("Submit", main_widget)

# Connect buttons to functions
submit_button.clicked.connect(on_submit_clicked)

# Arrange widgets in a layout
layout = QVBoxLayout()
layout.addWidget(url_label)
layout.addWidget(url_input)
layout.addWidget(submit_button)
main_widget.setLayout(layout)

# Initialize the crawler
_crawler = Crawler()

# Show the window
window.show()

# Run the application
app.exec_()
