import openai

languages = [
    "Spanish",
    "Russian",
    "French",
    "Italian",
    "German",
    "Swedish",
    "Norwegian",
    "Danish",
    "Finnish",
    "Portugese",
]


def completion(input):
    messages = [
        {"role": "system", "content": "You assist in translations."},
        {"role": "user", "content": input},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response["choices"][0]["message"]["content"]


def translate(language, input):
    return completion("Translate to " + language + ": " + input)
