from google import genai

client = genai.Client(vertexai=True,
                      project="your-gcp-project-id",
                      location="us-central1")

response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents='Why is the sky blue?'
)
print(response.text)
