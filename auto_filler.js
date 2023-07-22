const playwright = require('playwright');
const readline = require('readline');
const axios = require('axios');

class Crawler {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
  }

  async crawl() {
    try {
      this.browser = await playwright.chromium.launch();
      this.context = await this.browser.newContext();
      this.page = await this.context.newPage();
      const url = 'https://example.com'; // Replace with the URL you want to crawl
      await this.page.goto(url);
      await this.page.waitForLoadState('domcontentloaded');
      const visibledom = await this.page.innerText('body');
      const xpath_dict = this.getXpathDict(); // Replace with your Xpath dictionary logic
      const iframes_list = this.getIframesList(); // Replace with your iframe list logic
      return [visibledom, xpath_dict, iframes_list];
    } catch (error) {
      console.error('Error during crawling:', error);
    } finally {
      await this.browser.close();
    }
  }

  getXpathDict() {
    // Replace with your logic to extract and store the Xpath dictionary
    // For example:
    const xpath_dict = {
      'element1': { 'id': 'element1_id', 'other_attrs': 'other_attrs_value' },
      'element2': { 'id': 'element2_id', 'other_attrs': 'other_attrs_value' },
      // Add more elements as needed
    };
    return xpath_dict;
  }

  getIframesList() {
    // Replace with your logic to extract and store the list of iframes
    // For example:
    const iframes_list = [
      { 'id': 1, 'frame': 'iframe1' },
      { 'id': 2, 'frame': 'iframe2' },
      // Add more iframes as needed
    ];
    return iframes_list;
  }

  async getIframeById(id, iframes_list) {
    const iframe = iframes_list.find((item) => item.id === id);
    return iframe ? iframe.frame : null;
  }

  async clickElement(id, xpath_dict, iframes_list) {
    const xpath = this.getXpathById(id, xpath_dict);
    const frame = await this.getIframeByXpath(xpath, iframes_list);

    if (frame) {
      const xpathWithoutIframe = xpath.split('/').slice(1).join('/');
      await frame.click(`xpath=${xpathWithoutIframe}`);
    } else {
      await this.page.click(`xpath=${xpath}`);
    }
  }

  async typeIntoElement(id, xpath_dict, iframes_list, text) {
    const xpath = this.getXpathById(id, xpath_dict);
    const frame = await this.getIframeByXpath(xpath, iframes_list);

    if (frame) {
      const xpathWithoutIframe = xpath.split('/').slice(1).join('/');
      await frame.fill(`xpath=${xpathWithoutIframe}`, text);
    } else {
      await this.page.fill(`xpath=${xpath}`, text);
    }
  }

  async typeAndSubmit(xpath_dict, iframes_list, id, text) {
    const xpath = this.getXpathById(id, xpath_dict);
    const frame = await this.getIframeByXpath(xpath, iframes_list);

    if (frame) {
      const xpathWithoutIframe = xpath.split('/').slice(1).join('/');
      await frame.fill(`xpath=${xpathWithoutIframe}`, text);
      await frame.press(`xpath=${xpathWithoutIframe}`, 'Enter');
    } else {
      await this.page.fill(`xpath=${xpath}`, text);
      await this.page.press(`xpath=${xpath}`, 'Enter');
    }
  }

  async scrollUp() {
    const currentScrollPosition = await this.page.evaluate('window.pageYOffset');
    const viewportHeight = this.page.viewportSize['height'];
    const newScrollPosition = Math.max(currentScrollPosition - viewportHeight, 0);
    await this.page.evaluate(`window.scrollTo(0, ${newScrollPosition})`);
  }

  async scrollDown() {
    const currentScrollPosition = await this.page.evaluate('window.pageYOffset');
    const viewportHeight = this.page.viewportSize['height'];
    const newScrollPosition = currentScrollPosition + viewportHeight;
    await this.page.evaluate(`window.scrollTo(0, ${newScrollPosition})`);
  }

  async goToURL(url) {
    try {
      const response = await this.page.goto(url, { timeout: 0 });
      await this.page.waitForLoadState('domcontentloaded');
      const status = response ? response.status : 'unknown';
      console.log(`Navigating to ${url} returned status code ${status}`);
    } catch (error) {
      console.error('Error during navigation:', error);
    }
  }

  async goPageBack() {
    try {
      const response = await this.page.goBack({ timeout: 60000 });
      await this.page.waitForLoadState('domcontentloaded');
      if (response) {
        console.log(`Navigated back to the previous page with URL '${response.url}'. Status code ${response.status}`);
      } else {
        console.log('Unable to navigate back; no previous page in the history');
      }
    } catch (error) {
      console.error('Error during navigation:', error);
    }
  }

  getXpathById(id, xpathDict) {
    for (const [xpath, attrs] of Object.entries(xpathDict)) {
      if (attrs.id === id) {
        return xpath;
      }
    }
    return null;
  }

  async getIframeByXpath(xpath, iframesList) {
    const iframeId = Number(xpath.split('/')[1]); // extract the iframe_id from the xpath
    if (iframeId) {
      const iframe = iframesList.find((item) => item.id === iframeId);
      return iframe ? this.page.frame({ url: iframe.frame }) : null;
    }
    return null;
  }
}

