import os
import json
from openai import OpenAI
from typing import Dict, List, Tuple
from collections import defaultdict
from secrets import OPENAPI_API_KEY as key

class CitationGrader:
    def __init__(self, books_directory, api_key=None):
        """
        Initialize the grader.
        
        Args:
            books_directory: Path to the Books folder containing all sources
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
        """
        self.books_directory = books_directory
        self.client = OpenAI(api_key=api_key)
        self.citation_cache = {}  # Cache loaded citation files
        
    def load_citation_file(self, citation_path):
        """Load and cache citation file content."""
        if not citation_path or citation_path == "NOT_FOUND":
            return None
            
        # Check cache first
        if citation_path in self.citation_cache:
            return self.citation_cache[citation_path]
        
        # Load file
        full_path = os.path.join(self.books_directory, citation_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.citation_cache[citation_path] = content
                return content
        except FileNotFoundError:
            print(f"Warning: Citation file not found: {full_path}")
            return None
    
    def group_responses_by_citation(self, data, question_prompts):
        """
        Group responses by citation file for efficient batch processing.
        
        Returns:
            Dict[citation_file] -> List[(student_name, question_num, risk_num, response_text, ai_usage)]
        """
        grouped = defaultdict(list)
        
        for student_data in data.get('Students', []):
            student_name = student_data.get('Student', 'Unknown')
            
            for key, value in student_data.items():
                if key.startswith('Question ') and isinstance(value, dict):
                    question_num = key.split(' ')[1]
                    question_prompt = question_prompts.get(key, "")
                    
                    for field_name, field_value in value.items():
                        if field_name.startswith('Risk/mitigation ') and not field_name.endswith((' citation', ' grade')):
                            # Extract risk number
                            risk_num = field_name.split(' ')[1]
                            
                            # Get corresponding citation
                            citation_key = f"{field_name} citation"
                            citation_file = value.get(citation_key)
                            
                            # Get AI usage
                            ai_usage = value.get('AI usage', '')
                            
                            # Group by citation file
                            grouped[citation_file].append({
                                'student': student_name,
                                'question_num': question_num,
                                'question_prompt': question_prompt,
                                'risk_num': risk_num,
                                'response': field_value,
                                'ai_usage': ai_usage,
                                'field_name': field_name
                            })
        
        return grouped
    
    def grade_batch(self, citation_file, responses, citation_content):
        """
        Grade a batch of responses that all cite the same file.
        
        Args:
            citation_file: The citation file path
            responses: List of response dicts
            citation_content: The content of the citation file
            
        Returns:
            List[str]: Grades in same order as responses
        """
        # Build the prompt with all responses
        rubric = """GRADING RUBRIC:
		- 0 points: No text entered for answer (answer couldn't be found)
		- 2 points: Factually incorrect
		- 3 points: Overall idea is correct, but citation is wrong or misused
		- 4 points: Answer is only 1-2 sentences
		- 5 points: Answer is 3+ sentences
        This is for each part of the question. Then the question as a whole can have these deductions:
		- -1 point: Explained AI usage but didn't provide exact prompt explanation
		- -2 points: Only stated they used AI without explaining how, OR didn't state whether they used AI

		IMPORTANT: Start with the base points (0-25), then apply AI usage penalties at the end for the overall question (becomes 23-24 instead of 25)."""

        # Create citation context
        citation_context = ""
        if citation_content:
            citation_context = f"""
		CITATION SOURCE CONTENT:
		File: {citation_file}
		---
		{citation_content[:4000]}  # Limit to ~4000 chars to manage token usage
		---
		"""
        else:
            citation_context = f"\nCITATION SOURCE: {citation_file} (FILE NOT FOUND - students citing this have incorrect citations)\n"
        
        # Build responses section
        responses_text = ""
        for idx, resp in enumerate(responses, 1):
            responses_text += f"""
				RESPONSE #{idx}:
				Student: {resp['student']}
				Question {resp['question_num']}: {resp['question_prompt']}
				Risk/Mitigation {resp['risk_num']}: {resp['response']}
				AI Usage Statement: {resp['ai_usage']}
				---
				"""
        
        prompt = f"""{rubric}

{citation_context}

Grade each of the following responses. For EACH response, verify:
That the citation is from the linked work and that it mostly lines up with the content cited in that chapter/work.
If a citation is for mythical man month (MMM) make sure it's not just a chapter title. It needs to have a subheading, page number or direct quote. 
If a response doesn't have a citation or doesn't follow what I've outlined, flag it with an incorrect citation (3 points as outlined below)
If the overall question responses don't have a specific explanation of how they used AI -1 points from the overall question score
If a response is only 1-2 sentences then it should only get 4 points. 

{responses_text}

Return your grades in this EXACT format for each response:
RESPONSE #1: [points]|[a very concise and short (5-7 word) justification including: base score and one of these reasons: 5: full points; 4: if only 1-2 sentences; 3: citation isn't specific; 2: inappropriate answer or irrelevant citation; and 0: answer missing]
RESPONSE #2: [points]|[justification]
...

Be strict but fair. Verify citations match the actual source material content. Don't use any dashes (including m dashes)"""

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strict but fair academic grader. Follow the rubric precisely and verify citations against the actual source material."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Slightly higher for nuanced grading
                max_tokens=2000
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse the grades
            grades = []
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith('RESPONSE #'):
                    # Extract grade in format "RESPONSE #X: points|justification"
                    try:
                        parts = line.split(':', 1)[1].strip()
                        grades.append(parts)
                    except:
                        grades.append("ERROR|Could not parse grade")
            
            return grades
            
        except Exception as e:
            print(f"Error grading batch: {e}")
            return [f"ERROR|Grading failed: {str(e)}"] * len(responses)
    
    def grade_all_responses(self, input_json_path, question_prompts, output_json_path=None, batch_size=10):
        """
        Grade all responses in the JSON file.
        
        Args:
            input_json_path: Path to JSON with responses and citations
            question_prompts: Dict mapping question keys to prompt text
            output_json_path: Where to save output (None = overwrite input)
            batch_size: Max responses to grade per API call
        """
        # Load data
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Group responses by citation
        print("Grouping responses by citation file...")
        grouped = self.group_responses_by_citation(data, question_prompts)
        
        print(f"\nFound {len(grouped)} unique citation files")
        print(f"Total responses to grade: {sum(len(resps) for resps in grouped.values())}\n")
        
        # Process each citation group
        total_graded = 0
        for citation_file, responses in grouped.items():
            print(f"\nProcessing citation: {citation_file or 'NO_CITATION'}")
            print(f"  Responses using this citation: {len(responses)}")
            
            # Load citation content once
            citation_content = self.load_citation_file(citation_file)
            
            # Process in batches
            for i in range(0, len(responses), batch_size):
                batch = responses[i:i+batch_size]
                print(f"  Grading batch {i//batch_size + 1} ({len(batch)} responses)...", end=' ')
                
                grades = self.grade_batch(citation_file, batch, citation_content)
                
                # Apply grades back to original data
                for resp, grade in zip(batch, grades):
                    # Find the student and question in original data
                    for student_data in data['Students']:
                        if student_data['Student'] == resp['student']:
                            question_key = f"Question {resp['question_num']}"
                            if question_key in student_data:
                                grade_key = f"{resp['field_name']} grade"
                                student_data[question_key][grade_key] = grade
                                total_graded += 1
                                break
                
                print("✓")
        
        # Save results
        output_path = output_json_path or input_json_path
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Grading complete!")
        print(f"Total responses graded: {total_graded}")
        print(f"Output saved to: {output_path}")
        print(f"{'='*60}")
        
        return data


# Example usage
if __name__ == "__main__":
    # Define your question prompts
    question_prompts = {
        "Question 1": """Your team is developing a healthcare mobile app for a hospital network that handles patient data, appointment scheduling, and telemedicine features. The project began with well-defined requirements, but midway through, a new regulatory change (e.g., updated HIPAA compliance rules) requires integrating advanced encryption and audit logging. Simultaneously, the client insists on adding AI-driven symptom checkers using third-party APIs, while the team's senior developer leaves unexpectedly, forcing juniors to take on complex tasks. The deadline remains fixed, and budget constraints prevent hiring replacements quickly, leading to improvised code reviews via asynchronous tools.

Identify five risks and/or mitigations for potential risks/problems (numbered #1 through #5), each with explanations and citations. Then, state AI usage.""",
        "Question 2": """A global fintech company is overhauling its legacy banking software to a microservices architecture in the cloud. The 15-person team is distributed across five time zones, including regions with varying internet reliability, and relies on a mix of Slack, Jira, and video calls for coordination. No formal project manager is assigned; instead, a "flat" structure encourages self-organization, but cultural differences lead to miscommunications about priorities. Early on, the team discovers incompatible data formats from the old system, requiring custom migration scripts, while stakeholders push for blockchain integration without clear ROI analysis.

Identify five risks and/or mitigations for potential risks/problems (each numbered #1 through #5), with explanations and citations. Then, state AI usage.""",
		"Question 3": """You're managing a project for an e-commerce platform upgrade that includes real-time inventory tracking, personalized recommendations via machine learning, and integration with multiple payment gateways. Initial estimates were optimistic at 8 months, but after 4 months, user testing reveals overlooked accessibility issues for diverse user groups (e.g., international locales and disabilities). To accelerate, the team adds three new contractors mid-project, who bring expertise but unfamiliar tools, while the original team resists changes to their established workflows. External market pressures, like a competitor's launch, tempt cutting QA cycles.

Identify five risks and/or mitigations for potential risks/problems (each numbered #1 through #5), with explanations and citations. Then, state AI usage.""",
		"Question 4": """On a defense-contracted software project for simulation tools, the team of 8 experts excels in algorithms but struggles with interpersonal conflicts, including debates over modular vs. monolithic designs amplified by remote work setups. The workspace is a hybrid model with some in a noisy co-working space and others at home, leading to inconsistent participation in stand-ups. Security requirements demand frequent code audits, but tool incompatibilities cause delays, and a key stakeholder from the client side provides contradictory feedback loops without documented rationale.

Identify five risks and/or mitigations for potential risks/problems (numbered #1 through #5), with explanations and citations. Then, state AI usage.""",
		"Question 5": """A venture-backed startup is creating an AI-powered educational platform with adaptive learning paths, gamification, and natural language processing for content generation. Requirements started vague ("engaging for K-12 students"), evolving into demands for multi-language support and data privacy features amid shifting investor priorities. The lead engineer advocates for unproven open-source frameworks to innovate, deferring prototyping, while the small team (including interns) works in silos without integrated testing environments. Budget overruns from cloud costs prompt skipping formal retrospectives.

Identify five risks and/or mitigations for potential risks/problems (each numbered #1 through #5), with explanations and citations. Then, state AI usage."""
        # Add more as needed
    }
    
    # Initialize grader
    grader = CitationGrader(
        books_directory="Books",
        api_key=key
    )
    
    # Grade all responses
    grader.grade_all_responses(
        input_json_path="responses_with_citations_short.json",
        question_prompts=question_prompts,
        output_json_path="responses_graded.json",
        batch_size=10  # Adjust based on token limits
    )
    
    # Output will look like:
    # "Risk/mitigation 1": "...",
    # "Risk/mitigation 1 citation": "Mythical-man-month/Chapter-4.txt",
    # "Risk/mitigation 1 grade": "5|Good response with 4+ sentences. Citation correctly references Brooks' discussion of requirements. AI usage properly disclosed with example prompt. Base: 5 points, no penalties."