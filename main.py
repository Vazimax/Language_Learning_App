import os
import replicate
import streamlit as st

# Set up the Replicate API token
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API')
os.environ['REPLICATE_API_TOKEN'] = REPLICATE_API_TOKEN

# Initialize Replicate client
replicate.Client(api_token=REPLICATE_API_TOKEN)

st.title('Language Learning')

# Choose the language
languages = ['English', 'Arabic', 'Darija', 'German','Spanich','French','Chinese','Japanese']
language = st.selectbox('Select your language level', languages)

# Define language levels
levels = ['Absolute Beginner', 'Beginner', 'Intermediate', 'Advanced']
level = st.selectbox('Select your language level', levels)

# Input for the topic
topic = st.text_area("What's the topic you want it to cover?")

# Initialize session state variables
if 'text' not in st.session_state:
    st.session_state.text = ''
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'questions_generated' not in st.session_state:
    st.session_state.questions_generated = False

def get_response(prompt):
    try:
        output = replicate.run(
            "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
            input={"prompt": prompt, "max_length": 500, "temperature": 0.7}
        )
        return ''.join(output)
    except replicate.exceptions.ReplicateError as e:
        st.error(f"Replicate API Error: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def parse_questions(text):
    questions = []
    current_question = {}
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('Q'):
            if current_question:
                questions.append(current_question)
            current_question = {'question': line.split(':', 1)[1].strip(), 'options': [], 'answer': ''}
        elif line.startswith(('A.', 'B.', 'C.', 'D.')):
            current_question['options'].append(line)
        elif line.lower().startswith('answer:'):
            current_question['answer'] = line.split(':')[1].strip()
    if current_question:
        questions.append(current_question)
    return questions

if st.button('Generate Text'):
    if topic and level:
        with st.spinner('Generating the text ...'):
            prompt = f"Generate a short text (about 100-150 words) for language learning. The text should be suitable for a {level} level learner and cover the topic of {topic} in {language}."
            response = get_response(prompt)
            if response:
                st.session_state.text = response.strip()
                st.session_state.questions_generated = False
                st.session_state.questions = []  # Clear previous questions
            else:
                st.error("Failed to generate text. Please try again.")

if st.session_state.text:
    st.write("Generated Text:")
    st.write(st.session_state.text)
    
    if not st.session_state.questions_generated and st.button('Generate Questions'):
        with st.spinner('Generating questions ...'):
            prompt = f"""Based on the following text, generate 3 multiple-choice questions. Each question should have 4 options (A, B, C, D) with one correct answer.
            Format the output as follows:
            
            Q1: [Question 1]
            A. [Option A]
            B. [Option B]
            C. [Option C]
            D. [Option D]
            Answer: [Correct answer letter]
            
            Q2: [Question 2]
            ...
            
            Q3: [Question 3]
            ...
            
            Text: {st.session_state.text}"""
            
            questions_text = get_response(prompt)
            if questions_text:
                st.session_state.questions = parse_questions(questions_text)
                st.session_state.questions_generated = True
            else:
                st.error("Failed to generate questions. Please try again.")

if st.session_state.questions_generated:
    st.write('Generated Questions:')
    user_answers = []
    for i, q in enumerate(st.session_state.questions):
        st.write(f"Q{i+1}: {q['question']}")
        options = [opt.split('. ', 1)[1] for opt in q['options']]  # Remove the option letter
        user_answer = st.radio(f"Select your answer:", options, key=f"question_{i}")
        user_answers.append(chr(65 + options.index(user_answer)))  # Convert index to letter (A, B, C, D)
        
    # Assess answers button
    if st.button('Assess Answers'):
        correct_answers = [q['answer'] for q in st.session_state.questions]
        score = sum(1 for ua, ca in zip(user_answers, correct_answers) if ua == ca)
        total_questions = len(st.session_state.questions)
        st.write(f"Your score: {score}/{total_questions}")

        # Display correct answers
        st.write("Correct Answers:")
        for i, (q, ca) in enumerate(zip(st.session_state.questions, correct_answers)):
            st.write(f"Q{i+1}: {ca}")