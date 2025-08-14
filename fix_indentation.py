#!/usr/bin/env python3
"""
Script to fix indentation in the problematic function.
"""

def fix_function_indentation():
    """Fix the indentation in the analyze_response_star_route function"""
    
    with open('synergos/app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the start and end of the problematic function
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        if 'def analyze_response_star_route():' in line:
            start_line = i
        elif start_line is not None and line.strip().startswith('@app.route("/api/summarize_response_to_question"'):
            end_line = i
            break
    
    if start_line is None or end_line is None:
        print("Could not find the function boundaries")
        return
    
    print(f"Function found between lines {start_line + 1} and {end_line}")
    
    # Find the try: line
    try_line = None
    for i in range(start_line, end_line):
        if lines[i].strip() == 'try:':
            try_line = i
            break
    
    if try_line is None:
        print("Could not find the try: line")
        return
    
    # Fix indentation for lines after try:
    for i in range(try_line + 1, end_line):
        line = lines[i]
        if line.strip() and not line.startswith('        ') and not line.strip().startswith('except Exception as e:'):
            # Add 4 more spaces if line starts with 4 spaces or has content
            if line.startswith('    ') and not line.startswith('        '):
                lines[i] = '    ' + line
            elif line.strip() and not line.startswith(' '):
                lines[i] = '        ' + line
    
    # Write the fixed file
    with open('synergos/app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Indentation fixed!")

if __name__ == '__main__':
    fix_function_indentation()