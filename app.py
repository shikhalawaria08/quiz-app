from flask import Flask, render_template, request, flash, session
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time
import logging  # Added for logging
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, NumberRange, Regexp
import uuid  # Added for unique submission IDs

app = Flask(__name__)
app.secret_key = 'quiz_secret_key'  # For flash and forms

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Unique options for each question, limited to 10 per question
option_to_field = {
    # Question 1: What do you enjoy most in a work setting?
    "Brainstorming creative campaigns": "Marketing",
    "Building customer relationships": "Sales",
    "Organizing team events": "HR",
    "Optimizing workflows": "Operations",
    "Analyzing financial data": "Finance",
    "Coding new features": "IT",
    "Designing product features": "Product",
    "Collaborating with teams": "Operations",
    "Managing budgets": "Finance",
    "Securing networks": "IT",
    # Question 2: Which task excites you the most?
    "Creating ad visuals": "Marketing",
    "Closing sales deals": "Sales",
    "Recruiting talent": "HR",
    "Managing supply chains": "Operations",
    "Forecasting revenue": "Finance",
    "Debugging software": "IT",
    "Testing product prototypes": "Product",
    "Streamlining processes": "Operations",
    "Investing funds": "Finance",
    "Building apps": "IT",
    # Question 3: What type of work do you find most rewarding?
    "Launching marketing strategies": "Marketing",
    "Negotiating contracts": "Sales",
    "Training employees": "HR",
    "Ensuring quality control": "Operations",
    "Preparing tax reports": "Finance",
    "Setting up servers": "IT",
    "Planning product launches": "Product",
    "Coordinating logistics": "Operations",
    "Assessing risks": "Finance",
    "Updating systems": "IT",
    # Question 4: Which activity aligns with your strengths?
    "Crafting social media posts": "Marketing",
    "Presenting to clients": "Sales",
    "Resolving conflicts": "HR",
    "Scheduling deliveries": "Operations",
    "Balancing books": "Finance",
    "Writing code": "IT",
    "Gathering user feedback": "Product",
    "Monitoring performance": "Operations",
    "Advising on investments": "Finance",
    "Ensuring data security": "IT",
    # Question 5: What do you prefer working on daily?
    "Running ad campaigns": "Marketing",
    "Following up with leads": "Sales",
    "Developing HR policies": "HR",
    "Overseeing inventory": "Operations",
    "Reviewing expenses": "Finance",
    "Maintaining networks": "IT",
    "Defining product goals": "Product",
    "Improving efficiency": "Operations",
    "Creating financial plans": "Finance",
    "Supporting tech users": "IT",
    # Question 6: Which role sounds most appealing to you?
    "Brand strategist": "Marketing",
    "Account manager": "Sales",
    "Talent scout": "HR",
    "Operations coordinator": "Operations",
    "Financial analyst": "Finance",
    "Systems admin": "IT",
    "Product owner": "Product",
    "Supply chain lead": "Operations",
    "Treasury officer": "Finance",
    "Cybersecurity expert": "IT",
    # Question 7: What kind of project would you lead?
    "Marketing event": "Marketing",
    "Sales pitch": "Sales",
    "Employee onboarding": "HR",
    "Process improvement": "Operations",
    "Budget planning": "Finance",
    "Software upgrade": "IT",
    "Product roadmap": "Product",
    "Warehouse setup": "Operations",
    "Investment strategy": "Finance",
    "Network rollout": "IT",
    # Question 8: Which skill do you want to develop?
    "SEO techniques": "Marketing",
    "Sales forecasting": "Sales",
    "Leadership training": "HR",
    "Lean management": "Operations",
    "Financial modeling": "Finance",
    "Python programming": "IT",
    "User experience design": "Product",
    "Vendor negotiation": "Operations",
    "Risk analysis": "Finance",
    "Cloud computing": "IT",
    # Question 9: What motivates your career choices?
    "Creative impact": "Marketing",
    "Earning commissions": "Sales",
    "Team growth": "HR",
    "Operational success": "Operations",
    "Profit growth": "Finance",
    "Tech innovation": "IT",
    "Customer satisfaction": "Product",
    "Resource optimization": "Operations",
    "Wealth creation": "Finance",
    "System reliability": "IT",
    # Question 10: Which task feels most natural to you?
    "Writing content": "Marketing",
    "Building client trust": "Sales",
    "Mediating disputes": "HR",
    "Tracking shipments": "Operations",
    "Auditing accounts": "Finance",
    "Troubleshooting tech": "IT",
    "Iterating products": "Product",
    "Managing deadlines": "Operations",
    "Evaluating investments": "Finance",
    "Securing databases": "IT"
}

