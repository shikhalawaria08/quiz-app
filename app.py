from flask import Flask, render_template, request, flash
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange, Regexp

app = Flask(__name__)
app.secret_key = 'quiz_secret_key'  # For flash and forms

# Simplified option_to_field with less technical language
option_to_field = {
    "Coming up with ad ideas for products": "Marketing",
    "Looking at what customers like and say": "Marketing",
    "Planning brand ideas and content": "Marketing",
    "Setting up events and team-ups": "Marketing",
    "Checking how well ads work with numbers": "Marketing",
    "Handling social media and ads": "Marketing",
    "Doing studies on what people buy": "Marketing",
    "Making posters and promo stuff": "Marketing",
    "Working with online influencers": "Marketing",
    "Making websites show up better in searches": "Marketing",
    "Making friends with customers": "Sales",
    "Talking out deals and agreements": "Sales",
    "Hitting sales goals": "Sales",
    "Showing products to buyers": "Sales",
    "Dealing with customer no's": "Sales",
    "Checking in on potential customers": "Sales",
    "Setting up product shows": "Sales",
    "Keeping track of sales numbers": "Sales",
    "Selling more or extra items": "Sales",
    "Going to business fairs": "Sales",
    "Finding and talking to new hires": "HR",
    "Running training for staff": "HR",
    "Doing check-ins on work performance": "HR",
    "Fixing arguments at work": "HR",
    "Making rules for the company": "HR",
    "Planning fun team activities": "HR",
    "Handling pay and perks": "HR",
    "Encouraging different backgrounds at work": "HR",
    "Talking to people leaving the job": "HR",
    "Helping staff feel good": "HR",
    "Making work faster and better": "Operations",
    "Handling deliveries and supplies": "Operations",
    "Planning when things get done": "Operations",
    "Keeping the right amount of stock": "Operations",
    "Checking for good quality": "Operations",
    "Dealing with suppliers": "Operations",
    "Watching work numbers": "Operations",
    "Adding better ways to do things": "Operations",
    "Teamwork across groups": "Operations",
    "Running daily tasks": "Operations",
    "Making money reports and plans": "Finance",
    "Looking at places to put money": "Finance",
    "Handling money records and checks": "Finance",
    "Guessing future money trends": "Finance",
    "Dealing with taxes": "Finance",
    "Watching money coming in and out": "Finance",
    "Checking for money risks": "Finance",
    "Building money plans": "Finance",
    "Giving tips to save money": "Finance",
    "Tracking costs and earnings": "Finance",
    "Fixing computer problems": "IT",
    "Setting up new software": "IT",
    "Keeping networks safe": "IT",
    "Helping with tech issues": "IT",
    "Making new apps": "IT",
    "Taking care of computers": "IT",
    "Updating systems": "IT",
    "Backing up data": "IT",
    "Adding new tech": "IT",
    "Teaching tech skills": "IT",
    "Planning what products to make": "Product",
    "Asking what users need": "Product",
    "Picking what features to add": "Product",
    "Studying the market": "Product",
    "Working with designers": "Product",
    "Testing new versions": "Product",
    "Releasing new items": "Product",
    "Getting user opinions": "Product",
    "Improving products": "Product",
    "Matching products to company goals": "Product"
}

