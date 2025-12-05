For my project, I'm creating a multi-agent grader for the class I TA for (CS 428).
The first agent takes in a CSV with all the students' answers. It splits the answers by part (each answer has five portions). Then it returns it as a full JSON file.
The second agent takes in this JSON file of student responses and analyzes each student's answer based on the rubric. As part of this, it verifies the students' citations by comparing them with the books they're citing.
It will return the suggested grades with justification, and flag any low scores so that I can manually grade them. 

I've outlined the tools I'm planning on using and the formats I'm expecting. Circle's represent Data and squares represent agents and scripts. Arrows show where the data is inputted and produced. 
![Initial Design](InitialDesign.JPG)

By my class presentation I want a working grader that takes in the whole class and outputs accurate grade suggestions for each student based on the rubric. 