# Field details with action plan, growth path, and resources
field_details = {
    "Marketing": {
        "specialization": "Digital Marketing",
        "trending_roles": ["Digital Marketer", "Content Strategist", "SEO Specialist", "Market Research Analyst"],
        "skills_courses": ["SEO Optimization", "Content Creation", "Social Media Marketing", "Google Analytics Certification", "HubSpot Inbound Marketing Course"],
        "action_plan": ["Join a local marketing meetup", "Update your LinkedIn with SEO skills", "Create a portfolio of sample campaigns"],
        "growth_path": ["Junior Marketer", "Marketing Coordinator", "Marketing Manager", "Chief Marketing Officer (CMO)"],
        "resources": ["<a href='https://www.linkedin.com/learning/' target='_blank'>LinkedIn Learning - Marketing</a>", "<a href='https://www.coursera.org/specializations/digital-marketing' target='_blank'>Coursera - Digital Marketing</a>"]
    },
    "Sales": {
        "specialization": "Business Development",
        "trending_roles": ["Outside Sales Representative", "Sales Manager", "Business Development Professional", "Account Executive"],
        "skills_courses": ["Negotiation Skills", "CRM Tools (e.g., Salesforce)", "Lead Generation", "Salesforce Trailhead Courses", "LinkedIn Sales Navigator Training"],
        "action_plan": ["Attend a sales networking event", "Practice a 30-second pitch", "Set up a CRM profile"],
        "growth_path": ["Sales Associate", "Senior Sales Rep", "Sales Manager", "VP of Sales"],
        "resources": ["<a href='https://www.linkedin.com/learning/' target='_blank'>LinkedIn Learning - Sales</a>", "<a href='https://trailhead.salesforce.com/' target='_blank'>Salesforce Trailhead</a>"]
    },
    "HR": {
        "specialization": "Talent Management",
        "trending_roles": ["Workforce Development Manager", "HR Business Partner", "Talent Acquisition Specialist", "Diversity and Inclusion Manager"],
        "skills_courses": ["Recruitment Strategies", "Employee Engagement", "HR Analytics", "SHRM Certification", "Coursera HR Management Course"],
        "action_plan": ["Volunteer for a hiring committee", "Learn HR software (e.g., Workday)", "Network with HR professionals"],
        "growth_path": ["HR Assistant", "HR Generalist", "HR Manager", "CHRO"],
        "resources": ["<a href='https://www.shrm.org/certifications' target='_blank'>SHRM Certification</a>", "<a href='https://www.coursera.org/learn/human-resource-management' target='_blank'>Coursera - HR Management</a>"]
    },
    "Operations": {
        "specialization": "Supply Chain Management",
        "trending_roles": ["Sustainability Specialist", "Operations Manager", "Supply Chain Analyst", "Logistics Coordinator"],
        "skills_courses": ["Process Optimization", "Supply Chain Logistics", "Lean Six Sigma", "APICS Certification", "Coursera Supply Chain Management Specialization"],
        "action_plan": ["Shadow an operations team", "Learn supply chain tools (e.g., SAP)", "Get a logistics certification"],
        "growth_path": ["Operations Coordinator", "Supply Chain Analyst", "Operations Manager", "COO"],
        "resources": ["<a href='https://www.apics.org/credentials-education/credentials/cscp' target='_blank'>APICS CSCP</a>", "<a href='https://www.coursera.org/specializations/supply-chain-management' target='_blank'>Coursera - Supply Chain</a>"]
    },
    "Finance": {
        "specialization": "Financial Analysis",
        "trending_roles": ["Treasury Manager", "Financial Manager", "Private Equity Analyst", "FinTech Specialist"],
        "skills_courses": ["Financial Modeling", "Risk Assessment", "Budgeting", "CFA Certification", "Coursera Financial Management Course"],
        "action_plan": ["Take a budgeting course", "Join a finance forum", "Update resume with financial skills"],
        "growth_path": ["Financial Analyst", "Senior Analyst", "Finance Manager", "CFO"],
        "resources": ["<a href='https://www.cfainstitute.org/en/programs/cfa' target='_blank'>CFA Institute</a>", "<a href='https://www.coursera.org/learn/financial-management' target='_blank'>Coursera - Financial Management</a>"]
    },
    "IT": {
        "specialization": "AI and Cybersecurity",
        "trending_roles": ["AI Engineer", "Software Developer", "Information Security Analyst", "IT Manager"],
        "skills_courses": ["Python Programming", "AI/ML Fundamentals", "Cybersecurity", "AWS Certification", "Coursera Google IT Support Professional Certificate"],
        "action_plan": ["Start a coding project", "Earn an AWS certification", "Join a tech meetup"],
        "growth_path": ["Junior Developer", "Mid-Level Engineer", "Senior Developer", "CTO"],
        "resources": ["<a href='https://aws.amazon.com/certification/' target='_blank'>AWS Certification</a>", "<a href='https://www.coursera.org/professional-certificates/google-it-support' target='_blank'>Coursera - IT Support</a>"]
    },
    "Product": {
        "specialization": "Product Management",
        "trending_roles": ["Chief Growth Officer", "Product Manager", "E-commerce Specialist", "UX/UI Designer"],
        "skills_courses": ["Product Roadmapping", "User Research", "Agile Methodologies", "Product Management Certification (e.g., PMP)", "Coursera Google Product Management Certificate"],
        "action_plan": ["Create a mock product plan", "Learn Agile tools (e.g., Jira)", "Network with PMs"],
        "growth_path": ["Associate PM", "Product Manager", "Senior PM", "Chief Product Officer"],
        "resources": ["<a href='https://www.pmi.org/certifications/project-management-pmp' target='_blank'>PMP Certification</a>", "<a href='https://www.coursera.org/professional-certificates/google-project-management' target='_blank'>Coursera - Product Management</a>"]
    }
}

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open("Quiz responses")

