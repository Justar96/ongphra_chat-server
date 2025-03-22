from app.utils.fortune_tool import calculate_fortune
import json

# Calculate fortune for 14-02-1996 (format as YYYY-MM-DD)
fortune_data = calculate_fortune('1996-02-14')

# Print the result
print(json.dumps(fortune_data, indent=2, ensure_ascii=False))

# Print just the summary
print("\n=== Summary ===")
print(fortune_data["summary"])

# Print top interpretations
print("\n=== Top 3 Individual Interpretations ===")
for interp in fortune_data["individual_interpretations"][:3]:
    print(f"{interp['category']} ({interp['meaning']}): {interp['value']} - {interp['influence']}")

# Print top combinations
print("\n=== Top Combinations ===")
for combo in fortune_data["combination_interpretations"][:2]:
    print(f"{combo['heading']}: {combo['meaning']}") 