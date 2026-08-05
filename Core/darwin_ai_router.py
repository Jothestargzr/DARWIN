from flask import Flask, request, Response, stream_with_context
import requests
import json
import os

app = Flask(__name__)

# The actual DashScope API
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# Dynamic Difficulty Thresholds
MAX_MODEL = "qwen-max"
PLUS_MODEL = "qwen-plus"
COMPLEXITY_THRESHOLD = 15000 # characters

def determine_task_model(messages: list) -> str:
    """Analyze the prompt payload to determine if we need apex reasoning."""
    total_length = sum(len(str(m.get("content", ""))) for m in messages)
    
    # Heuristic 1: Payload size. Massive DOM dumps require max logic to not get lost.
    if total_length > COMPLEXITY_THRESHOLD:
        print(f"[*] SMART ROUTER: Heavy DOM payload ({total_length} chars). Routing to {MAX_MODEL}.")
        return MAX_MODEL
        
    # Heuristic 2: Keywords that imply heavy abstract logic rather than routine clicking
    combined_text = " ".join(str(m.get("content", "")).lower() for m in messages)
    complex_keywords = ["analyze", "plan", "debug", "architect", "extract all"]
    if any(kw in combined_text for kw in complex_keywords):
        print(f"[*] SMART ROUTER: Complex logic keyword detected. Routing to {MAX_MODEL}.")
        return MAX_MODEL
        
    print(f"[*] SMART ROUTER: Routine lightweight task ({total_length} chars). Routing to {PLUS_MODEL} to save credits.")
    return PLUS_MODEL

@app.route("/v1/chat/completions", methods=["POST"])
def proxy_chat_completions():
    # Extract the payload
    payload = request.json
    
    if not payload or "messages" not in payload:
        return {"error": "Invalid request format"}, 400
        
    # 1. Determine the appropriate model
    optimal_model = determine_task_model(payload["messages"])
    
    # 2. Overwrite whatever model BrowserOS requested with our optimized choice
    payload["model"] = optimal_model
    
    # 3. Forward the request to DashScope
    # Extract the API key from the incoming header that BrowserOS sent
    headers = {
        "Authorization": request.headers.get("Authorization"),
        "Content-Type": "application/json"
    }
    
    is_stream = payload.get("stream", False)
    
    try:
        # We use stream=True on requests to pipe it directly back to BrowserOS
        resp = requests.post(
            DASHSCOPE_URL,
            json=payload,
            headers=headers,
            stream=is_stream
        )
        
        if is_stream:
            def generate():
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk
            return Response(stream_with_context(generate()), content_type=resp.headers['Content-Type'])
        else:
            return Response(resp.content, status=resp.status_code, content_type=resp.headers['Content-Type'])
            
    except Exception as e:
        print(f"[!] Router Proxy Error: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    print("==============================================")
    print("🧠 DARWIN Smart AI Router is ONLINE.")
    print("Listening on http://127.0.0.1:5050")
    print("==============================================")
    # Run securely on localhost only
    app.run(host="127.0.0.1", port=5050, threaded=True)
