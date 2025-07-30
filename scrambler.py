import re
import random
import os
from pathlib import Path

# Read the original HTML file
with open('aapl_p33.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Dictionary to store original values and their placeholders
value_map = {}
placeholder_counter = 1

# Function to check if a number should be excluded (dates, years in headers, CSS values)
def should_exclude_number(number_str, context_before, context_after):
    """Check if a number should be excluded from scrambling (e.g., dates, years in headers, CSS values)"""
    
    # Remove commas for checking
    clean_number = number_str.replace(',', '')
    
    # Exclude years in the 2020s range (2020-2029)
    if clean_number.isdigit() and 2020 <= int(clean_number) <= 2029:
        return True
    
    # Exclude years in the 2010s range (2010-2019) - might be in historical data
    if clean_number.isdigit() and 2010 <= int(clean_number) <= 2019:
        return True
    
    # Exclude day numbers (1-31) when they appear in date contexts
    if clean_number.isdigit() and 1 <= int(clean_number) <= 31:
        # Check for date-related context
        context = (context_before + context_after).lower()
        if any(month in context for month in ['january', 'february', 'march', 'april', 'may', 'june',
                                            'july', 'august', 'september', 'october', 'november', 'december']):
            return True
    
    # Only exclude CSS styling values if the number is DIRECTLY part of a CSS property
    # Check the immediate context (±50 chars) for CSS property patterns
    immediate_before = context_before[-50:]
    immediate_after = context_after[:50]
    
    # Pattern: property:value (where our number is the value)
    css_property_pattern = r'(width|height|margin|padding|font-size|line-height|top|left|right|bottom|border|text-indent|min-height|max-width|max-height|min-width):\s*$'
    if re.search(css_property_pattern, immediate_before):
        return True
    
    # Exclude percentage values in CSS (number immediately followed by %)
    if immediate_after.startswith('%'):
        return True
    
    # Exclude values immediately followed by CSS units
    css_units = ['pt', 'px', 'em', 'rem', 'vh', 'vw', 'ch', 'ex']
    for unit in css_units:
        if immediate_after.startswith(unit):
            return True
    
    # Exclude document/entity identifiers (long numeric strings like 0000320193)
    if clean_number.isdigit() and len(clean_number) >= 8:
        return True
    
    return False

# Function to create a placeholder for a value
def create_placeholder(value, value_type):
    global placeholder_counter
    placeholder = f"{{{{VALUE_{placeholder_counter}_{value_type.upper()}}}}}"
    value_map[placeholder] = (value, value_type)
    placeholder_counter += 1
    return placeholder

# Function to generate a random value based on the original
def generate_random_value(original_value, value_type):
    if value_type == 'comma_number':
        # For numbers with commas, generate similar magnitude
        clean_num = int(original_value.replace(',', ''))
        magnitude = len(str(clean_num))
        
        # Generate random number with similar magnitude
        if magnitude <= 3:
            random_num = random.randint(100, 999)
        elif magnitude <= 4:
            random_num = random.randint(1000, 9999)
        elif magnitude <= 5:
            random_num = random.randint(10000, 99999)
        else:
            # For larger numbers, vary by ±30%
            variation = int(clean_num * 0.3)
            random_num = random.randint(max(1, clean_num - variation), clean_num + variation)
        
        # Format back with commas
        return f"{random_num:,}"
    
    elif value_type == 'plain_number':
        # For plain numbers without commas
        original_num = int(original_value)
        if original_num < 100:
            return str(random.randint(1, 999))
        else:
            # Vary by ±50% for smaller numbers
            variation = max(1, int(original_num * 0.5))
            return str(random.randint(max(1, original_num - variation), original_num + variation))
    
    return original_value  # Fallback

# Process different types of numerical values
def process_html_content(content):
    processed_content = content
    
    # Pattern 1: Numbers with commas in XBRL tags (e.g., >35,929</ix:nonfraction>)
    def replace_comma_numbers(match):
        full_match = match.group(0)
        number = match.group(1)
        
        # Get context around the match
        start_pos = max(0, match.start() - 200)
        end_pos = min(len(content), match.end() + 200)
        context_before = content[start_pos:match.start()]
        context_after = content[match.end():end_pos]
        
        if should_exclude_number(number, context_before, context_after):
            return full_match  # Don't replace
        
        placeholder = create_placeholder(number, 'comma_number')
        return full_match.replace(number, placeholder)
    
    processed_content = re.sub(r'>([0-9]{1,3}(?:,[0-9]{3})+)</ix:nonfraction>', replace_comma_numbers, processed_content)
    
    # Pattern 2: Plain numbers in XBRL tags (e.g., >895</ix:nonfraction> but not >0000320193</ix:nonfraction>)
    def replace_plain_numbers(match):
        full_match = match.group(0)
        number = match.group(1)
        
        # Skip if this contains a placeholder already
        if 'VALUE_' in full_match:
            return full_match
        
        # Get context around the match
        start_pos = max(0, match.start() - 200)
        end_pos = min(len(content), match.end() + 200)
        context_before = content[start_pos:match.start()]
        context_after = content[match.end():end_pos]
        
        if should_exclude_number(number, context_before, context_after):
            return full_match  # Don't replace
        
        placeholder = create_placeholder(number, 'plain_number')
        return full_match.replace(number, placeholder)
    
    processed_content = re.sub(r'>([0-9]+)</ix:nonfraction>', replace_plain_numbers, processed_content)
    
    return processed_content

# Process the HTML content
print("Processing HTML content...")
processed_content = process_html_content(html_content)

print(f"Found {len(value_map)} unique numerical values to randomize")

# Create output directory
os.makedirs('html_out', exist_ok=True)

# Generate 10 randomized versions
for i in range(1, 11):
    # Create a copy of the processed content
    randomized_content = processed_content
    
    # Replace all placeholders with random values
    for placeholder, (original_value, value_type) in value_map.items():
        random_value = generate_random_value(original_value, value_type)
        randomized_content = randomized_content.replace(placeholder, random_value)
    
    # Write to file
    output_file = f'html_out/{i}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(randomized_content)
    
    print(f"Generated {output_file}")

print("\nRandomization complete!")
print(f"\nPlaceholder mapping (first 10 examples):")
for i, (placeholder, (original, value_type)) in enumerate(list(value_map.items())[:10]):
    print(f"{placeholder}: {original} ({value_type})")

# Save placeholder mapping to CSV file
import csv

mapping_file = 'html_out/placeholder_mapping.csv'
with open(mapping_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Placeholder', 'Original Value', 'Value Type'])
    
    for placeholder, (original, value_type) in value_map.items():
        writer.writerow([placeholder, original, value_type])

print(f"\nPlaceholder mapping saved to: {mapping_file}")
print(f"Total placeholders created: {len(value_map)}")
print(f"\nCSS styling values (widths, heights, margins, etc.) have been preserved to maintain table formatting.")
print(f"Entity identifiers and dates have been preserved while financial values are randomized.")
