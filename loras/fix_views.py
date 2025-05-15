# Fix indentation in views.py
with open('loras/boutiqe/views.py', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Find the problem area
in_try_block = False
problem_fixed = False
for i in range(len(lines)):
    if 'try:' in lines[i]:
        in_try_block = True
    
    if in_try_block and 'messages.success(request, f' in lines[i]:
        # Check if the next line contains "except" with improper indentation
        next_line_index = i + 2
        if next_line_index < len(lines) and 'except Exception as e:' in lines[next_line_index]:
            # Insert proper indentation
            print(f"Found problem at line {i+1}, fixing...")
            indentation = ' ' * 8  # Assuming 8 spaces indentation
            lines[i] = indentation + lines[i].lstrip()
            lines[i+1] = indentation + lines[i+1].lstrip()
            problem_fixed = True
            break

if problem_fixed:
    with open('loras/boutiqe/views.py', 'w', encoding='utf-8') as file:
        file.writelines(lines)
    print("Fixed the indentation issue!")
else:
    print("Problem not found. Check the file structure.") 