import os, requests, json, random
from openai import OpenAI
from mjml import mjml_to_html
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


load_dotenv('vocabber.env')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEMPROMPT = os.getenv("SYSTEMPROMPT")
USERPROMPTPREFIX = os.getenv("USERPROMPTPREFIX")
userPrompt = os.getenv("USERPROMPT")
LENGTHLOW = int(os.getenv("LENGTHLOW"))
LENGTHHIGH = int(os.getenv("LENGTHHIGH"))
recipient_email = "dustin0357@outlook.com"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIANT_EMAILS = os.getenv("RECIPIANT_EMAILS").split(",")

def queryGPT(userPrompt, systemPrompt, OPENAI_API_KEY):

    client = OpenAI(
        api_key=OPENAI_API_KEY  # This is the default and can be omitted
    )
    print("Calling ChatGPT")

    response = client.chat.completions.create(
        response_format={"type": "json_object"},
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": systemPrompt
            },
            {
                "role": "user",
                "content": userPrompt
            }
        ]
    )

    response_text = response.choices[0].message.content
    #response_text = json.loads(response_text.strip()[7:-3])
    response_text = json.loads(response_text)

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
        <mj-section full-width="full-width" background-color="#ffffff" padding-bottom="0">
            <mj-column width="100%">
                <mj-image src="https://res.cloudinary.com/ddnbf9prg/image/upload/c_crop,w_800,h_500/v1740488213/header_vocabber5_d7yexe.png" alt=""/>
                <mj-text font-size="28px" font-weight="normal" color="#333333" align="center" padding="20px 0" letter-spacing="1px" line-height="1.5" text-transform="uppercase">Word of the Day</mj-text>
                <mj-text font-size="40px" font-weight="bold" color="#444444" align="center" padding="20px 0" letter-spacing="1px" line-height="1.5" text-transform="uppercase">{word_data['word']}</mj-text>
            </mj-column>
        </mj-section>
        <!-- Main Content Section -->
        <mj-section padding="20px" background-color="#ffffff">
          <mj-column>
            <mj-text>
                <h3>Pronunciation:</h3>
                <h3>{word_data['pronunciation']} ({word_data['phonetic']})</h3>
            </mj-text>
            <!-- Origin Section -->
            <mj-divider border-color="#4361ee" />
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
              <h4 align="center">Origin</h4>
              <p>{word_data['usages'][0]['origin_summary']}</p>
              <p><strong>Origin Details:</strong> {word_data['usages'][0]['origin_details']}</p>
              <p><strong>Earliest Usage:</strong> {word_data['usages'][0]['earliest_usage']}</p>
            </mj-text>

            <!-- Etymology Section -->
            <mj-divider border-color="#4361ee" />
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
              <h4 align="center">Etymology</h4>
              <h5>Root Words</h5>
              <ul style="padding-left: 20px;">
              """

    for et in word_data['etymology']['root_words']:
        mjml_text += f'<li><strong>{et["root"]}</strong> - {et["meaning"]}</li>'

    mjml_text += f"""</ul>
                     <p>{word_data['etymology']['linguistic_evolution']}</p>
                    </mj-text>
            <!-- Explanation by Age Section -->
            <mj-divider border-color="#4361ee" />
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
                <h4 align="center">Examples</h4></mj-text>
            """

    # Add explanations for different age groups
    for age in word_data['explanations']:

        mjml_text += f"""<mj-text>
        <h3>Explain it like I'm {age}</h3>
        <p><strong>Explanation:</strong> {word_data['explanations'][age]['explanation']}</p>
        <strong>Examples:</strong>
        <ul style="padding-left: 20px;">"""

        # Add short examples
        for ex in word_data['explanations'][age]['examples']['short examples']:
            mjml_text += f"""<li>{ex}</li>"""

        # Add long examples
        for ex in word_data['explanations'][age]['examples']['long examples']:
            mjml_text += f"""<li>{ex}</li>"""

        mjml_text += '</ul></mj-text><mj-divider border-color="#4361ee" />'

    mjml_text += f"""
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

    return mjml_to_html(mjml_text)['html']


def validateData(word_data):

    expectedKeys = ['word', 'usages', 'etymology', 'pronunciation', 'phonetic', 'examples', 'explanations']

    for key in expectedKeys:
        if key not in word_data:
            return False

    return True


def sendEmail(html, recipiant_email):


    SMTP_SERVER = "smtp.titan.email"
    SMTP_PORT = 587  # Use 465 for SSL
    subject = "Vocabber word of the day"

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Upgrade the connection to secure
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


# get word of random length
wordlength = random.randint(LENGTHLOW, LENGTHHIGH)

#isValid = False

#while isValid == False:

word = getWord(wordlength)

userPrompt = f'{USERPROMPTPREFIX} {word}.  {userPrompt}'
word_data = queryGPT(userPrompt, SYSTEMPROMPT, OPENAI_API_KEY)

#    isValid = validateData(word_data)

#ensure value exists
word_data['usages'][0]['earliest_usage'] = word_data.get('usages', [{}])[0].get('earliest_usage', 'Unknown')
word_data['pronunciation'] = word_data.get('pronunciation', 'Unknown')
word_data['phonetic'] = word_data.get('phonetic', 'Unknown')

html = createHTML(word_data)

for recipient_email in RECIPIANT_EMAILS:
    sendEmail(html, recipient_email)
