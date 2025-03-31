import json
from difflib import get_close_matches

#Load FAQs
def load_faqs(filepath="data/faqs.json"):
    """Loads FAQ data from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

#Find the best matching question
def find_best_answer(user_question, faqs):
    """Finds the closest matching question in the FAQ dataset."""
    questions = [faq["question"] for faq in faqs]
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.5)
    
    if matches:
        for faq in faqs:
            if faq["question"] == matches[0]:
                return faq["answer"]
    
    return "I'm not sure about that. Would you like me to connect you to a human?"

def chatbot():
    """Runs a simple chatbot interface."""
    faqs = load_faqs()

    print("Owl AI: Hi! Ask me anything about Able. Type 'exit' to stop.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            print("Owl AI: Goodbye!")
            break
        
        response = find_best_answer(user_input, faqs)
        print(f"Owl AI: {response}")

# Run the chatbot
if __name__ == "__main__":
    chatbot()
