import sys

def patch_file():
    try:
        # Open the file
        with open('boutiqe/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # The function we want to remove
        function_to_remove = '''def save_contact_info(request, name, phone, address, city='', note=''):
    """
    حفظ معلومات الاتصال للمستخدم أو الزائر في الجلسة
    """
    # تخزين معلومات الاتصال في جلسة المستخدم
    contact_info = {
        'name': name,
        'phone': phone,
        'address': address,
        'city': city,
        'note': note
    }
    
    # حفظ في الجلسة
    request.session['contact_info'] = contact_info
    
    return contact_info'''
        
        # Remove the function
        if function_to_remove in content:
            content = content.replace(function_to_remove, '')
            print("Function found and removed!")
        else:
            print("Function not found in the file.")
        
        # Write the file back
        with open('boutiqe/views.py', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("File updated successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    patch_file() 