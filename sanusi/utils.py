from html.parser import HTMLParser
import json, re, ast

from bs4 import BeautifulSoup

from chat.models import Chat, Message


def save_chat_and_message(chat, sender, message, response_json, channel):
    try:
        # Create two Message objects
        messages = [
            Message(
                chat=chat,
                content=message,
                sender=str(sender),
                sanusi_response=response_json.get("response"),
            ),
            Message(chat=chat, sender="agent", content=response_json.get("response")),
        ]
        Message.objects.bulk_create(messages)  # Bulk create the messages

        # Update the Chat object fields
        chat.channel = chat.channel or channel
        chat.sentiment = response_json.get("sentiment")
        chat.escalated = chat.escalated or response_json.get("escalate_issue")
        chat.keyword = response_json.get("chat_context")

        if chat.department == "none":
            chat.department = response_json.get("escalation_department")
        elif chat.department != "none" and chat.department != "":
            pass  # You might want to add some logic here if needed

        chat.save()  # Save the updated Chat object

    except Exception as e:
        # Handle any exceptions that may occur during the process
        print("An error occurred:", str(e))


def parse_answer_with_regex(answer):
    try:
        # Try to parse answer as JSON
        response_json = json.loads(answer)
    except (json.JSONDecodeError, ValueError):
        # If it fails, try to parse it using regex
        response_regex = r'"Response: (.*?)escalate_issue:'
        response = re.search(response_regex, answer, re.DOTALL).group(1).strip()
        pairs_regex = r"(\w+): ([^,]*)"
        pairs = re.findall(pairs_regex, answer)
        response_json = {"response": response}
        for key, value in pairs:
            if value == "true":
                response_json[key] = True
            elif value == "false":
                response_json[key] = False
            elif value == "null":
                response_json[key] = None
            else:
                response_json[key] = value.strip()
    return response_json


def parse_response_data(response_data):
    response_start = response_data.index("Response:")
    response_end = response_data.index("escalate_issue:")
    response_text = (
        response_data[response_start:response_end].replace("Response:", "").strip()
    )

    meta_start = response_end
    meta_data_text = response_data[meta_start:].strip()

    meta_data_text = meta_data_text.replace("\n", ", ")
    meta_data_text = "{" + meta_data_text.replace(": ", '": ') + "}"
    meta_data_text = meta_data_text.replace("false", '"false"')
    meta_data_text = meta_data_text.replace("null", '"null"')
    meta_data_text = meta_data_text.replace("low", '"low"')
    meta_data_text = meta_data_text.replace("positive", '"positive"')
    meta_data = json.loads(meta_data_text)

    response_data_parsed = {
        "response": response_text,
        "escalate_issue": meta_data["escalate_issue"] == "true",
        "escalation_department": None
        if meta_data["escalation_department"] == "null"
        else meta_data["escalation_department"],
        "severity": meta_data["severity"],
        "sentiment": meta_data["sentiment"],
    }

    return response_data_parsed


def dict_to_html(d):
    html = ""
    for key, value in d.items():
        html += "<h1>{}</h1>\n<p>{}</p>\n".format(key.capitalize(), value)
    return html


def is_html(s):
    return bool(BeautifulSoup(s, "html.parser").find())


def json_to_html(json_obj):
    html = ""
    for key, value in json_obj.items():
        html += f"<h1>{key}:</h1>\n<p>{value}</p>\n"
    return html


def remove_first_and_last_quotes(s):
    s = s.strip()  # Remove leading and trailing whitespaces
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]  # Removes the quotes
    else:
        return s


def parse_json_from_answer(answer):
    start = answer.find("Here is the response in the specified format:")
    if start == -1:
        raise ValueError("Could not find the start of JSON in the answer")

    json_str = answer[
        start + len("Here is the response in the specified format:") :
    ].strip()
    json_str = json_str.replace("'", '"')

    return json.loads(json_str)


def is_valid_format(response):
    # Define required keys and their expected types
    required_keys = {
        "response": str,
        "escalate_issue": lambda x: isinstance(x, str) and len(x) in [4, 5],
        "escalation_department": lambda x: x == "null"
        or x
        in [
            "sales",
            "operations",
            "billing",
            "engineering",
            "customer service",
            "support",
        ],
        "severity": lambda x: x in ["low", "medium", "high"],
        "sentiment": lambda x: x in ["positive", "negative", "neutral"],
    }

    # Check if all required keys are present and values are of the expected type
    if isinstance(response, dict):
        for key, expected_type in required_keys.items():
            if key not in response or not expected_type(response[key]):
                return False
        return True
    elif isinstance(response, str) or isinstance(response, dict):
        return response
    else:
        return False


def is_html(s):
    return bool(BeautifulSoup(s, "html.parser").find())


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.first_p_tag = None
        self.is_p_tag = False

    def handle_starttag(self, tag, attrs):
        if tag == "p" and self.first_p_tag is None:
            self.is_p_tag = True

    def handle_endtag(self, tag):
        if tag == "p":
            self.is_p_tag = False

    def handle_data(self, data):
        if self.is_p_tag and self.first_p_tag is None:
            self.first_p_tag = data


def try_parse_json(answer):
    try:
        # Attempt to parse as JSON
        response_json = json.loads(answer)
        if type(response_json) == dict:
            return response_json
    except json.JSONDecodeError:
        pass

    # Replace single quotes with double quotes, but not in contractions
    answer_double_quotes = re.sub(r"(?<!\w)'(?!')", '"', answer)
    try:
        # Attempt to parse the modified string as JSON
        response_json = json.loads(answer_double_quotes)
        if type(response_json) == dict:
            return response_json
    except json.JSONDecodeError:
        pass

    try:
        # If the above fails, attempt to parse as a Python dictionary string
        response_json = ast.literal_eval(answer)
        if type(response_json) == dict:
            return response_json
    except (ValueError, SyntaxError):
        pass

    return None


def parse_answer_with_regex(answer):
    try:
        response_json = json.loads(answer)
        if not is_valid_format(response_json):
            raise ValueError("Invalid response format")

        return response_json
    except (json.JSONDecodeError, ValueError):
        # Attempt to parse as a Python dictionary string
        try:
            response_json = ast.literal_eval(answer)
            return response_json
        except (ValueError, SyntaxError):
            # If parsing fails, return the original string
            return answer

    return answer
