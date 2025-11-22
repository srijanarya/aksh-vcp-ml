import re

text = """received a Letter of Intent (LOI) amounting to
₹27,77,69,586.82 /- (Rupees Twenty Seven Crores Seventy Seven Lakhs Sixty Nine Thousand Five Hundred
Eighty-Six and Paisa Eighty Two only) from Rajasthan Rajya Vidyut Prasaran Nigam Limited for executing the
works"""

client_pattern = r"(?:received|bagged|awarded|secured).*(?:order|contract|loi|letter of intent).*(?:from|by)\s+([A-Z][a-zA-Z0-9\s\.\,\(\)\-]+?)(?:\.|for|worth|dated|vide|against)"

match = re.search(client_pattern, text, re.IGNORECASE)
if match:
    print("Match found:")
    print(f"Client: '{match.group(1).strip()}'")
else:
    print("No match found")
    print("Let me try a simpler pattern...")
    
    # Try just "from [Name]"
    simple_pattern = r"from\s+([A-Z][a-zA-Z0-9\s\.\,\(\)\-]+?)(?:\s+for)"
    simple_match = re.search(simple_pattern, text)
    if simple_match:
        print(f"Simple pattern worked: '{simple_match.group(1).strip()}'")
