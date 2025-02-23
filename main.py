import os, requests, json, random
from openai import OpenAI
#import openai
from dotenv import load_dotenv, dotenv_values


load_dotenv('vocabber.env')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEMPROMPT = os.getenv("SYSTEMPROMPT")
USERPROMPTPREFIX = os.getenv("USERPROMPTPREFIX")
userPrompt = os.getenv("USERPROMPT2")
LENGTHLOW = int(os.getenv("LENGTHLOW"))
LENGTHHIGH = int(os.getenv("LENGTHHIGH"))


def queryGPT(userPrompt, systemPrompt, OPENAI_API_KEY):

    client = OpenAI(
        api_key=OPENAI_API_KEY  # This is the default and can be omitted
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": userPrompt
            },
            {
                "role": "system",
                "content": systemPrompt
            }
        ],
        model="gpt-4o-mini",
    )

    response_text = response.choices[0].message.content
    return response_text


def getWord(length = 7):
    url = f'https://random-word-api.herokuapp.com/word?length={length}'
    response = requests.get(url)

    #convert from string to list
    word = json.loads(response.text)[0]

    return word


# get word of random length
wordlength = random.randint(LENGTHLOW, LENGTHHIGH)
word = getWord(wordlength)

userPrompt = f'{USERPROMPTPREFIX} {word}.  {userPrompt}'
word_data = queryGPT(userPrompt, SYSTEMPROMPT, OPENAI_API_KEY)
count = 0

