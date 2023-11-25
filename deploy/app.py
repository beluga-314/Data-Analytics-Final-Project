from flask import Flask, render_template, request
import joblib
import re
import pickle

app = Flask(__name__, template_folder='./')

# Function to convert user input into a data point
def create_data_point(program, discipline, gpa, skills, courses):
    data_point = {
        'program': int(program),
        'discipline': int(discipline),
        'gpa': float(gpa),
    }
    data_point = generate_course_features(data_point, courses)
    data_point = generate_skill_features(data_point, skills)
    feature_order = ['gpa', 'discipline', 'program', 'aero', 'aero_skills', 'analytics', 'analytics_skills', 'chem',
                 'chem_skills', 'comm', 'comm_skills', 'da', 'da_skills', 'des', 'des_skills', 'ds', 'ds_skills', 'ee',
                 'ee_skills', 'mech', 'mech_skills', 'misc', 'misc_skills', 'mm', 'mm_skills', 'rob', 'rob_skills',
                 'sde', 'sde_skills', 'vlsi', 'vlsi_skills']
    X_test = [[data_point.get(feature, 0) for feature in feature_order]]
    # print(X_test)
    return X_test


sector_map = {
    'ds': 'Data Science',
    'sde': 'Software Development',
    'des': 'Design',
    'ee' : 'Electrical Engineering',
    'aero': 'Aerospace',
    'vlsi' : 'VLSI',
    'analytics': 'Data Analytics',
    'chem': 'Chemical Engineering',
    'mech': 'Mechanical Engineering',
    'misc': 'Misc',
    'comm': 'Communications',
    'rob' : 'Robotics',
    'mm':'Multimedia systems',
    'da':'Data Science'
}

numerical_map = {
    0: 'ds',
    1: 'sde',
    2: 'des',
    3: 'ee',
    4: 'aero',
    5: 'vlsi',
    6: 'analytics',
    7: 'chem',
    8: 'mech',
    9: 'misc',
    10: 'comm',
    11: 'rob',
    12: 'mm',
    13: 'da'
}

with open('./course_keywords.pkl', 'rb') as file:
    transformed_keywords = pickle.load(file)
with open('./skill_keywords.pkl', 'rb') as file:
    skill_keywords = pickle.load(file)


# Add a new function to find the max slot
def get_max_slot(probabilities):
    return max(probabilities.items(), key=lambda x: x[1])[0] if probabilities else ''

# Function to preprocess data for ML model
def generate_course_features(data_point, courses):

    # Remove NaN values (if any) and concatenate course names
    course_names = ' '.join([str(course) for course in courses])

    # Tokenize course names into words (you can adjust the regex pattern as needed)
    words = re.findall(r'\b\w+\b', course_names.lower())

    # Remove stop words
    with open('stopwords_set.pkl', 'rb') as file:
        stop_words = pickle.load(file)
    words = [word for word in words if word not in stop_words]

    # Get unique words
    unique_words = set(words)

    # Extract keywords (words) from the unique words
    keywords = list(unique_words)

    # Update the corresponding transformed columns based on the keywords
    for key,_ in sector_map.items():
        matching_positions = set(keywords) & set(transformed_keywords.get(key, []))

        # Use a cutoff value (you can adjust this value)
        cutoff = 5
        if len(matching_positions) >= cutoff:
            data_point[key] = 1
        else:
            data_point[key] = 0

    return data_point


def generate_skill_features(data_point, skills):
    # Remove NaN values (if any) and concatenate course names
    skill_names = ' '.join([str(skill) for skill in skills])

    # Tokenize course names into words (you can adjust the regex pattern as needed)
    words = re.findall(r'\b\w+\b', skill_names.lower())

    # Remove stop words
    with open('stopwords_set.pkl', 'rb') as file:
        stop_words = pickle.load(file)
    words = [word for word in words if word not in stop_words]

    # Get unique words
    unique_words = set(words)

    # Extract keywords (words) from the unique words
    keywords = list(unique_words)

    # Update the corresponding transformed columns based on the keywords
    for key,_ in sector_map.items():
        matching_positions = set(keywords) & set(skill_keywords.get(key + '_skills', []))

        # Use a cutoff value (you can adjust this value)
        cutoff = 5
        if len(matching_positions) >= cutoff:
            data_point[key+'_skills'] = 1
        else:
            data_point[key+'_skills'] = 0

    return data_point

