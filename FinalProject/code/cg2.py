import os
import json
from openai import OpenAI
from typing import Dict, Any, List
from secrets import OPENAPI_API_KEY as key

class CitationFileLocator:
    def __init__(self, books_directory, api_key=None):
        """
        Initialize the citation locator.
        
        Args:
            books_directory: Path to the Books folder containing all sources
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
        """
        self.books_directory = books_directory
        self.client = OpenAI(api_key=api_key)
        self.file_index = self._build_file_index()
    
    def _build_file_index(self):
        """Build an index of all available files with their metadata."""
        file_index = []
        
        for root, dirs, files in os.walk(self.books_directory):
            for file in files:
                if file.endswith('.txt'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.books_directory)
                    
                    parts = rel_path.split(os.sep)
                    
                    file_info = {
                        'path': rel_path,
                        'filename': file,
                        'collection': parts[0] if len(parts) > 0 else '',
                        'full_path': full_path
                    }
                    
                    file_index.append(file_info)
        
        return file_index
    
    def _create_file_list_prompt(self):
        """Create a formatted list of available files for the prompt."""
        file_list = []
        for idx, file_info in enumerate(self.file_index, 1):
            file_list.append(f"{idx}. {file_info['path']}")
        
        return "\n".join(file_list)
    
    def identify_citation_file(self, response_text):
        """
        Use OpenAI API to identify which file contains the citation.
        
        Args:
            response_text: The text containing the citation reference
            
        Returns:
            str: The file path, or None if not found
        """
        # Skip if text is empty or too short
        if not response_text or len(response_text.strip()) < 10:
            return None
            
        file_list = self._create_file_list_prompt()
        
        prompt = f"""You are a citation file locator. Given a response text that contains citations, identify which file from the available files list contains the cited source.

Available files:
{file_list}

Response text:
{response_text}

Instructions:
1. Identify the citation in the response text (book title, chapter, author, article name, etc.)
2. Match it to the most appropriate file from the available files list
3. Return ONLY the file path exactly as it appears in the list above
4. If multiple files match, return the most specific match
5. If no file matches, return "NOT_FOUND"

Return only the file path, nothing else."""

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise citation matcher. Return only the exact file path from the provided list."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=350
            )
            
            file_path = completion.choices[0].message.content.strip()
            
            if file_path == "NOT_FOUND":
                return None
            
            valid_paths = [f['path'] for f in self.file_index]
            if file_path in valid_paths:
                return file_path
            else:
                return self._fuzzy_match(file_path)
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
    
    def _fuzzy_match(self, returned_path):
        """Try to match a returned path to an actual file if exact match fails."""
        returned_lower = returned_path.lower().replace('\\', '/')
        
        for file_info in self.file_index:
            file_path_lower = file_info['path'].lower().replace('\\', '/')
            
            if returned_lower in file_path_lower or file_path_lower in returned_lower:
                return file_info['path']
        
        return None
    
    def process_json_file(self, input_json_path, output_json_path=None):
        """
        Process a JSON file and add citation fields for each risk/mitigation.
        
        Args:
            input_json_path: Path to input JSON file
            output_json_path: Path to save output (if None, overwrites input)
            
        Returns:
            Dict: The processed data
        """
        # Read the JSON file
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process each student
        total_citations = 0
        found_citations = 0
        
        for student_data in data.get('Students', []):
            student_name = student_data.get('Student', 'Unknown')
            print(f"\nProcessing student: {student_name}")
            
            # Process each question
            for key, value in student_data.items():
                if key.startswith('Question ') and isinstance(value, dict):
                    print(f"  {key}")
                    
                    # Process each risk/mitigation
                    for field_name, field_value in list(value.items()):
                        if field_name.startswith('Risk/mitigation ') and not field_name.endswith(' citation'):
                            total_citations += 1
                            print(f"    Processing {field_name}...", end=' ')
                            
                            # Get citation file
                            citation_file = self.identify_citation_file(field_value)
                            
                            # Add citation field
                            citation_key = f"{field_name} citation"
                            value[citation_key] = citation_file if citation_file else "NOT_FOUND"
                            
                            if citation_file:
                                found_citations += 1
                                print(f"✓ {citation_file}")
                            else:
                                print("✗ NOT_FOUND")
        
        # Save the updated JSON
        output_path = output_json_path or input_json_path
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"Total citations processed: {total_citations}")
        print(f"Citations found: {found_citations}")
        print(f"Citations not found: {total_citations - found_citations}")
        print(f"Output saved to: {output_path}")
        print(f"{'='*60}")
        
        return data
    
    def process_single_student(self, data: Dict, student_name: str) -> Dict:
        """
        Process citations for a single student (useful for testing).
        
        Args:
            data: The full JSON data structure
            student_name: Name of student to process
            
        Returns:
            Dict: Updated data
        """
        for student_data in data.get('Students', []):
            if student_data.get('Student') == student_name:
                print(f"\nProcessing student: {student_name}")
                
                for key, value in student_data.items():
                    if key.startswith('Question ') and isinstance(value, dict):
                        for field_name, field_value in list(value.items()):
                            if field_name.startswith('Risk/mitigation '):
                                citation_file = self.identify_citation_file(field_value)
                                citation_key = f"{field_name} citation"
                                value[citation_key] = citation_file if citation_file else "NOT_FOUND"
                                print(f"  {field_name}: {citation_file or 'NOT_FOUND'}")
                
                break
        
        return data


# Example usage
if __name__ == "__main__":
    # Initialize the locator
    locator = CitationFileLocator(
        books_directory="Books",
        api_key=key  # Or set OPENAI_API_KEY env var
    )
    
    # Process the entire JSON file
    # locator.process_json_file(
    #     input_json_path="responses.json",
    #     output_json_path="responses_with_citations.json"  # Or None to overwrite
    # )
    
    # Alternative: Test with a single student first
    with open("responses.json", 'r') as f:
        data = json.load(f)
    locator.process_single_student(data, "student name")
    with open("students_graded.json", 'w') as f:
        json.dump(data, f, indent=2)