# Field details remain the same
field_details = {
    "Marketing": {
        "specialization": "Digital Marketing",
        "trending_roles": ["Digital Marketer", "Content Strategist", "SEO Specialist", "Market Research Analyst"],
        "skills_courses": ["SEO Optimization", "Content Creation", "Social Media Marketing", "Google Analytics Certification", "HubSpot Inbound Marketing Course"]
    },
    "Sales": {
        "specialization": "Business Development",
        "trending_roles": ["Outside Sales Representative", "Sales Manager", "Business Development Professional", "Account Executive"],
        "skills_courses": ["Negotiation Skills", "CRM Tools (e.g., Salesforce)", "Lead Generation", "Salesforce Trailhead Courses", "LinkedIn Sales Navigator Training"]
    },
    "HR": {
        "specialization": "Talent Management",
        "trending_roles": ["Workforce Development Manager", "HR Business Partner", "Talent Acquisition Specialist", "Diversity and Inclusion Manager"],
        "skills_courses": ["Recruitment Strategies", "Employee Engagement", "HR Analytics", "SHRM Certification", "Coursera HR Management Course"]
    },
    "Operations": {
        "specialization": "Supply Chain Management",
        "trending_roles": ["Sustainability Specialist", "Operations Manager", "Supply Chain Analyst", "Logistics Coordinator"],
        "skills_courses": ["Process Optimization", "Supply Chain Logistics", "Lean Six Sigma", "APICS Certification", "Coursera Supply Chain Management Specialization"]
    },
    "Finance": {
        "specialization": "Financial Analysis",
        "trending_roles": ["Treasury Manager", "Financial Manager", "Private Equity Analyst", "FinTech Specialist"],
        "skills_courses": ["Financial Modeling", "Risk Assessment", "Budgeting", "CFA Certification", "Coursera Financial Management Course"]
    },
    "IT": {
        "specialization": "AI and Cybersecurity",
        "trending_roles": ["AI Engineer", "Software Developer", "Information Security Analyst", "IT Manager"],
        "skills_courses": ["Python Programming", "AI/ML Fundamentals", "Cybersecurity", "AWS Certification", "Coursera Google IT Support Professional Certificate"]
    },
    "Product": {
        "specialization": "Product Management",
        "trending_roles": ["Chief Growth Officer", "Product Manager", "E-commerce Specialist", "UX/UI Designer"],
        "skills_courses": ["Product Roadmapping", "User Research", "Agile Methodologies", "Product Management Certification (e.g., PMP)", "Coursera Google Product Management Certificate"]
    }
}

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_info = json.loads(os.environ['GOOGLE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)

# Recent submissions to prevent duplicates
recent_submissions = {}

# Define form with validations
class QuizForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, message="Age must be a positive number")])
    contact = StringField('Mobile Number', validators=[DataRequired(), Regexp(r'^\d{10}$', message="Mobile number must be exactly 10 digits")])
    email = StringField('Email', validators=[DataRequired(), Email(message="Invalid email address")])
    profession = StringField('Profession', validators=[DataRequired()])
    experience = IntegerField('Experience (Years)', validators=[DataRequired(), NumberRange(min=0, message="Experience must be a positive whole number")])
    interest_area = StringField('Interest Area', validators=[DataRequired()])
    submit = SubmitField('Submit')

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
    options = list(option_to_field.keys())  # Simplified options

    if request.method == 'POST':
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
                        try:
                            spreadsheet = client.open("Quiz responses")
                            sheet = spreadsheet.worksheet("Quiz Responses")
                            row_data = [
                                name, age, contact, email, profession, experience, interest_area,
                                answers['q1'], answers['q2'], answers['q3'], answers['q4'], answers['q5'],
                                answers['q6'], answers['q7'], answers['q8'], answers['q9'], answers['q10'],
                                recommended_field
                            ]
                            sheet.append_row(row_data)
                            recent_submissions[client_ip] = (current_time, data_hash)
                            flash("Data saved successfully!", "success")
                        except Exception as e:
                            save_error = f"Error saving data: {str(e)}"
                            flash("Error saving data. Please try again.", "danger")
            else:
                try:
                    spreadsheet = client.open("Quiz responses")
                    sheet = spreadsheet.worksheet("Quiz Responses")
                    row_data = [
                        name, age, contact, email, profession, experience, interest_area,
                        answers['q1'], answers['q2'], answers['q3'], answers['q4'], answers['q5'],
                        answers['q6'], answers['q7'], answers['q8'], answers['q9'], answers['q10'],
                        recommended_field
                    ]
                    sheet.append_row(row_data)
                    recent_submissions[client_ip] = (current_time, hash(str(answers)))
                    flash("Data saved successfully!", "success")
                except Exception as e:
                    save_error = f"Error saving data: {str(e)}"
                    flash("Error saving data. Please try again.", "danger")

            return render_template('result.html', name=name, recommended_field=recommended_field, details=details, save_error=save_error)
        else:
            flash("Please correct the errors in the form.", "danger")

    return render_template('quiz_bootstrap.html', form=form, questions=questions, options=options)

if __name__ == '__main__':
    app.run(debug=True)