function get_gpt_command(text) {
  // Replace this function with your logic to generate GPT command based on input text
  // For example:
  const gptCmd = `gpt.generate("${text}")`;
  return gptCmd;
}

function gpt_for_text_summarization(text) {
  // Replace this function with your logic to summarize text using GPT
  // For example:
  const summarizedText = text.slice(0, 200); // Just returning the first 200 characters as a summary
  return summarizedText;
}

function gpt_for_drop_down(optionData, text) {
  // Replace this function with your logic to process drop-down options using GPT
  // For example:
  const selectedOption = optionData.split(',')[0]; // Just returning the first option
  return selectedOption;
}

async function pdfCall() {
  // Replace this function with your logic to generate PDF or handle form submission
  console.log('Form submitted or PDF generated.');
}

// Create a new instance of the Crawler class
const _crawler = new Crawler();

// Main function to execute the crawling and form filling
async function on_submit_clicked() {
  const url = 'https://example.com'; // Replace with the URL you want to crawl
  await _crawler.goToURL(url);

  const [visibledom, xpath_dict, iframes_list] = await _crawler.crawl();
  console.log('iframes_list', iframes_list);
  const string_text = visibledom;
  console.log('string_text', string_text);
  const gpt_cmd = get_gpt_command(string_text);
  console.log('gpt command: ', gpt_cmd);
  const clicked = false;
  let data = {};

  if (gpt_cmd.length > 0) {
    try {
      data = eval(gpt_cmd);
    } catch (e) {
      console.log(`Error in evaluating gpt_cmd: ${e}`);
      _crawler.scroll_down();
    }

    if (data['Powered by Typeform']) {
      delete data['Powered by Typeform'];
    }

    const swapped_data = {};

    for (const [key, value] of Object.entries(data)) {
      if (typeof key === 'number') {
        swapped_data[String(value)] = key;
      } else {
        swapped_data[key] = value;
      }
    }

    let previous_llmaanswer = '';

    for (const [key, value] of Object.entries(data)) {
      console.log('key', key);
      let result = file_path({ query: key }); // Replace file_path with your logic to query the file
      let llmaanswer = result['result'];
      let Text_summarized = gpt_for_text_summarization(llmaanswer);
      console.log('llmaanswer', llmaanswer);
      console.log('Text_summarized', Text_summarized);
      let clicked = false;
      const sub_mappings = {};

      if (Array.isArray(value) && value.every((item) => typeof item === 'object')) {
        const optiondata_str = JSON.stringify(value);
        const similarity_check = gpt_for_drop_down(optiondata_str, Text_summarized);
        console.log('similarity_check', similarity_check);

        if (similarity_check && similarity_check !== 'None') {
          data = eval(similarity_check);
          for (const [key, value] of Object.entries(data)) {
            await _crawler.clickElement(value, xpath_dict, iframes_list);
            if (['submit', 'subscribe'].includes(key.toLowerCase())) {
              clicked = true;
              pdfCall();
            }
          }
        } else {
          const user_input = await getInputFromUser(`Enter input for ${key} with optionIDs ${value}: `);
          console.log('User input:', user_input);
          llmaanswer = user_input;
          console.log(typeof llmaanswer);
          await _crawler.clickElement(llmaanswer, xpath_dict, iframes_list);
        }
      } else {
        const keywords = ["don't know", "don't", "unsure"];
        if (keywords.some((keyword) => Text_summarized.includes(keyword))) {
          const user_input = await getInputFromUser(`Enter input for ${key}: `);
          console.log('User input:', user_input);
          Text_summarized = user_input;
        }

        if (['submit', 'subscribe'].includes(key.toLowerCase())) {
          await _crawler.typeAndSubmit(xpath_dict, iframes_list, key, Text_summarized);
        } else {
          await _crawler.typeIntoElement(value, xpath_dict, iframes_list, Text_summarized);
        }
      }
    }

    if (!clicked) {
      await _crawler.scroll_down();
    }
    await sleep(5000);
  }
}

function getInputFromUser(prompt) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question(prompt, (input) => {
      rl.close();
      resolve(input);
    });
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Call the main function
on_submit_clicked();
