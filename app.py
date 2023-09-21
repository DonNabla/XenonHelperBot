import os
import json
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify,render_template
from pymongo.mongo_client import MongoClient
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError
from bson import ObjectId  # Import ObjectId from bson

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO)

# Set up logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO)

def load_instructions_from_file(filename):
    try:
        with open(filename, 'r') as file:
            content = json.load(file)
            return content['name'], content['content']
    except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
        logging.error(f"Error reading {filename}: {e}")
        return None, [{"type": "section", "text": {"type": "mrkdwn", "text": f"Instructions for {filename} not found or not accessible."}}]


    
def get_config():
    """Retrieve configuration values from environment variables."""
    return {
        "SIGNING_SECRET": os.getenv("SLACK_SIGNING_SECRET"),
        "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
        "CHANNEL_ID": os.getenv("CHANNEL_ID", "C05R986BYT1"),  # Default value provided
        "MONGODB_USERNAME": os.getenv("MONGODB_USERNAME"),
        "MONGODB_PASSWORD": os.getenv("MONGODB_PASSWORD"),
        "MONGODB_DATABASE": os.getenv("MONGODB_DATABASE")
    }

config = get_config()
client = WebClient(token=config["SLACK_BOT_TOKEN"])
signature_verifier = SignatureVerifier(signing_secret=config["SIGNING_SECRET"])

def get_all_instruction_files(directory="./instructions"):
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.json')]

ISSUE_INSTRUCTIONS = {}
for filepath in get_all_instruction_files():
    name, content = load_instructions_from_file(filepath)
    if name:
        ISSUE_INSTRUCTIONS[name] = content


##################### MongoDB Initialization #####################

# MongoDB setup 
MONGO_URI = f"mongodb+srv://{config['MONGODB_USERNAME']}:{config['MONGODB_PASSWORD']}@cluster0.5qylimo.mongodb.net/?retryWrites=true&w=majority"
# Remember to add the IP address of your machine to the IP access list in MongoDB Atlas

# Create a new client and connect to the server
Mongo_client = MongoClient(MONGO_URI) #, server_api=ServerApi('1')
# Send a ping to confirm a successful connection
try:
    Mongo_client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# use a database named "myDatabase"
db = Mongo_client.jarvisdb

# use a collection named "recipes"
my_collection = db["jarviscoll"]

##################################################################

################## Dashboard Routes ##############################
@app.route('/dashboard')
def dashboard():
    return render_template('home.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')


ITEMS_PER_PAGE = 5  # This is a default value. You can change it.

@app.route('/get-issues', methods=['GET'])
def get_issues():
    page = request.args.get('page', 1, type=int)
    items_per_page = request.args.get('items_per_page', ITEMS_PER_PAGE, type=int)
    skip = (page - 1) * items_per_page

    try:
        issues = list(my_collection.find().skip(skip).limit(items_per_page))

        # Convert ObjectId to string
        for document in issues:
            document['_id'] = str(document['_id'])

        total_issues = my_collection.count_documents({})
        return jsonify({"issues": issues, "total_issues": total_issues})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-issue-counts', methods=['GET'])
def get_issue_counts():
    try:
        total_issues = my_collection.count_documents({})
        pending_issues = my_collection.count_documents({"status": "pending"})
        resolved_issues = my_collection.count_documents({"status": "resolved"})

        return jsonify({
            "total_issues": total_issues,
            "pending_issues": pending_issues,
            "resolved_issues": resolved_issues
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
##################################################################

################## SlackBot Routes ###############################
    
@app.route('/help', methods=['POST'])
def help_command():
    """Handle the help command."""
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return jsonify({'error': 'invalid request'}), 400

    trigger_id = request.form['trigger_id']
    try:
        response = client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "issue_type",
                "title": {"type": "plain_text", "text": "🛠 HelpDesk"},
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "Welcome to HelpDesk!"}
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "block_id": "section-1",
                        "text": {"type": "mrkdwn", "text": "Please select your issue type:"},
                        "accessory": {
                            "type": "static_select",
                            "placeholder": {"type": "plain_text", "text": "Select an issue"},
                            "options": [
                                {"text": {"type": "plain_text", "text": f" {name}"},
                                 "value": name} for name in ISSUE_INSTRUCTIONS.keys()
                            ],
                            "action_id": "issue_selection"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": "You have issue with the HelperBot? Contact Maxime Pierre."}
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Continue"},
                                "style": "primary",
                                "action_id": "continue_issue_selection"
                            }
                        ]
                    }
                ]
            }
        )
    except SlackApiError as e:
        logging.error(f"Error opening view: {e}")
        return jsonify({'error': e.response['error']}), 400

    return jsonify({'text': 'Please check the Pop-up window to continue.'})




