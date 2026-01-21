from src.server import search_web

print("🧪 Testing MCP Tool: search_web...")

# Call the function exactly how the AI Agent would call it
try:
    result = search_web("What is the capital of Montenegro?")
    
    print("\n✅ Tool Execution Successful!")
    print("🔻 RESPONSE PREVIEW 🔻")
    print("-" * 30)
    print(result[:500]) # Print just the first 500 chars to keep it clean
    print("..." + "\n" + "-" * 30)

except Exception as e:
    print(f"❌ Tool Failed: {e}")