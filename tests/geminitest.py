from google import genai

client = genai.Client(vertexai=True,
                      project="geminijournal-463220",
                      location="us-central1")

response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents='Why is the sky blue?'
)
print(response.text)
