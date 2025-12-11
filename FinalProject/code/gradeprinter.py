import json
import re

class GradePrinter:
    def __init__(self, json_file_path):
        """
        Initialize the grade printer.
        
        Args:
            json_file_path: Path to the JSON file with graded responses
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def print_all_grades(self, output_file=None):
        """
        Print all grades in a readable format.
        
        Args:
            output_file: Optional file path to save output (None = print to console)
        """
        output_lines = []
        
        for student_data in self.data.get('Students', []):
            student_name = student_data.get('Student', 'Unknown')
            
            # Print student header
            output_lines.append("=" * 80)
            output_lines.append(f"STUDENT: {student_name}")
            output_lines.append("=" * 80)
            output_lines.append("")
            
            # Get all questions for this student
            questions = [(k, v) for k, v in student_data.items() 
                        if k.startswith('Question ') and isinstance(v, dict)]
            
            # Sort questions numerically
            questions.sort(key=lambda x: int(x[0].split(' ')[1]))
            
            for question_key, question_data in questions:
                output_lines.append(f"{question_key}:")
                output_lines.append("-" * 80)
                
                # Get all risk/mitigation grades
                grades = []
                for field_name, field_value in question_data.items():
                    if field_name.endswith(' grade'):
                        # Extract the risk/mitigation number
                        match = re.search(r'Risk/mitigation (\d+)', field_name)
                        if match:
                            risk_num = int(match.group(1))
                            grades.append((risk_num, field_value))
                
                # Sort by risk/mitigation number
                grades.sort(key=lambda x: x[0])
                
                # Print each grade
                for risk_num, grade_value in grades:
                    # Parse the grade (format: "points|justification")
                    if '|' in grade_value:
                        points, justification = grade_value.split('|', 1)
                        output_lines.append(f"  Part {risk_num} grade: {points.strip()}")
                        output_lines.append(f"    {justification.strip()}")
                    else:
                        # Fallback if format is different
                        output_lines.append(f"  Part {risk_num} grade: {grade_value}")
                    output_lines.append("")
                
                output_lines.append("")
            
            output_lines.append("")
        
        # Output to file or console
        output_text = '\n'.join(output_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"Grades saved to: {output_file}")
        else:
            print(output_text)
    
    def print_student_grades(self, student_name, output_file=None):
        """
        Print grades for a specific student.
        
        Args:
            student_name: Name of the student
            output_file: Optional file path to save output
        """
        output_lines = []
        
        for student_data in self.data.get('Students', []):
            if student_data.get('Student') == student_name:
                output_lines.append("=" * 80)
                output_lines.append(f"STUDENT: {student_name}")
                output_lines.append("=" * 80)
                output_lines.append("")
                
                questions = [(k, v) for k, v in student_data.items() 
                            if k.startswith('Question ') and isinstance(v, dict)]
                questions.sort(key=lambda x: int(x[0].split(' ')[1]))
                
                for question_key, question_data in questions:
                    output_lines.append(f"{question_key}:")
                    output_lines.append("-" * 80)
                    
                    grades = []
                    for field_name, field_value in question_data.items():
                        if field_name.endswith(' grade'):
                            match = re.search(r'Risk/mitigation (\d+)', field_name)
                            if match:
                                risk_num = int(match.group(1))
                                grades.append((risk_num, field_value))
                    
                    grades.sort(key=lambda x: x[0])
                    
                    for risk_num, grade_value in grades:
                        if '|' in grade_value:
                            points, justification = grade_value.split('|', 1)
                            output_lines.append(f"  Part {risk_num} grade: {points.strip()}")
                            output_lines.append(f"    {justification.strip()}")
                        else:
                            output_lines.append(f"  Part {risk_num} grade: {grade_value}")
                        output_lines.append("")
                    
                    output_lines.append("")
                
                break
        
        output_text = '\n'.join(output_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"Grades for {student_name} saved to: {output_file}")
        else:
            print(output_text)
    
    def print_summary_statistics(self):
        """Print summary statistics for all grades."""
        all_scores = []
        student_scores = {}
        
        for student_data in self.data.get('Students', []):
            student_name = student_data.get('Student', 'Unknown')
            student_total = 0
            student_count = 0
            
            for key, value in student_data.items():
                if key.startswith('Question ') and isinstance(value, dict):
                    for field_name, field_value in value.items():
                        if field_name.endswith(' grade') and '|' in field_value:
                            try:
                                points = float(field_value.split('|')[0].strip())
                                all_scores.append(points)
                                student_total += points
                                student_count += 1
                            except ValueError:
                                pass
            
            if student_count > 0:
                student_scores[student_name] = student_total / student_count
        
        # Print summary
        print("=" * 80)
        print("GRADE SUMMARY")
        print("=" * 80)
        print(f"Total responses graded: {len(all_scores)}")
        if all_scores:
            print(f"Average score: {sum(all_scores) / len(all_scores):.2f}")
            print(f"Highest score: {max(all_scores)}")
            print(f"Lowest score: {min(all_scores)}")
            print()
            print("Student Averages:")
            for student, avg in sorted(student_scores.items(), key=lambda x: x[1], reverse=True):
                print(f"  {student}: {avg:.2f}")
        print("=" * 80)


# Example usage
if __name__ == "__main__":
    # Initialize printer
    printer = GradePrinter("responses_graded.json")
    
    # Option 1: Print all grades to console
    printer.print_all_grades()
    
    # Option 2: Print all grades to a file
    # printer.print_all_grades(output_file="all_grades.txt")
    
    # Option 3: Print grades for a specific student
    # printer.print_student_grades("Alvey, Ethan")
    # printer.print_student_grades("Alvey, Ethan", output_file="alvey_grades.txt")
    
    # Option 4: Print summary statistics
    # printer.print_summary_statistics()