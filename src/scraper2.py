import json
import re
from openai import OpenAI
import openai
import creds  # Assuming creds.py contains your API key
import os
from dotenv import load_dotenv

def configure():
    load_dotenv()

client = OpenAI(api_key=creds.apikeysecret)

#Load the raw text
with open("data/raw_text.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

faqs = []
current_section = ""
current_paragraphs = []

header_pattern = re.compile(r"^H\d:\s*(.*)")
paragraph_pattern = re.compile(r"^P:\s*(.*)")
numbered_list_pattern = re.compile(r"(?:^|\s)(\d+\.\s*)")

for line in lines:
    line = line.strip()
    line = re.sub(numbered_list_pattern, " ", line)

    #detect H HTML elements
    header_match = header_pattern.match(line)
    if header_match:
        # Process previous section before switching
        if current_section and current_paragraphs:
            faqs.append({"section": current_section, "content": " ".join(current_paragraphs)})
        current_section = header_match.group(1)  # Update current section
        current_paragraphs = []  # Reset content list
        continue

    #detect P html elements
    paragraph_match = paragraph_pattern.match(line)
    if paragraph_match:
        current_paragraphs.append(paragraph_match.group(1))

#Save last section
if current_section and current_paragraphs:
    faqs.append({"section": current_section, "content": " ".join(current_paragraphs)})

#part2: Use LLM to Transform Statements into Questions
def generate_faq(section, content):
    prompt = f"""
    Convert the following text with this structure:
    
    Topic: {section}
    Description: {content}
    
    Provide a natural-sounding question that someone might ask based on this information.
    """
    response = client.chat.completions.create(
                model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}]
                )
    
    return response.choices[0].message.content.strip()

final_faqs = []
for item in faqs:
    question = generate_faq(item["section"], item["content"])
    final_faqs.append({"question": question, "answer": item["content"]})

#Save to JSON
with open("data/faqs.json", "w", encoding="utf-8") as json_file:
    json.dump(final_faqs, json_file, indent=4, ensure_ascii=False)

print("FAQs extracted, transformed with GPT, and saved to data/faqs.json")
