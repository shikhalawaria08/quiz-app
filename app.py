from flask import Flask, render_template, request, flash
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'quiz_secret_key'  # Needed for flash messages

# Store recent submissions (simple in-memory check; resets on server restart)
recent_submissions = {}  # {ip_address: (timestamp, data_hash)}

# Mapping from descriptive options to corporate fields (unchanged)
option_to_field = {
    "Creating campaigns to promote products": "Marketing",
    "Analyzing customer trends and feedback": "Marketing",
    "Developing brand strategies and content": "Marketing",
    "Planning events and partnerships": "Marketing",
    "Measuring campaign success with metrics": "Marketing",
    "Managing social media and advertising": "Marketing",
    "Conducting market research studies": "Marketing",
    "Designing promotional materials": "Marketing",
    "Collaborating with influencers": "Marketing",
    "Optimizing SEO and online presence": "Marketing",

    "Building relationships with clients": "Sales",
    "Negotiating deals and contracts": "Sales",
    "Meeting sales targets and quotas": "Sales",
    "Presenting products to potential buyers": "Sales",
    "Handling customer objections": "Sales",
    "Following up on leads": "Sales",
    "Organizing sales demos": "Sales",
    "Tracking sales performance": "Sales",
    "Upselling and cross-selling": "Sales",
    "Attending trade shows": "Sales",

    "Recruiting and interviewing candidates": "HR",
    "Managing employee training programs": "HR",
    "Handling performance reviews": "HR",
    "Resolving workplace conflicts": "HR",
    "Developing company policies": "HR",
    "Organizing team-building activities": "HR",
    "Overseeing payroll and benefits": "HR",
    "Promoting diversity and inclusion": "HR",
    "Conducting exit interviews": "HR",
    "Supporting employee well-being": "HR",

    "Streamlining processes for efficiency": "Operations",
    "Managing supply chain logistics": "Operations",
    "Coordinating project timelines": "Operations",
    "Optimizing inventory levels": "Operations",
    "Ensuring quality control": "Operations",
    "Handling vendor relationships": "Operations",
    "Monitoring operational metrics": "Operations",
    "Implementing process improvements": "Operations",
    "Coordinating cross-team efforts": "Operations",
    "Managing daily workflows": "Operations",

    "Preparing financial reports and budgets": "Finance",
    "Analyzing investment opportunities": "Finance",
    "Managing accounts and audits": "Finance",
    "Forecasting financial trends": "Finance",
    "Handling tax compliance": "Finance",
    "Overseeing cash flow": "Finance",
    "Evaluating financial risks": "Finance",
    "Creating financial models": "Finance",
    "Advising on cost reductions": "Finance",
    "Tracking expenses and revenues": "Finance",

    "Troubleshooting technical issues": "IT",
    "Implementing software solutions": "IT",
    "Managing network security": "IT",
    "Supporting user technology needs": "IT",
    "Developing custom applications": "IT",
    "Maintaining hardware systems": "IT",
    "Conducting system upgrades": "IT",
    "Ensuring data backups": "IT",
    "Integrating new technologies": "IT",
    "Providing IT training": "IT",

    "Defining product roadmaps": "Product",
    "Gathering user requirements": "Product",
    "Prioritizing features for development": "Product",
    "Conducting market analysis": "Product",
    "Collaborating with design teams": "Product",
    "Testing product prototypes": "Product",
    "Launching new products": "Product",
    "Collecting user feedback": "Product",
    "Iterating on product improvements": "Product",
    "Aligning product with business goals": "Product"
}

# Details for each field (unchanged)
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

# Set up Google Sheets client (runs once)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)

@app.route('/', methods=['GET', 'POST'])
def quiz():
    save_error = None
    if request.method == 'POST':
        # Get client IP (simplistic; use with caution in production)
        client_ip = request.remote_addr
        
        # Get form data
        name = request.form['name']
        age = request.form['age']
        contact = request.form['contact']
        email = request.form['email']
        profession = request.form['profession']
        experience = request.form['experience']
        interest_area = request.form['interest_area']
        
        # Collect answers for all 10 questions
        answers = {f'q{i}': request.form.get(f'q{i}') for i in range(1, 11)}
        
        # Count votes for each field based on descriptive options
        fields = ['Marketing', 'Sales', 'HR', 'Operations', 'Finance', 'IT', 'Product']
        votes = {field: 0 for field in fields}
        
        for i in range(1, 11):
            answer = request.form.get(f'q{i}')
            if answer in option_to_field:
                field = option_to_field[answer]
                votes[field] += 1
        
        # Find the field with the most votes
        recommended_field = max(votes, key=votes.get)
        
        # Get details for the recommended field
        details = field_details[recommended_field]
        
        # Check for duplicate submission (within 1 second)
        current_time = time.time()
        if client_ip in recent_submissions:
            last_time, last_hash = recent_submissions[client_ip]
            if current_time - last_time < 1:  # 1-second window
                save_error = "Duplicate submission detected. Data was not saved again."
                print("Duplicate submission skipped.")
            else:
                # Update recent submissions
                data_hash = hash(str(answers))  # Simple hash of answers
                if last_hash == data_hash and current_time - last_time < 5:  # 5-second duplicate check
                    save_error = "Duplicate submission detected. Data was not saved again."
                    print("Duplicate submission skipped.")
                else:
                    # Save to Google Sheets
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
                        print("Data saved to Google Sheets successfully!")
                        recent_submissions[client_ip] = (current_time, data_hash)
                    except gspread.WorksheetNotFound:
                        save_error = "Worksheet 'Quiz Responses' not found. Please ensure the sheet tab is named 'Quiz Responses' exactly."
                    except gspread.exceptions.APIError as api_err:
                        if "storageQuotaExceeded" in str(api_err):
                            save_error = "Storage quota exceeded for service account. Data wasn't saved this time."
                        else:
                            save_error = f"API Error: {api_err}"
                    except Exception as e:
                        save_error = f"Error saving data: {e}"
        else:
            # First submission for this IP
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
                print("Data saved to Google Sheets successfully!")
                recent_submissions[client_ip] = (current_time, hash(str(answers)))
            except gspread.WorksheetNotFound:
                save_error = "Worksheet 'Quiz Responses' not found. Please ensure the sheet tab is named 'Quiz Responses' exactly."
            except gspread.exceptions.APIError as api_err:
                if "storageQuotaExceeded" in str(api_err):
                    save_error = "Storage quota exceeded for service account. Data wasn't saved this time."
                else:
                    save_error = f"API Error: {api_err}"
            except Exception as e:
                save_error = f"Error saving data: {e}"
        
        # Render result page with optional error message
        return render_template('result.html', name=name, recommended_field=recommended_field, details=details, save_error=save_error)
    
    return render_template('quiz_bootstrap.html')

if __name__ == '__main__':
    app.run(debug=True)