def get_slack_user_name(user_id, slack_token):
    url = f"https://slack.com/api/users.info?user={user_id}"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.get(url, headers=headers)
    user_info = response.json()
    if user_info['ok']:
        return user_info['user']['name']
    else:
        print(f"Error fetching user name for {user_id}: {user_info['error']}")  # Log the error
        return None

@app.route('/slack/interactions', methods=['POST'])
def interactions():
    """Handle Slack interactions."""
    payload = json.loads(request.form['payload'])

    logging.debug(payload)

    if payload['type'] == 'block_actions':
        action_id = payload['actions'][0]['action_id']
        view_id = payload['view']['id'] if 'view' in payload else None

        # Check if the action is from the "Continue" button
        if action_id == 'continue_issue_selection':
            # Extract the selected issue from the modal's state
            selected_issue = payload['view']['state']['values']['section-1']['issue_selection']['selected_option']['value']
            # Use the extracted selected_issue value to update the modal
            if selected_issue:
                update_modal_with_instructions(view_id, selected_issue, ISSUE_INSTRUCTIONS)

        # Check if the action is from the "Pending" button
        elif action_id == 'issue_status_change':
            button_value = payload['actions'][0]['value']

            # Split the value into the MongoDB ID and the status
            issue_id_str, current_status = button_value.split('|')
            issue_id = ObjectId(issue_id_str)

            # Toggle the status
            new_status = "resolved" if current_status == "pending" else "pending"
            new_button_text = "Resolved" if new_status == "resolved" else "Pending"

            # Update the MongoDB record
            try:
                my_collection.update_one({"_id": issue_id}, {"$set": {"status": new_status}})
            except Exception as e:
                logging.error(f"Error updating MongoDB status record: {e}")

            # Extract the original blocks from the payload
            original_blocks = payload['message'].get('blocks', [])

            # Create the new blocks for the status button
            status_block = {
                "type": "actions",
                "block_id": "status_block",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": new_button_text
                        },
                        "value": f"{issue_id_str}|{new_status}",  # Update the value with the new status
                        "action_id": "issue_status_change",
                        "style": "primary" if new_status == "resolved" else "danger",
                    }
                ]
            }

            # Append the new status block to the original blocks
            updated_blocks = original_blocks[:-1] + [status_block]  # Replace the last block with the updated status block
            logging.debug(f"updated blocks: {updated_blocks}")

            # Update the Slack message using the chat_update method
            try:
                client.chat_update(
                    channel=payload['channel']['id'],
                    ts=payload['message']['ts'],
                    blocks=updated_blocks,
                    text=":exclamation: *Issue Update* :exclamation:"
                )
            except SlackApiError as e:
                logging.error(f"Error updating Slack message: {e}")

        elif action_id == 'issue_not_solved':
            metadata = json.loads(payload['view']['private_metadata'])
            selected_issue = metadata['selected_issue']
            if selected_issue:
                show_issue_form(view_id, selected_issue)
            else:
                logging.error(f"No selected issue found in payload.")

    elif payload['type'] == 'view_submission' and payload['view']['callback_id'] == 'issue_form':
        user_id = payload['user']['id']
        user_name = get_slack_user_name(user_id, config["SLACK_BOT_TOKEN"])

        description = payload['view']['state']['values']['issue_description']['description_input']['value']
        reproduce = payload['view']['state']['values']['issue_reproduce']['reproduce_input']['value']
        log = payload['view']['state']['values']['issue_log']['log_input']['value']
        machine_partition = payload['view']['state']['values']['Issue_machine_partition']['machine_partition_input']['value']
        container = payload['view']['state']['values']['issue_container']['container_input']['value']
        straxen_version = payload['view']['state']['values']['issue_straxen_version']['straxen_version_input']['value']

        metadata = json.loads(payload['view']['private_metadata'])
        selected_issue = metadata['selected_issue']   

        #Get time of submission
        current_time = datetime.now()
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

        # Insert the new issue into MongoDB
        issue_document = {
            "user_id": user_name,
            "issue_type": selected_issue,
            "submitted_at": formatted_time,
            "description": description,
            "reproduce": reproduce,
            "log": log,
            "machine_partition": machine_partition,
            "container": container,
            "straxen_version": straxen_version,
            "status": "pending",
        }
        result = my_collection.insert_one(issue_document)

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":exclamation: *New Issue Reported by <@{user_id}>* :exclamation:\n"
                            f"──────────────────────────────────────\n"
                            f"*Description of the issue:*\n{description}\n\n"
                            f"*How to reproduce the issue:*\n{reproduce}\n\n"
                            f"*Error Log:*\n{log}\n\n"
                            f"*Machine/Partition:*\n{machine_partition}\n\n"
                            f"*Container:*\n{container}\n\n"
                            f"*straxen.print_versions():*\n{straxen_version}\n"
                            f"──────────────────────────────────────\n"
                            f"_Any help would be kindly appreciated!_"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Pending"
                        },
                        "value": f"{str(result.inserted_id)}|pending",  # Embed both the MongoDB document ID and the status
                        "action_id": "issue_status_change",
                        "style": "danger"
                    }
                ]
            }
        ]
        # Post the message to the Slack channel
        client.chat_postMessage(
            channel=config["CHANNEL_ID"],
            blocks=blocks,
        )

    return jsonify({}), 200