# Setup Analytics worksheet
try:
    analytics_sheet = spreadsheet.worksheet("Analytics")
except gspread.WorksheetNotFound:
    analytics_sheet = spreadsheet.add_worksheet(title="Analytics", rows="1000", cols="10")
    analytics_sheet.append_row(["Timestamp", "Event_Type", "IP", "UTM_Source", "Duration", "Submission_ID", "Details"])

# Recent submissions to prevent duplicates
recent_submissions = {}

def log_event(event_type, ip, utm_source, duration=None, submission_id=None, details=None):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, event_type, ip, utm_source, duration or '', submission_id or '', details or '']
    analytics_sheet.append_row(row)

# Define form with validations
class QuizForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, message="Age must be a positive number")])
    contact = StringField('Mobile Number', validators=[DataRequired(), Regexp(r'^\d{10}$', message="Mobile number must be exactly 10 digits")])
    email = StringField('Email', validators=[DataRequired(), Email(message="Invalid email address")])
    profession = StringField('Profession', validators=[DataRequired()])
    experience = SelectField('No. of Years of Experience', validators=[DataRequired()], choices=[
        ('', 'Select Experience'),
        ('Fresher', 'Fresher'),
        ('less than 1 year', 'less than 1 year'),
        ('1-3 years', '1-3 years'),
        ('3-7 years', '3-7 years'),
        ('7-10 years', '7-10 years'),
        ('more than 10 years', 'more than 10 years')
    ])
    interest_area = StringField('Interest Area', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/log_time', methods=['POST'])
def log_time():
    duration = request.form.get('duration')
    submission_id = session.get('submission_id')
    ip = request.remote_addr
    log_event('time_spent', ip, '', duration, submission_id)
    return 'OK'

@app.route('/log_share', methods=['POST'])
def log_share():
    submission_id = session.get('submission_id')
    ip = request.remote_addr
    log_event('share', ip, '', None, submission_id, 'LinkedIn Share')
    return 'OK'

@app.route('/', methods=['GET', 'POST'])
def quiz():
    form = QuizForm()
    save_error = None
    questions = [
        "What do you enjoy most in a work setting?",
        "Which task excites you the most?",
        "What type of work do you find most rewarding?",
        "Which activity aligns with your strengths?",
        "What do you prefer working on daily?",
        "Which role sounds most appealing to you?",
        "What kind of project would you lead?",
        "Which skill do you want to develop?",
        "What motivates your career choices?",
        "Which task feels most natural to you?"
    ]
    # Dynamic options for each question
    question_options = [
        [opt for opt in option_to_field.keys() if "Question 1" in opt or opt in [
            "Brainstorming creative campaigns", "Building customer relationships", "Organizing team events",
            "Optimizing workflows", "Analyzing financial data", "Coding new features", "Designing product features",
            "Collaborating with teams", "Managing budgets", "Securing networks"]],
        [opt for opt in option_to_field.keys() if "Question 2" in opt or opt in [
            "Creating ad visuals", "Closing sales deals", "Recruiting talent", "Managing supply chains",
            "Forecasting revenue", "Debugging software", "Testing product prototypes", "Streamlining processes",
            "Investing funds", "Building apps"]],
        [opt for opt in option_to_field.keys() if "Question 3" in opt or opt in [
            "Launching marketing strategies", "Negotiating contracts", "Training employees",
            "Ensuring quality control", "Preparing tax reports", "Setting up servers", "Planning product launches",
            "Coordinating logistics", "Assessing risks", "Updating systems"]],
        [opt for opt in option_to_field.keys() if "Question 4" in opt or opt in [
            "Crafting social media posts", "Presenting to clients", "Resolving conflicts", "Scheduling deliveries",
            "Balancing books", "Writing code", "Gathering user feedback", "Monitoring performance",
            "Advising on investments", "Ensuring data security"]],
        [opt for opt in option_to_field.keys() if "Question 5" in opt or opt in [
            "Running ad campaigns", "Following up with leads", "Developing HR policies", "Overseeing inventory",
            "Reviewing expenses", "Maintaining networks", "Defining product goals", "Improving efficiency",
            "Creating financial plans", "Supporting tech users"]],
        [opt for opt in option_to_field.keys() if "Question 6" in opt or opt in [
            "Brand strategist", "Account manager", "Talent scout", "Operations coordinator",
            "Financial analyst", "Systems admin", "Product owner", "Supply chain lead",
            "Treasury officer", "Cybersecurity expert"]],
        [opt for opt in option_to_field.keys() if "Question 7" in opt or opt in [
            "Marketing event", "Sales pitch", "Employee onboarding", "Process improvement",
            "Budget planning", "Software upgrade", "Product roadmap", "Warehouse setup",
            "Investment strategy", "Network rollout"]],
        [opt for opt in option_to_field.keys() if "Question 8" in opt or opt in [
            "SEO techniques", "Sales forecasting", "Leadership training", "Lean management",
            "Financial modeling", "Python programming", "User experience design", "Vendor negotiation",
            "Risk analysis", "Cloud computing"]],
        [opt for opt in option_to_field.keys() if "Question 9" in opt or opt in [
            "Creative impact", "Earning commissions", "Team growth", "Operational success",
            "Profit growth", "Tech innovation", "Customer satisfaction", "Resource optimization",
            "Wealth creation", "System reliability"]],
        [opt for opt in option_to_field.keys() if "Question 10" in opt or opt in [
            "Writing content", "Building client trust", "Mediating disputes", "Tracking shipments",
            "Auditing accounts", "Troubleshooting tech", "Iterating products", "Managing deadlines",
            "Evaluating investments", "Securing databases"]]
    ]

    # Log visit on GET request
    if request.method == 'GET':
        utm_source = request.args.get('utm_source', 'direct')
        log_event('visit', request.remote_addr, utm_source)

    if request.method == 'POST':
        try:
            if form.validate_on_submit():
                client_ip = request.remote_addr
                name = form.name.data
                age = form.age.data
                contact = form.contact.data
                email = form.email.data
                profession = form.profession.data
                experience = form.experience.data
                interest_area = form.interest_area.data
                answers = {f'q{i}': request.form.get(f'q{i}') for i in range(1, 11)}

                fields = ['Marketing', 'Sales', 'HR', 'Operations', 'Finance', 'IT', 'Product']
                votes = {field: 0 for field in fields}
                for i in range(1, 11):
                    answer = answers.get(f'q{i}')
                    if answer in option_to_field:
                        votes[option_to_field[answer]] += 1

                recommended_field = max(votes, key=votes.get)
                details = field_details[recommended_field]
                current_time = time.time()
                submission_id = str(uuid.uuid4())  # Generate unique ID for this submission

                # Duplicate check
                if client_ip in recent_submissions:
                    last_time, last_hash = recent_submissions[client_ip]
                    if current_time - last_time < 1:
                        save_error = "Duplicate submission detected. Data was not saved again."
                    else:
                        data_hash = hash(str(answers))
                        if last_hash == data_hash and current_time - last_time < 5:
                            save_error = "Duplicate submission detected. Data was not saved again."
                        else:
                            sheet = spreadsheet.worksheet("Quiz Responses")
                            row_data = [
                                name, age, contact, email, profession, experience, interest_area,
                                answers['q1'], answers['q2'], answers['q3'], answers['q4'], answers['q5'],
                                answers['q6'], answers['q7'], answers['q8'], answers['q9'], answers['q10'],
                                recommended_field,  # Added
                                details['specialization'],  # Added
                                ', '.join(details['skills_courses']),  # Added
                                ', '.join(details['action_plan']),  # Added
                                ' → '.join(details['growth_path'])  # Added
                            ]
                            sheet.append_row(row_data)
                            recent_submissions[client_ip] = (current_time, data_hash)
                            # Log submission
                            log_event('submission', client_ip, 'quiz', None, submission_id)
                            session['submission_id'] = submission_id
                            flash("Data saved successfully!", "success")
                else:
                    sheet = spreadsheet.worksheet("Quiz Responses")
                    row_data = [
                        name, age, contact, email, profession, experience, interest_area,
                        answers['q1'], answers['q2'], answers['q3'], answers['q4'], answers['q5'],
                        answers['q6'], answers['q7'], answers['q8'], answers['q9'], answers['q10'],
                        recommended_field,  # Added
                        details['specialization'],  # Added
                        ', '.join(details['skills_courses']),  # Added
                        ', '.join(details['action_plan']),  # Added
                        ' → '.join(details['growth_path'])  # Added
                    ]
                    sheet.append_row(row_data)
                    recent_submissions[client_ip] = (current_time, hash(str(answers)))
                    # Log submission
                    log_event('submission', client_ip, 'quiz', None, submission_id)
                    session['submission_id'] = submission_id
                    flash("Data saved successfully!", "success")

                # Clear session on successful submission except submission_id
                # session.clear()  # Commented to keep submission_id for tracking
                url = request.url_root
                share_message = f"I just discovered my ideal career path with this amazing quiz! Turns out I'm a {recommended_field} expert. What's yours? Take the quiz now: {url} and unlock your potential! #CareerDiscovery"
                return render_template('result.html', name=name, recommended_field=recommended_field, details=details, save_error=save_error, submission_id=submission_id, url=url, share_message=share_message)
            else:
                # Store form data in session on validation failure
                session['name'] = form.name.data
                session['age'] = form.age.data
                session['contact'] = form.contact.data
                session['email'] = form.email.data
                session['profession'] = form.profession.data
                session['experience'] = form.experience.data
                session['interest_area'] = form.interest_area.data
                for i in range(1, 11):
                    session[f'q{i}'] = request.form.get(f'q{i}')
                flash("Please correct the errors in the form.", "danger")
        except Exception as e:
            logger.error(f"Error in quiz route: {str(e)}")
            flash("An error occurred while processing your quiz. Please try again.", "danger")
            # Store form data in session on exception
            session['name'] = form.name.data
            session['age'] = form.age.data
            session['contact'] = form.contact.data
            session['email'] = form.email.data
            session['profession'] = form.profession.data
            session['experience'] = form.experience.data
            session['interest_area'] = form.interest_area.data
            for i in range(1, 11):
                session[f'q{i}'] = request.form.get(f'q{i}')
            return render_template('quiz_bootstrap.html', form=form, questions=questions, question_options=question_options)

    # Pre-fill form from session on GET or failed POST
    form.name.data = session.get('name', '')
    form.age.data = session.get('age', '')
    form.contact.data = session.get('contact', '')
    form.email.data = session.get('email', '')
    form.profession.data = session.get('profession', '')
    form.experience.data = session.get('experience', '')
    form.interest_area.data = session.get('interest_area', '')

    return render_template('quiz_bootstrap.html', form=form, questions=questions, question_options=question_options)

if __name__ == '__main__':
    app.run(debug=True)
