import os, requests, json, random, urllib3
from openai import OpenAI
from mjml import mjml_to_html
from dotenv import load_dotenv
import smtplib, clickhouse_connect
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

load_dotenv('/vocabber/vocabber.env')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEMPROMPT = os.getenv("SYSTEMPROMPT")
USERPROMPTPREFIX = os.getenv("USERPROMPTPREFIX")
userPrompt = os.getenv("USERPROMPT")

DBHOST = os.getenv("DBHOST")
DBUSER = os.getenv("DBUSER")
DBPASS = os.getenv("DBPASS")
DBTABLEWORD = os.getenv("DBTABLEWORD")
DBTABLEDATA = os.getenv("DBTABLEDATA")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIANT_EMAILS = os.getenv("RECIPIANT_EMAILS").split(",")


def getClickSession():

    try:
        # Set up Session() to not show warnings/errors for the self-signed cert
        clickSession = requests.Session()
        clickSession.verify = False
        urllib3.disable_warnings()
        clickSession.headers.update({
            "accept": "application/json, text/plain",
            "X-Requested-With": "required"
            })
        #logging.debug(f'{logWorkload} : Establish Clickhouse session - Success')

    except Exception as e:
        #logging.error(f'{logWorkload} : Establish Clickhouse session - Failed: {e}')
        pass

    return clickSession


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
    response_text = json.loads(response_text)

    return response_text


def getWord(DBTABLEWORD):

    #Select unused word
    query = f"SELECT * FROM {DBTABLEWORD} WHERE used IS NULL ORDER BY rand() LIMIT 1"
    result = clickClient.command(query)
    randomWord = result[1]

    #flag word as used
    updateQuery = f"ALTER TABLE vocabber.words_21 UPDATE used = toUnixTimestamp(now()) WHERE word = '{randomWord}'";
    update = clickClient.command(updateQuery)

    return randomWord


def PushToDB(word_data):

    def escape_sql_value(value):
        """Converts a value to a string and escapes single quotes for safe SQL insertion."""
        if isinstance(value, (dict, list)):  # Convert lists/dicts to JSON strings
            value = json.dumps(value, ensure_ascii=False)
        return str(value).replace("'", r"\'")  # Escape single quotes

    # Extract and escape all fields
    word = escape_sql_value(word_data.get("word", ""))
    phonetic = escape_sql_value(word_data.get("phonetic", ""))
    pronunciation = escape_sql_value(word_data.get("pronunciation", "")).replace("/", "").replace("'", "")
    linguistic_evolution = escape_sql_value(word_data.get("etymology", {}).get("linguistic_evolution", ""))
    root_words = escape_sql_value(word_data.get("etymology", {}).get("root_words", []))
    explanations = escape_sql_value(word_data.get("explanations", {}))
    usages = escape_sql_value(word_data.get("usages", []))

    insertion_string = f"""
    ('{word}', '{phonetic}', '{pronunciation}', '{linguistic_evolution}', '{root_words}', '{explanations}', '{usages}')
    """

    # Execute the Insert Command
    query = f'INSERT INTO {DBTABLEDATA} VALUES {insertion_string}'
    print(query)
    clickClient.command(query)


def createHTML(word_data):
    mjml_text = f"""
    <mjml>
      <mj-body>
        <!-- Header Section -->
        <mj-section full-width="full-width" background-color="#ffffff" padding-bottom="0">
            <mj-column width="100%">
                <mj-image href="https://vocabber.com" src="https://res.cloudinary.com/ddnbf9prg/image/upload/v1742023565/header_vocabber5_white_outline_jasujd.png" alt=""/>
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
            <mj-text font-size="18px" font-family="Arial, sans-serif" color="#333333">
                <h4 align="center">Examples</h4></mj-text>
            """

    # Add explanations for different age groups
    for age in word_data['explanations']:

        mjml_text += f"""<mj-text>
        <h3>Explain it like I'm {age}</h3>
        <h4>Explanation:</h4>
        <p>{word_data['explanations'][age]['explanation']}</p>
        <h4>Examples:</h4>
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
        <mj-section padding="20px">
          <mj-column>
            <mj-text align="center" font-size="14px" font-family="Arial, sans-serif">
              <p>Learn more words and expand your knowledge every day!</p>
              <p>&copy; "<a href="https://vocabber.com">Vocabber.com</a> - Made for Zara ❤️"</p>
            </mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    """

    return mjml_to_html(mjml_text)['html']


def sendEmail(html, recipiant_email):


    SMTP_SERVER = "smtp.ionos.com"
    SMTP_PORT = 587  # Use 465 for SSL
    subject = "Vocabber word of the day"

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = formataddr(('Vocabber', EMAIL_ADDRESS))
    msg["To"] = recipient_email
    msg["Subject"] = subject
    spoofedFrom = 'wordoftheday@vocabber.com'

    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Upgrade the connection to secure
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        #server.sendmail(spoofedFrom, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


# Connect to ClickHouse
clickClient = clickhouse_connect.get_client(host=DBHOST, port=8123, user=DBUSER, password=DBPASS)
clickSession = getClickSession()

word = getWord(DBTABLEWORD)

userPrompt = f'{USERPROMPTPREFIX} {word}.  {userPrompt}'
word_data = queryGPT(userPrompt, SYSTEMPROMPT, OPENAI_API_KEY)
#PushToDB(word_data)

html = createHTML(word_data)

for recipient_email in RECIPIANT_EMAILS:
    sendEmail(html, recipient_email)

exit(0)
