import os, requests, json, random
from openai import OpenAI
from mjml import mjml_to_html
from dotenv import load_dotenv


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
    response_text = json.loads(response_text.strip()[7:-3])

    return response_text


def getWord(length = 7):
    url = f'https://random-word-api.herokuapp.com/word?length={length}'
    response = requests.get(url)

    #convert from string to list
    word = json.loads(response.text)[0]

    return word


def createHTML(word_data):
    mjml_text = f"""
    <mjml>
      <mj-body>
        <!-- Header Section -->
        <mj-section background-color="#FF8CFF">
          <mj-column>
            <mj-text align="center" font-size="24px" color="#ffffff" font-family="Arial, sans-serif">
              <h1>Discover the Word: {word_data['word']}</h1>
            </mj-text>
          </mj-column>
        </mj-section>

        <!-- Main Content Section -->
        <mj-section padding="20px" background-color="#ffffff">
          <mj-column>
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
              <h2>Pronunciation:</h2>
              <h3>{word_data['pronunciation']} ({word_data['phonetic']})</h3>
              <p><a href="{word_data['audio']}" style="color: #FF8CFF;">Listen to the Pronunciation</a></p>
            </mj-text>

            <!-- Origin Section -->
            <mj-divider border-color="#FF8CFF" />
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
              <h4>Origin</h4>
              <p>{word_data['usages'][0]['origin_summary']}</p>
              <p><strong>Origin Details:</strong> {word_data['usages'][0]['origin_details']}</p>
              <p><strong>Earliest Usage:</strong> {word_data['usages'][0]['earliest_usage']}</p>
            </mj-text>

            <!-- Etymology Section -->
            <mj-divider border-color="#FF8CFF" />
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
              <h4>Etymology</h4>
              <h5>Root Words</h5>
              <ul style="padding-left: 20px;">
              """

    for et in word_data['etymology']['root_words']:
        mjml_text += f'<li><strong>{et["root"]}</strong> - {et["meaning"]}</li>'

    mjml_text += f"""</ul>
                     <p>{word_data['etymology']['linguistic_evolution']}</p>
                    </mj-text>
            <!-- Explanation by Age Section -->
            <mj-divider border-color="#FF8CFF" />
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
                <h4>Examples</h4>
            """

    # Add explanations for different age groups
    for age in word_data['explanations']:
        mjml_text += f"""<h3>Explain it like I'm {age}</h3>
                            <p><strong>Explanation:</strong> {word_data['explanations'][age]['explanation']}</p>
                            <strong>Examples:</strong>
                            <ul style="padding-left: 20px;">"""

        # Add short examples
        for ex in word_data['explanations'][age]['examples']['short examples']:
            mjml_text += f"""<li>{ex}</li>"""

        # Add long examples
        for ex in word_data['explanations'][age]['examples']['long examples']:
            mjml_text += f"""<li>{ex}</li>"""

        mjml_text += '</ul></hr>'

    mjml_text += f"""
            </mj-text>
          </mj-column>
        </mj-section>

        <!-- Footer Section -->
        <mj-section background-color="#FF8CFF" padding="20px">
          <mj-column>
            <mj-text align="center" color="#ffffff" font-size="14px" font-family="Arial, sans-serif">
              <p>Learn more words and expand your knowledge every day!</p>
              <p>&copy; "Vocabber - Made for Zara ❤️"</p>
            </mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    """

    count = 0
    return mjml_to_html(mjml_text)['html']


def validateData(word_data):

    expectedKeys = ['word', 'usages', 'etymology', 'pronunciation', 'phonetic', 'audio', 'examples', 'explanations']

    for key in expectedKeys:
        if key not in word_data:
            return False

    return True


def sendEmail(html):
    pass

# get word of random length
wordlength = random.randint(LENGTHLOW, LENGTHHIGH)

isValid = False

while isValid == False:

    word = getWord(wordlength)

    userPrompt = f'{USERPROMPTPREFIX} {word}.  {userPrompt}'
    word_data = queryGPT(userPrompt, SYSTEMPROMPT, OPENAI_API_KEY)

    isValid = validateData(word_data)


#html = createHTML(word_data)
html = createHTML(word_data)

sendEmail(html)

count = 0

