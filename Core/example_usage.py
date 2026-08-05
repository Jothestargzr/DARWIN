"""
GLM-5 Quickstart Example Script
Demonstrates basic usage, streaming responses, reasoning effort configuration, and API routing.
"""

import os
import sys
from glm5_client import GLM5Client


def main():
    print("=" * 60)
    print("🚀 GLM-5 Quickstart & Demonstration Script")
    print("=" * 60)

    client = GLM5Client()

    if not client.is_configured():
        print("\n⚠️  No valid API Token configured!")
        print("To run live API requests with your API Token / Gateway:")
        print(" 1. Edit .env file and set your token & optional proxy base URL:")
        print("    GLM_API_KEY='your_api_token'")
        print("    GLM_BASE_URL='https://api.z.ai/v1'  (or OpenRouter / custom gateway)")
        print(" 2. Re-run this script: python3 example_usage.py\n")
        print("Displaying demo code structure without sending active API request...\n")
        
        demo_messages = [
            {"role": "system", "content": "You are GLM-5, an advanced coding and reasoning AI."},
            {"role": "user", "content": "Write a Python function to solve the Traveling Salesperson Problem using Dynamic Programming."}
        ]
        print(f"Sample Message Payload:\n{demo_messages}\n")
        print("Client is ready to call:")
        print("  client.chat(messages, model='glm-5.2', reasoning_effort='max')")
        print("  client.chat_stream(messages, model='glm-5.2', reasoning_effort='high')")
        print("\n" + "=" * 60)
        return

    print(f"✅ API Token detected. Using model: {client.default_model}\n")

    # 1. Non-Streaming Request Example
    print("1️⃣ Testing Non-Streaming Completion (Model: GLM-5.2, Effort: max)...")
    messages = [
        {"role": "system", "content": "You are GLM-5, an elite coding and reasoning assistant."},
        {"role": "user", "content": "Give a 2-sentence summary of why 1M context is useful for repository-level coding."}
    ]
    
    try:
        response = client.chat(messages=messages, model="glm-5.2", reasoning_effort="max")
        print(f"\n🤖 Response:\n{response['content']}\n")
    except Exception as e:
        print(f"❌ API Request failed: {e}\n")

    # 2. Streaming Request Example
    print("2️⃣ Testing Streaming Completion (Model: GLM-5.2, Effort: high)...")
    prompt = "Explain in 3 bullet points how speculative decoding works in LLMs."
    print(f"Prompt: '{prompt}'\nStream Output: ", end="", flush=True)

    try:
        for chunk in client.chat_stream(
            messages=[{"role": "user", "content": prompt}],
            model="glm-5.2",
            reasoning_effort="high"
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n❌ Streaming request failed: {e}\n")

    print("=" * 60)
    print("✨ Demonstration complete!")


if __name__ == "__main__":
    main()
