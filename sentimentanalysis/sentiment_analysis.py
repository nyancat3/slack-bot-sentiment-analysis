import os
import datetime

# Import boto3 for Amazon Comprehend
import boto3

# Import .env
from dotenv import load_dotenv

# Import python_slack_sdk
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Import .env values
load_dotenv()
SLACK_BOT_TOKEN = os.getenv('SLACK_API_TOKEN') # TODO: Slack App API Token beginning with xoxb-
CHANNEL_ID = os.getenv('CHANNEL_ID') # TODO: Set ID of the channel you'd like to get messages from.

# Set clients
boto3_client = boto3.client('comprehend', region_name = 'ap-northeast-1')
slack_web_client = WebClient(token=SLACK_BOT_TOKEN)

try:
    # Call the conversations.history method using the WebClient
    # conversations.history returns the first 100 messages by default
    # These results are paginated, see: https://api.slack.com/methods/conversations.history$pagination
    latest = datetime.datetime.now()
    oledest = datetime.datetime.now() - datetime.timedelta(days=1)
    conversation_history = slack_web_client.conversations_history(channel=CHANNEL_ID, latest=latest.timestamp(), oldest=oledest.timestamp())
    analysis_text = ''
    texts = [message.get('text') for message in conversation_history['messages']]

    for text in texts:
        if ('さんがチャンネルに参加しました' in text or
            'removed an integration' in text or
            'added an integration' in text):
            continue

        result = boto3_client.detect_sentiment(
            Text = text,
            LanguageCode = 'ja' # TODO: Target language
        )

        emoji = '😐'
        if result['Sentiment'] == 'POSITIVE':
            emoji = '😄'
        elif result['Sentiment'] == 'NEGATIVE':
            emoji = '😥'
        elif result['Sentiment'] == 'MIXED':
            emoji = '😵'

        analysis_text += f'{text}\n{emoji}\n'

        for sentiment, score in result['SentimentScore'].items():
            analysis_text += f'    {sentiment}: {score}\n'

        analysis_text += '---\n'

    print(analysis_text)
    slack_web_client.chat_postMessage(channel='#bot_test', text=analysis_text)  # TODO: Set a name of the channel you'd like to post the result to.

except SlackApiError as e:
    print('Error creating conversation: {}'.format(e))
