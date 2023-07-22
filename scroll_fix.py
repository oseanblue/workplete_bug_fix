def on_submit_clicked():
    url = url_input.text()  # Get the URL from the input box
    if url:
        _crawler.goToURL(url)
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
                                    pdfCall()
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
                                pdfCall()
                            else:
                                _crawler.click_element(value, xpath_dict, iframes_list)

                if not clicked:
                    _crawler.scroll_down()
                time.sleep(5)
