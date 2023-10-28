import json
import os
import re
import time

import configparser
import pyfiglet
import typer

import openai
from modules.text_scraper.main import extract_text_from_url, extract_links_from_nav

app = typer.Typer()


def map_to_list_object(url, link):
    name = link.replace(url, "")
    if name.endswith("/"):
        name = name[:-1]
    name = name.replace("/", "-")
    return {"name": name, "url": link}


@app.command()
def links():
    url = "https://docs.megaport.com/"
    links_found = extract_links_from_nav(url)
    if links_found:
        print("Found total links: " + str(len(links_found)))
        file_name = "links.json"
        with open(file_name, 'w') as file:
            json_data = [map_to_list_object(url, item) for item in links_found]
            file.write(json.dumps(json_data, indent=4))
            print("Created file: " + file_name)


@app.command()
def scraper():
    json_file_path = "links.json"
    # Load URLs from a JSON file
    if os.path.exists(json_file_path):
        print("Found " + json_file_path)
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        download_dir = "downloads"
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        for d in data:
            file_name = os.path.join(download_dir, d.get("name") + ".txt")
            if not os.path.exists(file_name):
                text = extract_text_from_url(d.get("url"))
                if text is not None:
                    with open(file_name, 'w') as file:
                        file.write(text)
                        print("Created file: " + file_name)
    else:
        print("Could not find file " + json_file_path)


@app.command()
def generate_question_answer():
    config = configparser.ConfigParser()
    config.read("application.properties")
    api_key = config.get("OpenAI", "api_key")

    json_file_path = "links.json"
    # Load URLs from a JSON file
    if os.path.exists(json_file_path):
        print("Found " + json_file_path)
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        print("Found total elements: " + str(len(data)))

        openai.api_key = api_key

        for d in data:
            file_name = os.path.join("downloads", d.get("name") + ".txt")
            if not os.path.exists(file_name):
                print("Could not find " + file_name)
            else:
                openai_dir = "openai"
                if not os.path.exists(openai_dir):
                    os.makedirs(openai_dir)
                openai_response_file_name = os.path.join(openai_dir, d.get("name") + ".json")
                openai_response_questions_file_name = os.path.join(openai_dir, d.get("name") + "-questions.json")
                if not os.path.exists(openai_response_questions_file_name):
                    with open(file_name, 'r') as file:
                        text = file.read()
                        if text:
                            text += "Create me an array json formatted response using the above data with objects having \"input\" as a random question and \"output\" the answer to the question. You must create 20 objects regardless of brevity reasons."
                            try:
                                response = openai.ChatCompletion.create(
                                    model="gpt-3.5-turbo",
                                    messages=[{"role": "user", "content": text}]
                                )
                                with open(openai_response_file_name, 'w') as openaifile:
                                    openaifile.write(json.dumps(response, indent=4))
                                    print("Created file: " + openai_response_file_name)

                                content = response.choices[0].message.content
                                print(content)
                                pattern = r'```(.*?)```'
                                matched_content = re.search(pattern, content, re.DOTALL)
                                print(matched_content)

                                with open(openai_response_questions_file_name, 'w') as openaifile:
                                    if matched_content is not None:
                                        modified_content = matched_content.group(1).replace("\n", "").replace("\\", "")
                                        if modified_content.startswith("json"):
                                            modified_content = modified_content.replace("json", "", 1)
                                        openaifile.write(modified_content)
                                    else:
                                        openaifile.write(content.replace("\n", "").replace("\\", ""))
                                    print("Created file: " + openai_response_questions_file_name)
                            except Exception as e:
                                print("Caught exception for " + json.dumps(d), e)

                        else:
                            print("Could not read file " + file_name)
                else:
                    print(openai_response_questions_file_name + " already exists")
    else:
        print("Could not find file " + json_file_path)


@app.command()
def collate_questions():
    print("Collate OpenAI questions into one file")
    json_file_path = "links.json"
    # Load URLs from a JSON file
    if os.path.exists(json_file_path):
        print("Found " + json_file_path)
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        result_array = []
        print("Found total elements: " + str(len(data)))

        for d in data:
            file_name = os.path.join("openai", d.get("name") + "-questions.json")
            if not os.path.exists(file_name):
                print("Could not find " + file_name)
            else:
                print("Processing file " + file_name)
                with open(file_name, 'r') as questions_file:
                    questions = json.load(questions_file)
                if questions:
                    for q in questions:
                        result_array.append(q)

        print("Total questions: " + str(len(result_array)))  # 4823

        with open("all-questions.json", 'w') as allquestions:
            allquestions.write(json.dumps(result_array, indent=4))
            print("Created file: all-questions.json")


@app.command()
def tune_openai():
    print("Tuning OpenAI")
    config = configparser.ConfigParser()
    config.read("application.properties")
    api_key = config.get("OpenAI", "api_key")

    if os.path.exists("fine-tuning-job.json"):
        print("fine-tuning-job already exists. delete file to create a new one")
        return

    json_file_path = "all-questions.json"
    if os.path.exists(json_file_path):
        print("Found " + json_file_path)
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
        jsonl_file_path = "all-questions.jsonl"
        with open(jsonl_file_path, 'w') as jsonl_file:
            for item in data:
                jsonl_file.write(json.dumps(convert_to_chatgpt_format(item)) + '\n')

        openai.api_key = api_key
        print("Uploading training file")
        file_upload = openai.File.create(
            file=open(jsonl_file_path, "rb"),
            purpose='fine-tune'
        )

        print("Creating fine-tuning job")
        job = openai.FineTuningJob.create(training_file=file_upload.id, model="gpt-3.5-turbo")

        with open("fine-tuning-job.json", 'w') as allquestions:
            allquestions.write(json.dumps(job, indent=4))
            print("Created file: fine-tuning-job.json")

        print("Finished creating fine-tuning job")


@app.command()
def check_tune_openai():
    print("Checking Tuning Job Status OpenAI")
    config = configparser.ConfigParser()
    config.read("application.properties")
    api_key = config.get("OpenAI", "api_key")
    openai.api_key = api_key
    polling_interval = 60
    with open("fine-tuning-job.json", 'r') as json_file:
        data = json.load(json_file)
    job_id = data.get("id")
    while True:

        job = openai.FineTuningJob.retrieve(id=job_id)
        status = job.status
        print(f"Job Status: {status}")

        if status == "succeeded":
            print("Fine-tuning job has completed successfully!")
            break
        elif status == "failed":
            print("Fine-tuning job has failed.")
            break
        time.sleep(polling_interval)


def convert_to_chatgpt_format(input_data):
    output_data = {
        "messages": [
            {
                "role": "user",
                "content": input_data["input"]
            },
            {
                "role": "assistant",
                "content": input_data["output"]
            }
        ]
    }
    return output_data


# https://typer.tiangolo.com/
if __name__ == "__main__":
    print(pyfiglet.figlet_format("Open AI Data Scaper & Tuner"))
    app()
