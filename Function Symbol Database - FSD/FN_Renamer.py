import re
import sys
import os

def normalize_function_names(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Reading file: {input_file}")
    
    addr_to_stdname = {}
    
    definition_pattern = re.compile(r'^(sub_[0-9A-Fa-f]+)\s*\|\s*([^\|]+?)\s*\|', re.MULTILINE)
    
    for match in definition_pattern.finditer(content):
        address = match.group(1)
        std_name = match.group(2).strip()
        addr_to_stdname[address] = std_name
    
    print(f"Found {len(addr_to_stdname)} standardized functions:")
    for addr, name in list(addr_to_stdname.items())[:5]:
        print(f"   {addr} -> {name}")
    if len(addr_to_stdname) > 5:
        print(f"   ... and {len(addr_to_stdname) - 5} more")
    
    def smart_replace(match):
        full_match = match.group(0)
        addr = match.group(1)
        
        start_pos = match.start()
        
        line_start = content.rfind('\n', 0, start_pos) + 1
        line_end = content.find('\n', start_pos)
        if line_end == -1:
            line_end = len(content)
        
        current_line = content[line_start:line_end]
        
        first_pipe = current_line.find('|')
        
        if first_pipe != -1:
            abs_first_pipe = line_start + first_pipe
            
            if start_pos < abs_first_pipe:
                return full_match
        
        if addr in addr_to_stdname:
            return addr_to_stdname[addr]
        return full_match
    
    function_pattern = re.compile(r'(sub_[0-9A-Fa-f]+)')
    
    new_content = function_pattern.sub(smart_replace, content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    changes = sum(1 for a,b in zip(content.splitlines(), new_content.splitlines()) if a != b)
    
    print(f"\nOperation completed successfully!")
    print(f"Output: {output_file}")
    print(f"Lines changed: {changes}")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Correct usage:")
        print(f"   py {os.path.basename(__file__)} .txt")
        print("\nNote: Output file will be automatically created as .txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if input_file.endswith('.txt'):
        output_file = input_file[:-4] + '2.txt'
    else:
        output_file = input_file + '_normalized.txt'
    
    print("=" * 50)
    print("Function Name Normalization Tool")
    print("=" * 50)
    print(f"Input file : {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 50)
    
    success = normalize_function_names(input_file, output_file)
    
    if not success:
        sys.exit(1)
    
    print("\nDone!")

if __name__ == "__main__":
    main()