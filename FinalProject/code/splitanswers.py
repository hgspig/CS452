# -*- coding: utf-8 -*-

import json
from openai import OpenAI
from secrets import OPENAPI_API_KEY as key

OPENAI_API_KEY = key
client = OpenAI(api_key=OPENAI_API_KEY)

def get_clean_json():
    prompt = """
        You are splitting student answers for a midterm. 
        The current format is in csv but I need you to output it in json. The current format is: Student,Question 1,Question 2,Question 3,Question 4,Question 5 
        You need to convert it into json with this format:

        {
        "Students": [
            {
            "Student": "name",
            "Question 1": {
                "Risk/mitigation 1": "...",
                "Risk/mitigation 2": "...",
                "Risk/mitigation 3": "...",
                "Risk/mitigation 4": "...",
                "Risk/mitigation 5": "...",
                "AI usage": ""
            }
        }
        ...
        ]
        }

        If a student does not mention AI for any of the questions, leave it as "".
        Do not change ANY content from the student.

        Final answer: only valid JSON

        Student responses:
        "sample","#1: Risk: Toolchain inconsistencies in hybrid setups leading to deployment failures. With team members using varying DevOps tools like Kubernetes vs. Docker Compose, integration errors could arise during containerization, delaying the ERP refactor and amplifying downtime risks. Citation: DeMarco & Lister, Peopleware, Ch. 5 (discusses how mismatched environments erode productivity and foster "flow" interruptions) #2: Mitigation: Standardize tooling through team training sessions. Form a subgroup to enforce unified tools and conduct workshops, ensuring compatibility in CI/CD pipelines to streamline migrations and patches. Citation: Lecture on Team Dynamics (Knutson podcast #4), emphasizing sociological alignment in ambiguous tech stacks #3: Risk: Security vulnerabilities from third-party libraries post-exploit. The urgent patch could introduce regressions in AI analytics if not thoroughly tested, potentially exposing supply chain data in a high-stakes enterprise system. Citation: Brooks, The Mythical Man-Month, Ch. 6 (highlights the challenges of system integration and unforeseen bugs in complex additions like patches) #4: Mitigation: Implement incremental rollouts with monitoring. Deploy changes in stages, using feedback loops to catch issues early from the cyber incident, balancing speed with robustness. Citation: Brooks, The Mythical Man-Month, Ch. 7 (advocates for incremental planning and safeguards against complexities in large-scale projects) #5: Risk: Requirements creep from business units without assessments. Adding custom dashboards mid-refactor could inflate scope, straining resources already diverted by the security incident and executive pressures. Citation: DeMarco & Lister, Peopleware, Ch. 3 (warns about managerial pressures that lead to unchecked interruptions and scope expansion) AI usage: I used Grok with the prompt “Give me a list of risks that cloud-native refactors could have involving security incidents.” I then built off this list and combined with the preliminary ideas to ensure I covered everything we talked about in class."
        """

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You return ONLY valid JSON. No markdown, no commentary."},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content.strip()

    # Remove accidental markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()

    return raw

json_text = get_clean_json()

try:
    data = json.loads(json_text)
except json.JSONDecodeError as e:
    print("JSON was invalid. Here's the raw output so you can inspect it:")
    print(json_text)
    raise e

with open("example.json", "w") as f:
    json.dump(data, f, indent=4)

print("Saved example.json")