def update_modal_with_instructions(view_id, selected_issue, instructions):
    instructions_blocks = instructions[selected_issue]
    logging.debug(f"Updating modal with instructions: {instructions_blocks}")

    
    private_metadata_content = json.dumps({"selected_issue": selected_issue})

    try:
        response = client.views_update(
            view_id=view_id,
            view={
                "type": "modal",
                "callback_id": "instructions_modal",
                "title": {"type": "plain_text", "text": "Instructions"},
                "blocks": instructions_blocks + [
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "If you have any tips in minds that should go there, please let us know!"
                            }
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "It doesn't help :/"},
                                "action_id": "issue_not_solved",
                                "style": "danger"
                            }
                        ]
                    }
                ],
                "private_metadata": private_metadata_content
            }
        )
    except SlackApiError as e:
        logging.error(f"Error updating modal: {e}")


def show_issue_form(view_id,selected_issue):

    private_metadata_content = json.dumps({"selected_issue": selected_issue})

    try:
        response = client.views_update(
            view_id=view_id,
            view={
                "type": "modal",
                "callback_id": "issue_form",
                "title": {"type": "plain_text", "text": "Provide More Details"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "issue_description",
                        "label": {"type": "plain_text", "text": "Can you describe in detail your issue?"},
                        "element": {
                            "type": "plain_text_input", 
                            "action_id": "description_input",
                            "multiline": True
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "issue_reproduce",
                        "label": {"type": "plain_text", "text": "Can you explain how to reproduce it?"},
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "reproduce_input",
                            "multiline": True
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "issue_log",
                        "label": {"type": "plain_text", "text": "Can you provide a gist of the error log?"},
                        "element": {
                            "type": "plain_text_input", 
                            "action_id": "log_input",
                            "multiline": True  
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "Issue_machine_partition",
                        "label": {"type": "plain_text", "text": "On which machine/partition did you encounter the issue?"},
                        "element": {
                            "type": "plain_text_input", 
                            "action_id": "machine_partition_input",
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "issue_container",
                        "label": {"type": "plain_text", "text": "Which container did you used?"},
                        "element": {
                            "type": "plain_text_input", 
                            "action_id": "container_input",
                        },
                        "optional": True
                    },
                    {
                        "type": "input",
                        "block_id": "issue_straxen_version",
                        "label": {"type": "plain_text", "text": "Output of straxen.print_versions()"},
                        "element": {
                            "type": "plain_text_input", 
                            "action_id": "straxen_version_input",
                            "multiline": True  
                        },
                        "optional": True
                    },
                ],
                 "private_metadata": private_metadata_content,
                "submit": {"type": "plain_text", "text": "Submit"}
            }
        )
    except SlackApiError as e:
        logging.error(f"Error updating modal: {e}")

##################################################################


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