def run_ml_model(X_test):
    # Replace this with your actual ML model logic
    slot_model = joblib.load('random_forest_model.joblib')
    slots_test = slot_model.predict_proba(X_test)
    probabilities = {
        'Slot 1': round(slots_test[0][0], 2),
        'Slot 2': round(slots_test[0][1], 2),
        'Slot 3': round(slots_test[0][2], 2)
    }

    ctc_model = joblib.load('random_forest_model_regression_ctc 1.joblib')
    ctc_test = ctc_model.predict(X_test)

    sector_model = joblib.load('random_forest_model_sector.joblib')
    sect = sector_model.predict_proba(X_test)[0]
    threshold = 0.2
    top_classes_indices = [index for index, value in enumerate(sect) if value > threshold]
    top_sec = [sector_map.get(numerical_map[class_index], 'Unknown') for class_index in top_classes_indices]
    return probabilities, round(ctc_test[0]/ 100000, 2), top_sec

# Dictionary to map option values to labels for program and discipline
PROGRAM_OPTIONS = {
    '1': 'M.Tech',
    '2': 'M.Tech(Res)',
    '3': 'PhD(Eng)',
    '4': 'MSc(Res)',
    '5': 'BSc(Res)',
    '6': 'M.Mgmt',
    '7': 'M.Des',
    '8': 'PhD(Sci)',
    '9': 'PhD',
    '10': 'Post Doc'
}

DISCIPLINE_OPTIONS = {
    '0': 'Instrumentation Systems',
    '1': 'Biology',
    '2': 'Mechanical Sciences',
    '3': 'Electronic Product Design',
    '4': 'Quantum Technology',
    '5': 'Electronic Systems Engineering',
    '6': 'Centre for Nano Science & Engineering',
    '7': 'Robotics and Autonomous Systems',
    '8': 'Computational and Data Science',
    '9': 'Chemical Science',
    '10': 'Material Sciences',
    '11': 'BSc (Res) Mathematics',
    '12': 'BSc (Research) in Chemistry',
    '13': 'Management Studies',
    '14': 'Post Doc',
    '15': 'MSc (Research) in Physics',
    '16': 'Nano Science and Engineering',
    '17': 'Smart Manufacturing',
    '19': 'Sustainable Technologies',
    '20': 'Civil Engineering',
    '21': 'Signal Processing',
    # '22': 'Computer Science and Automation',
    '23': 'Materials Engineering',
    '24': 'Master of Product Design and Manufacturing',
    '25': 'Master of Business Analytics & Technology Management',
    '26': 'Solid State and Structural Chemistry Unit',
    '27': 'Earth & Environmental Sciences',
    '29': 'Artificial Intelligence',
    # '28': 'Mathematics',
    # '30': 'Microelectronics and VLSI Design',
    '31': 'Interdisciplinary Centre for Energy Research',
    '32': 'Organic Chemistry',
    '34': 'The Robert Bosch Centre for Cyber-Physical Systems',
    '35': 'System Science & Automation',
    '33': 'UG - Physics',
    '36': 'Molecular Biophysics Unit',
    '37': 'Biochemistry',
    '38': 'UG - Chemistry',
    '39': 'Molecular Reproduction, Development and Genetics',
    '41': 'Communication Networks',
    '40': 'Centre for Atmospheric and Oceanic Sciences',
    '42': 'Centre for Product Design and Manufacturing (CPDM)',
    '43': 'UG - Biology',
    '44': 'Physics',
    # '45': 'Signal Processing',
    '46': 'Interdisciplinary Mathematical Sciences',
    '47': 'Physics (PHY)',
    # '48': 'Centre for Earth Sciences (CEAS)',
    '31': 'Microelectronics',
    '52': 'Computer Science and Automation',
    '53': 'Centre for Ecological Sciences',
    '54': 'Inorganic and Physical Chemistry',
    # '54': 'Materials Research Centre',
    '56': 'Instrumentation and Applied Physics',
    '57': 'Electrical Communication Engineering',
    # '57': 'Department of Management Studies',
    # '58': 'Materials Engineering',
    '60': 'Aerospace Engineering',
    # '60': 'Civil Engineering'
}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/result', methods=['GET'])
def result():
    # Handle GET requests for the result page
    return render_template('result.html')

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        program = request.form['program']
        discipline = request.form['discipline']
        gpa = request.form['gpa']
        skills = request.form.getlist('skills[]')
        courses = request.form.getlist('courses[]')
        # Create a data point from user input
        data_point = create_data_point(program, discipline, gpa, skills, courses)

        # Use the machine learning model to make predictions
        probabilities, salary, top_sec = run_ml_model(data_point)

        # Retrieve the labels for program and discipline
        program_label = PROGRAM_OPTIONS.get(program, 'Unknown Program')
        discipline_label = DISCIPLINE_OPTIONS.get(discipline, 'Unknown Discipline')

        return render_template('result.html', skills=skills, courses=courses, gpa=gpa, program_label=program_label,
                       discipline_label=discipline_label, probabilities=probabilities, max_slot=get_max_slot(probabilities), salary = salary, top_sec=top_sec)
if __name__ == '__main__':
    app.run(debug=True)
