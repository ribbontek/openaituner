# openaituner

This experimental project massages scraped website data for fine-tuning purposes in OpenAI. 

It scrapes data from Megaport docs website & takes advantage of generative AI for 
writing sample question and answer data that will be used for training an AI. 
These of course had to be cleaned up as the generated responses weren't always accurate in structuring the question and answers in json 
& would sometimes write unrelated responses.

In the end, after uploading to OpenAI to fine-tune, the fine-tuned model didn't return promising results and answers were very short (blame the data for this),
so another approach will have to be explored in structuring question & answer responses to train the model

---

### setting up the project

`python3.10 -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

`python script.py --help`

Create an application.properties file with the following config

```
[OpenAI]
api_key=<YOUR_OPENAI_KEY>
```

---

### scripts:

The links function scraped the Megaport docs website for all the links in the nav bar
```bash
python script.py links
```

The scraper function scrapes all the pages in the Megaport docs website using the scraped links
```bash
python script.py scraper
```

The generate-question-answer function uses the scraped data with OpenAI to generate questions and answers & stores the results in a json format
```bash
python script.py generate-question-answer
```

The collate-questions function collates the question and answer json data generated from OpenAI for all the pages from Megaport docs website
(Some manual data cleaning is required before trying this step)
```bash
python script.py collate-questions
```

The tune-openai function uses the collated data & generates a structure applicable for fine-tuning OpenAI models. 
It then sends this training file to OpenAI
```bash
python script.py tune-openai
```

The check-tune-openai function polls OpenAI using the fine-tuning-job data that was generated when triggering the tune-openai script.
Though you receive an email when the fine-tuning job is done & can often take longer than what is expected depending on how much data is provided to OpenAI
```bash
python script.py check-tune-openai
```

---

### helper functions:

Added this to bash aliases for installing python packages
```shell
function pip-install-save {
    pip install $1 && pip freeze | grep $1 >> requirements.txt
}
```

```bash
pip-install-save pyfiglet
```

