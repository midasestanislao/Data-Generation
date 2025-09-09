import streamlit as st
import pandas as pd
import random
import json
import hashlib
from datetime import datetime
import io
import traceback

# Try to import pyperclip for clipboard functionality
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Try to import xlsxwriter, but don't fail if it's not available
try:
    import xlsxwriter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    
# Try openpyxl as alternative
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Test Persona Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal professional CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    h1 {
        color: #1f2937;
        font-weight: 500;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }
    .stButton>button {
        background-color: #4b5563;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #374151;
    }
    .metric-row {
        background-color: #f9fafb;
        padding: 1rem;
        border-radius: 0.25rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

class PersonaGenerator:
    """Generate test personas with public place addresses and guaranteed uniqueness"""
    
    def __init__(self):
        # Extended name lists for better variety
        self.first_names = {
            'male': ['James', 'John', 'Robert', 'Michael', 'William', 'David', 
                     'Richard', 'Joseph', 'Thomas', 'Christopher', 'Daniel', 'Matthew',
                     'Anthony', 'Mark', 'Donald', 'Kenneth', 'Steven', 'Edward',
                     'Brian', 'Ronald', 'Kevin', 'Jason', 'Jeffrey', 'Ryan',
                     'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen',
                     'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin', 'Samuel',
                     'Frank', 'Gregory', 'Raymond', 'Alexander', 'Patrick', 'Jack'],
            'female': ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara',
                      'Susan', 'Jessica', 'Sarah', 'Karen', 'Nancy', 'Margaret',
                      'Lisa', 'Betty', 'Dorothy', 'Sandra', 'Ashley', 'Kimberly',
                      'Donna', 'Emily', 'Michelle', 'Carol', 'Amanda', 'Melissa',
                      'Deborah', 'Stephanie', 'Rebecca', 'Laura', 'Sharon', 'Cynthia',
                      'Kathleen', 'Amy', 'Shirley', 'Angela', 'Helen', 'Anna',
                      'Brenda', 'Pamela', 'Nicole', 'Emma', 'Samantha', 'Katherine']
        }
        
        self.last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
                           'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez',
                           'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore',
                           'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
                           'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
                           'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott',
                           'Torres', 'Nguyen', 'Hill', 'Flores', 'Green', 'Adams',
                           'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell']
        
        # Duplicate tracking with multiple strategies
        self.unique_tracker = {
            'full_names': set(),
            'emails': set(),
            'phones': set(),
            'addresses': set(),
            'name_hashes': set(),
            'person_hashes': set()
        }
        
        # Statistics tracking
        self.generation_stats = {
            'collision_attempts': 0,
            'unique_regenerations': 0,
            'total_generated': 0
        }
        
        # All 50 US States with public places
        self.public_places = {
            'Alabama': [
                {'name': 'Birmingham Public Library', 'address': '2100 Park Place', 'city': 'Birmingham', 'zip': '35203'},
                {'name': 'Montgomery City Hall', 'address': '103 N Perry St', 'city': 'Montgomery', 'zip': '36104'},
                {'name': 'Railroad Park', 'address': '1600 1st Ave S', 'city': 'Birmingham', 'zip': '35233'},
                {'name': 'Mobile Public Library', 'address': '701 Government St', 'city': 'Mobile', 'zip': '36602'},
                {'name': 'Huntsville Public Library', 'address': '915 Monroe St SW', 'city': 'Huntsville', 'zip': '35801'},
            ],
            'Alaska': [
                {'name': 'Anchorage Public Library', 'address': '3600 Denali St', 'city': 'Anchorage', 'zip': '99503'},
                {'name': 'Alaska State Capitol', 'address': '120 4th St', 'city': 'Juneau', 'zip': '99801'},
                {'name': 'Fairbanks Public Library', 'address': '1215 Cowles St', 'city': 'Fairbanks', 'zip': '99701'},
                {'name': 'Town Square Park', 'address': '540 W 5th Ave', 'city': 'Anchorage', 'zip': '99501'},
                {'name': 'Juneau Public Library', 'address': '292 Marine Way', 'city': 'Juneau', 'zip': '99801'},
            ],
            'Arizona': [
                {'name': 'Phoenix Public Library', 'address': '1221 N Central Ave', 'city': 'Phoenix', 'zip': '85004'},
                {'name': 'Arizona State Capitol', 'address': '1700 W Washington St', 'city': 'Phoenix', 'zip': '85007'},
                {'name': 'Tucson City Hall', 'address': '255 W Alameda St', 'city': 'Tucson', 'zip': '85701'},
                {'name': 'Scottsdale Public Library', 'address': '3839 N Drinkwater Blvd', 'city': 'Scottsdale', 'zip': '85251'},
                {'name': 'Mesa Public Library', 'address': '64 E 1st St', 'city': 'Mesa', 'zip': '85201'},
            ],
            'Arkansas': [
                {'name': 'Little Rock Central Library', 'address': '100 Rock St', 'city': 'Little Rock', 'zip': '72201'},
                {'name': 'Arkansas State Capitol', 'address': '500 Woodlane St', 'city': 'Little Rock', 'zip': '72201'},
                {'name': 'Riverfront Park', 'address': '400 President Clinton Ave', 'city': 'Little Rock', 'zip': '72201'},
                {'name': 'Fayetteville Public Library', 'address': '401 W Mountain St', 'city': 'Fayetteville', 'zip': '72701'},
                {'name': 'Fort Smith Public Library', 'address': '3201 Rogers Ave', 'city': 'Fort Smith', 'zip': '72903'},
            ],
            'California': [
                {'name': 'Los Angeles Central Library', 'address': '630 W 5th St', 'city': 'Los Angeles', 'zip': '90071'},
                {'name': 'San Francisco Public Library', 'address': '100 Larkin St', 'city': 'San Francisco', 'zip': '94102'},
                {'name': 'Golden Gate Park', 'address': '501 Stanyan St', 'city': 'San Francisco', 'zip': '94117'},
                {'name': 'San Diego Central Library', 'address': '330 Park Blvd', 'city': 'San Diego', 'zip': '92101'},
                {'name': 'California State Capitol', 'address': '1315 10th St', 'city': 'Sacramento', 'zip': '95814'},
            ],
            'Colorado': [
                {'name': 'Denver Public Library', 'address': '10 W 14th Ave Pkwy', 'city': 'Denver', 'zip': '80204'},
                {'name': 'Denver Botanic Gardens', 'address': '1007 York St', 'city': 'Denver', 'zip': '80206'},
                {'name': 'Boulder Public Library', 'address': '1001 Arapahoe Ave', 'city': 'Boulder', 'zip': '80302'},
                {'name': 'Colorado State Capitol', 'address': '200 E Colfax Ave', 'city': 'Denver', 'zip': '80203'},
                {'name': 'Pikes Peak Library', 'address': '20 N Cascade Ave', 'city': 'Colorado Springs', 'zip': '80903'},
            ],
            'Connecticut': [
                {'name': 'Hartford Public Library', 'address': '500 Main St', 'city': 'Hartford', 'zip': '06103'},
                {'name': 'Connecticut State Capitol', 'address': '210 Capitol Ave', 'city': 'Hartford', 'zip': '06106'},
                {'name': 'New Haven Free Library', 'address': '133 Elm St', 'city': 'New Haven', 'zip': '06510'},
                {'name': 'Bushnell Park', 'address': '1 Jewell St', 'city': 'Hartford', 'zip': '06103'},
                {'name': 'Stamford Public Library', 'address': '1 Public Library Plaza', 'city': 'Stamford', 'zip': '06904'},
            ],
            'Delaware': [
                {'name': 'Wilmington Library', 'address': '10 E 10th St', 'city': 'Wilmington', 'zip': '19801'},
                {'name': 'Delaware Legislative Hall', 'address': '411 Legislative Ave', 'city': 'Dover', 'zip': '19901'},
                {'name': 'Brandywine Park', 'address': '1080 N Park Dr', 'city': 'Wilmington', 'zip': '19802'},
                {'name': 'Dover Public Library', 'address': '35 E Loockerman St', 'city': 'Dover', 'zip': '19901'},
                {'name': 'Newark Free Library', 'address': '750 Library Ave', 'city': 'Newark', 'zip': '19711'},
            ],
            'Florida': [
                {'name': 'Miami-Dade Public Library', 'address': '101 W Flagler St', 'city': 'Miami', 'zip': '33130'},
                {'name': 'Orlando Public Library', 'address': '101 E Central Blvd', 'city': 'Orlando', 'zip': '32801'},
                {'name': 'Tampa-Hillsborough Library', 'address': '900 N Ashley Dr', 'city': 'Tampa', 'zip': '33602'},
                {'name': 'Jacksonville Public Library', 'address': '303 N Laura St', 'city': 'Jacksonville', 'zip': '32202'},
                {'name': 'Lake Eola Park', 'address': '512 E Washington St', 'city': 'Orlando', 'zip': '32801'},
            ],
            'Georgia': [
                {'name': 'Atlanta-Fulton Library', 'address': '1 Margaret Mitchell Square', 'city': 'Atlanta', 'zip': '30303'},
                {'name': 'Piedmont Park', 'address': '1320 Monroe Dr NE', 'city': 'Atlanta', 'zip': '30306'},
                {'name': 'Georgia State Capitol', 'address': '206 Washington St SW', 'city': 'Atlanta', 'zip': '30334'},
                {'name': 'Savannah Public Library', 'address': '2002 Bull St', 'city': 'Savannah', 'zip': '31401'},
                {'name': 'Columbus Public Library', 'address': '3000 Macon Rd', 'city': 'Columbus', 'zip': '31906'},
            ],
            'Hawaii': [
                {'name': 'Hawaii State Library', 'address': '478 S King St', 'city': 'Honolulu', 'zip': '96813'},
                {'name': 'Hawaii State Capitol', 'address': '415 S Beretania St', 'city': 'Honolulu', 'zip': '96813'},
                {'name': 'Kapiolani Park', 'address': '3840 Paki Ave', 'city': 'Honolulu', 'zip': '96815'},
                {'name': 'Maui Public Library', 'address': '251 S High St', 'city': 'Wailuku', 'zip': '96793'},
                {'name': 'Hilo Public Library', 'address': '300 Waianuenue Ave', 'city': 'Hilo', 'zip': '96720'},
            ],
            'Idaho': [
                {'name': 'Boise Public Library', 'address': '715 S Capitol Blvd', 'city': 'Boise', 'zip': '83702'},
                {'name': 'Idaho State Capitol', 'address': '700 W Jefferson St', 'city': 'Boise', 'zip': '83720'},
                {'name': 'Julia Davis Park', 'address': '700 S Capitol Blvd', 'city': 'Boise', 'zip': '83702'},
                {'name': 'Coeur d\'Alene Library', 'address': '702 E Front Ave', 'city': 'Coeur d\'Alene', 'zip': '83814'},
                {'name': 'Idaho Falls Library', 'address': '457 W Broadway St', 'city': 'Idaho Falls', 'zip': '83402'},
            ],
            'Illinois': [
                {'name': 'Chicago Public Library', 'address': '400 S State St', 'city': 'Chicago', 'zip': '60605'},
                {'name': 'Millennium Park', 'address': '201 E Randolph St', 'city': 'Chicago', 'zip': '60602'},
                {'name': 'Illinois State Capitol', 'address': '401 S 2nd St', 'city': 'Springfield', 'zip': '62701'},
                {'name': 'Grant Park', 'address': '337 E Randolph St', 'city': 'Chicago', 'zip': '60601'},
                {'name': 'Navy Pier', 'address': '600 E Grand Ave', 'city': 'Chicago', 'zip': '60611'},
            ],
            'Indiana': [
                {'name': 'Indianapolis Public Library', 'address': '40 E St Clair St', 'city': 'Indianapolis', 'zip': '46204'},
                {'name': 'Indiana State Capitol', 'address': '200 W Washington St', 'city': 'Indianapolis', 'zip': '46204'},
                {'name': 'White River State Park', 'address': '801 W Washington St', 'city': 'Indianapolis', 'zip': '46204'},
                {'name': 'Fort Wayne Library', 'address': '900 Library Plaza', 'city': 'Fort Wayne', 'zip': '46802'},
                {'name': 'Evansville Public Library', 'address': '200 SE Martin Luther King Jr Blvd', 'city': 'Evansville', 'zip': '47713'},
            ],
            'Iowa': [
                {'name': 'Des Moines Public Library', 'address': '1000 Grand Ave', 'city': 'Des Moines', 'zip': '50309'},
                {'name': 'Iowa State Capitol', 'address': '1007 E Grand Ave', 'city': 'Des Moines', 'zip': '50319'},
                {'name': 'Gray\'s Lake Park', 'address': '2101 Fleur Dr', 'city': 'Des Moines', 'zip': '50321'},
                {'name': 'Cedar Rapids Library', 'address': '450 5th Ave SE', 'city': 'Cedar Rapids', 'zip': '52401'},
                {'name': 'Davenport Public Library', 'address': '321 Main St', 'city': 'Davenport', 'zip': '52801'},
            ],
            'Kansas': [
                {'name': 'Wichita Public Library', 'address': '223 S Main St', 'city': 'Wichita', 'zip': '67202'},
                {'name': 'Kansas State Capitol', 'address': '300 SW 10th Ave', 'city': 'Topeka', 'zip': '66612'},
                {'name': 'Topeka Public Library', 'address': '1515 SW 10th Ave', 'city': 'Topeka', 'zip': '66604'},
                {'name': 'Kansas City Library', 'address': '625 Minnesota Ave', 'city': 'Kansas City', 'zip': '66101'},
                {'name': 'Lawrence Public Library', 'address': '707 Vermont St', 'city': 'Lawrence', 'zip': '66044'},
            ],
            'Kentucky': [
                {'name': 'Louisville Free Library', 'address': '301 York St', 'city': 'Louisville', 'zip': '40203'},
                {'name': 'Kentucky State Capitol', 'address': '700 Capitol Ave', 'city': 'Frankfort', 'zip': '40601'},
                {'name': 'Cherokee Park', 'address': '745 Cochran Hill Rd', 'city': 'Louisville', 'zip': '40206'},
                {'name': 'Lexington Public Library', 'address': '140 E Main St', 'city': 'Lexington', 'zip': '40507'},
                {'name': 'Bowling Green Library', 'address': '1225 State St', 'city': 'Bowling Green', 'zip': '42101'},
            ],
            'Louisiana': [
                {'name': 'New Orleans Public Library', 'address': '219 Loyola Ave', 'city': 'New Orleans', 'zip': '70112'},
                {'name': 'Louisiana State Capitol', 'address': '900 N 3rd St', 'city': 'Baton Rouge', 'zip': '70802'},
                {'name': 'City Park', 'address': '1 Palm Dr', 'city': 'New Orleans', 'zip': '70124'},
                {'name': 'Baton Rouge Library', 'address': '7711 Goodwood Blvd', 'city': 'Baton Rouge', 'zip': '70806'},
                {'name': 'Lafayette Public Library', 'address': '301 W Congress St', 'city': 'Lafayette', 'zip': '70501'},
            ],
            'Maine': [
                {'name': 'Portland Public Library', 'address': '5 Monument Square', 'city': 'Portland', 'zip': '04101'},
                {'name': 'Maine State House', 'address': '2 State House Station', 'city': 'Augusta', 'zip': '04333'},
                {'name': 'Deering Oaks Park', 'address': '20 Deering Ave', 'city': 'Portland', 'zip': '04102'},
                {'name': 'Bangor Public Library', 'address': '145 Harlow St', 'city': 'Bangor', 'zip': '04401'},
                {'name': 'Lewiston Public Library', 'address': '200 Lisbon St', 'city': 'Lewiston', 'zip': '04240'},
            ],
            'Maryland': [
                {'name': 'Enoch Pratt Library', 'address': '400 Cathedral St', 'city': 'Baltimore', 'zip': '21201'},
                {'name': 'Maryland State House', 'address': '100 State Cir', 'city': 'Annapolis', 'zip': '21401'},
                {'name': 'Inner Harbor', 'address': '401 Light St', 'city': 'Baltimore', 'zip': '21202'},
                {'name': 'Rockville Library', 'address': '21 Maryland Ave', 'city': 'Rockville', 'zip': '20850'},
                {'name': 'Silver Spring Library', 'address': '900 Wayne Ave', 'city': 'Silver Spring', 'zip': '20910'},
            ],
            'Massachusetts': [
                {'name': 'Boston Public Library', 'address': '700 Boylston St', 'city': 'Boston', 'zip': '02116'},
                {'name': 'Boston Common', 'address': '139 Tremont St', 'city': 'Boston', 'zip': '02111'},
                {'name': 'Massachusetts State House', 'address': '24 Beacon St', 'city': 'Boston', 'zip': '02133'},
                {'name': 'Cambridge Public Library', 'address': '449 Broadway', 'city': 'Cambridge', 'zip': '02138'},
                {'name': 'Worcester Public Library', 'address': '3 Salem Square', 'city': 'Worcester', 'zip': '01608'},
            ],
            'Michigan': [
                {'name': 'Detroit Public Library', 'address': '5201 Woodward Ave', 'city': 'Detroit', 'zip': '48202'},
                {'name': 'Michigan State Capitol', 'address': '100 N Capitol Ave', 'city': 'Lansing', 'zip': '48933'},
                {'name': 'Belle Isle Park', 'address': '2 Inselruhe Ave', 'city': 'Detroit', 'zip': '48207'},
                {'name': 'Grand Rapids Library', 'address': '111 Library St NE', 'city': 'Grand Rapids', 'zip': '49503'},
                {'name': 'Ann Arbor Library', 'address': '343 S 5th Ave', 'city': 'Ann Arbor', 'zip': '48104'},
            ],
            'Minnesota': [
                {'name': 'Minneapolis Central Library', 'address': '300 Nicollet Mall', 'city': 'Minneapolis', 'zip': '55401'},
                {'name': 'Minnesota State Capitol', 'address': '75 Rev Dr Martin Luther King Jr Blvd', 'city': 'St Paul', 'zip': '55155'},
                {'name': 'Lake Harriet Park', 'address': '4135 W Lake Harriet Pkwy', 'city': 'Minneapolis', 'zip': '55409'},
                {'name': 'St Paul Public Library', 'address': '90 W 4th St', 'city': 'St Paul', 'zip': '55102'},
                {'name': 'Duluth Public Library', 'address': '520 W Superior St', 'city': 'Duluth', 'zip': '55802'},
            ],
            'Mississippi': [
                {'name': 'Jackson Library', 'address': '300 N State St', 'city': 'Jackson', 'zip': '39201'},
                {'name': 'Mississippi State Capitol', 'address': '400 High St', 'city': 'Jackson', 'zip': '39201'},
                {'name': 'LeFleur\'s Bluff State Park', 'address': '2140 Riverside Dr', 'city': 'Jackson', 'zip': '39202'},
                {'name': 'Gulfport Library', 'address': '1708 25th Ave', 'city': 'Gulfport', 'zip': '39501'},
                {'name': 'Biloxi Public Library', 'address': '580 Howard Ave', 'city': 'Biloxi', 'zip': '39530'},
            ],
            'Missouri': [
                {'name': 'Kansas City Public Library', 'address': '14 W 10th St', 'city': 'Kansas City', 'zip': '64105'},
                {'name': 'Missouri State Capitol', 'address': '201 W Capitol Ave', 'city': 'Jefferson City', 'zip': '65101'},
                {'name': 'Forest Park', 'address': '5595 Grand Dr', 'city': 'St Louis', 'zip': '63112'},
                {'name': 'St Louis Public Library', 'address': '1301 Olive St', 'city': 'St Louis', 'zip': '63103'},
                {'name': 'Springfield Library', 'address': '4653 S Campbell Ave', 'city': 'Springfield', 'zip': '65810'},
            ],
            'Montana': [
                {'name': 'Billings Public Library', 'address': '510 N Broadway', 'city': 'Billings', 'zip': '59101'},
                {'name': 'Montana State Capitol', 'address': '1301 E 6th Ave', 'city': 'Helena', 'zip': '59601'},
                {'name': 'Pioneer Park', 'address': '401 Parkhill Dr', 'city': 'Billings', 'zip': '59101'},
                {'name': 'Missoula Public Library', 'address': '301 E Main St', 'city': 'Missoula', 'zip': '59802'},
                {'name': 'Great Falls Library', 'address': '301 2nd Ave N', 'city': 'Great Falls', 'zip': '59401'},
            ],
            'Nebraska': [
                {'name': 'Omaha Public Library', 'address': '215 S 15th St', 'city': 'Omaha', 'zip': '68102'},
                {'name': 'Nebraska State Capitol', 'address': '1445 K St', 'city': 'Lincoln', 'zip': '68509'},
                {'name': 'Memorial Park', 'address': '6005 Underwood Ave', 'city': 'Omaha', 'zip': '68132'},
                {'name': 'Lincoln City Libraries', 'address': '136 S 14th St', 'city': 'Lincoln', 'zip': '68508'},
                {'name': 'Grand Island Library', 'address': '211 N Washington St', 'city': 'Grand Island', 'zip': '68801'},
            ],
            'Nevada': [
                {'name': 'Las Vegas Library', 'address': '833 Las Vegas Blvd N', 'city': 'Las Vegas', 'zip': '89101'},
                {'name': 'Nevada State Capitol', 'address': '101 N Carson St', 'city': 'Carson City', 'zip': '89701'},
                {'name': 'Sunset Park', 'address': '2601 E Sunset Rd', 'city': 'Las Vegas', 'zip': '89120'},
                {'name': 'Reno Library', 'address': '301 S Center St', 'city': 'Reno', 'zip': '89501'},
                {'name': 'Henderson Libraries', 'address': '280 S Green Valley Pkwy', 'city': 'Henderson', 'zip': '89012'},
            ],
            'New Hampshire': [
                {'name': 'Manchester City Library', 'address': '405 Pine St', 'city': 'Manchester', 'zip': '03104'},
                {'name': 'New Hampshire State House', 'address': '107 N Main St', 'city': 'Concord', 'zip': '03301'},
                {'name': 'White Park', 'address': '125 White St', 'city': 'Concord', 'zip': '03301'},
                {'name': 'Nashua Public Library', 'address': '2 Court St', 'city': 'Nashua', 'zip': '03060'},
                {'name': 'Portsmouth Library', 'address': '175 Parrott Ave', 'city': 'Portsmouth', 'zip': '03801'},
            ],
            'New Jersey': [
                {'name': 'Newark Public Library', 'address': '5 Washington St', 'city': 'Newark', 'zip': '07101'},
                {'name': 'New Jersey State House', 'address': '125 W State St', 'city': 'Trenton', 'zip': '08608'},
                {'name': 'Liberty State Park', 'address': '1 Audrey Zapp Dr', 'city': 'Jersey City', 'zip': '07305'},
                {'name': 'Jersey City Library', 'address': '472 Jersey Ave', 'city': 'Jersey City', 'zip': '07302'},
                {'name': 'Camden County Library', 'address': '203 Laurel Rd', 'city': 'Voorhees', 'zip': '08043'},
            ],
            'New Mexico': [
                {'name': 'Albuquerque Library', 'address': '501 Copper Ave NW', 'city': 'Albuquerque', 'zip': '87102'},
                {'name': 'New Mexico State Capitol', 'address': '490 Old Santa Fe Trail', 'city': 'Santa Fe', 'zip': '87501'},
                {'name': 'Roosevelt Park', 'address': '500 Spruce St SE', 'city': 'Albuquerque', 'zip': '87106'},
                {'name': 'Santa Fe Public Library', 'address': '145 Washington Ave', 'city': 'Santa Fe', 'zip': '87501'},
                {'name': 'Las Cruces Library', 'address': '200 E Picacho Ave', 'city': 'Las Cruces', 'zip': '88001'},
            ],
            'New York': [
                {'name': 'New York Public Library', 'address': '476 5th Ave', 'city': 'New York', 'zip': '10018'},
                {'name': 'Central Park', 'address': '59th to 110th St', 'city': 'New York', 'zip': '10022'},
                {'name': 'Brooklyn Public Library', 'address': '10 Grand Army Plaza', 'city': 'Brooklyn', 'zip': '11238'},
                {'name': 'Buffalo Central Library', 'address': '1 Lafayette Square', 'city': 'Buffalo', 'zip': '14203'},
                {'name': 'Albany Public Library', 'address': '161 Washington Ave', 'city': 'Albany', 'zip': '12210'},
            ],
            'North Carolina': [
                {'name': 'Charlotte Library', 'address': '310 N Tryon St', 'city': 'Charlotte', 'zip': '28202'},
                {'name': 'North Carolina State Capitol', 'address': '1 E Edenton St', 'city': 'Raleigh', 'zip': '27601'},
                {'name': 'Freedom Park', 'address': '1900 East Blvd', 'city': 'Charlotte', 'zip': '28203'},
                {'name': 'Wake County Library', 'address': '4020 Carya Dr', 'city': 'Raleigh', 'zip': '27610'},
                {'name': 'Durham County Library', 'address': '300 N Roxboro St', 'city': 'Durham', 'zip': '27701'},
            ],
            'North Dakota': [
                {'name': 'Bismarck Library', 'address': '515 N 5th St', 'city': 'Bismarck', 'zip': '58501'},
                {'name': 'North Dakota State Capitol', 'address': '600 E Boulevard Ave', 'city': 'Bismarck', 'zip': '58505'},
                {'name': 'Sertoma Park', 'address': '2400 Longspur Trail', 'city': 'Bismarck', 'zip': '58504'},
                {'name': 'Fargo Public Library', 'address': '102 3rd St N', 'city': 'Fargo', 'zip': '58102'},
                {'name': 'Grand Forks Library', 'address': '2110 Library Cir', 'city': 'Grand Forks', 'zip': '58201'},
            ],
            'Ohio': [
                {'name': 'Columbus Library', 'address': '96 S Grant Ave', 'city': 'Columbus', 'zip': '43215'},
                {'name': 'Ohio Statehouse', 'address': '1 Capitol Square', 'city': 'Columbus', 'zip': '43215'},
                {'name': 'Goodale Park', 'address': '120 W Goodale St', 'city': 'Columbus', 'zip': '43215'},
                {'name': 'Cleveland Public Library', 'address': '325 Superior Ave E', 'city': 'Cleveland', 'zip': '44114'},
                {'name': 'Cincinnati Library', 'address': '800 Vine St', 'city': 'Cincinnati', 'zip': '45202'},
            ],
            'Oklahoma': [
                {'name': 'Metropolitan Library', 'address': '300 Park Ave', 'city': 'Oklahoma City', 'zip': '73102'},
                {'name': 'Oklahoma State Capitol', 'address': '2300 N Lincoln Blvd', 'city': 'Oklahoma City', 'zip': '73105'},
                {'name': 'Scissortail Park', 'address': '300 SW 7th St', 'city': 'Oklahoma City', 'zip': '73109'},
                {'name': 'Tulsa City Library', 'address': '400 Civic Center', 'city': 'Tulsa', 'zip': '74103'},
                {'name': 'Norman Public Library', 'address': '225 N Webster Ave', 'city': 'Norman', 'zip': '73069'},
            ],
            'Oregon': [
                {'name': 'Multnomah County Library', 'address': '801 SW 10th Ave', 'city': 'Portland', 'zip': '97204'},
                {'name': 'Oregon State Capitol', 'address': '900 Court St NE', 'city': 'Salem', 'zip': '97301'},
                {'name': 'Tom McCall Waterfront Park', 'address': '98 SW Naito Pkwy', 'city': 'Portland', 'zip': '97204'},
                {'name': 'Eugene Public Library', 'address': '100 W 10th Ave', 'city': 'Eugene', 'zip': '97401'},
                {'name': 'Salem Public Library', 'address': '585 Liberty St SE', 'city': 'Salem', 'zip': '97301'},
            ],
            'Pennsylvania': [
                {'name': 'Free Library Philadelphia', 'address': '1901 Vine St', 'city': 'Philadelphia', 'zip': '19103'},
                {'name': 'Pennsylvania State Capitol', 'address': '501 N 3rd St', 'city': 'Harrisburg', 'zip': '17120'},
                {'name': 'Rittenhouse Square', 'address': '1800 Walnut St', 'city': 'Philadelphia', 'zip': '19103'},
                {'name': 'Carnegie Library Pittsburgh', 'address': '4400 Forbes Ave', 'city': 'Pittsburgh', 'zip': '15213'},
                {'name': 'Allentown Public Library', 'address': '1210 Hamilton St', 'city': 'Allentown', 'zip': '18102'},
            ],
            'Rhode Island': [
                {'name': 'Providence Public Library', 'address': '150 Empire St', 'city': 'Providence', 'zip': '02903'},
                {'name': 'Rhode Island State House', 'address': '82 Smith St', 'city': 'Providence', 'zip': '02903'},
                {'name': 'Roger Williams Park', 'address': '1000 Elmwood Ave', 'city': 'Providence', 'zip': '02907'},
                {'name': 'Warwick Public Library', 'address': '600 Sandy Ln', 'city': 'Warwick', 'zip': '02886'},
                {'name': 'Newport Public Library', 'address': '300 Spring St', 'city': 'Newport', 'zip': '02840'},
            ],
            'South Carolina': [
                {'name': 'Charleston County Library', 'address': '68 Calhoun St', 'city': 'Charleston', 'zip': '29401'},
                {'name': 'South Carolina State House', 'address': '1100 Gervais St', 'city': 'Columbia', 'zip': '29201'},
                {'name': 'Marion Square', 'address': '329 Meeting St', 'city': 'Charleston', 'zip': '29403'},
                {'name': 'Richland Library', 'address': '1431 Assembly St', 'city': 'Columbia', 'zip': '29201'},
                {'name': 'Greenville County Library', 'address': '25 Heritage Green Pl', 'city': 'Greenville', 'zip': '29601'},
            ],
            'South Dakota': [
                {'name': 'Siouxland Libraries', 'address': '200 N Dakota Ave', 'city': 'Sioux Falls', 'zip': '57104'},
                {'name': 'South Dakota State Capitol', 'address': '500 E Capitol Ave', 'city': 'Pierre', 'zip': '57501'},
                {'name': 'Falls Park', 'address': '131 E Falls Park Dr', 'city': 'Sioux Falls', 'zip': '57104'},
                {'name': 'Rapid City Library', 'address': '610 Quincy St', 'city': 'Rapid City', 'zip': '57701'},
                {'name': 'Aberdeen Library', 'address': '215 SE 4th Ave', 'city': 'Aberdeen', 'zip': '57401'},
            ],
            'Tennessee': [
                {'name': 'Nashville Public Library', 'address': '615 Church St', 'city': 'Nashville', 'zip': '37219'},
                {'name': 'Tennessee State Capitol', 'address': '600 Dr MLK Jr Blvd', 'city': 'Nashville', 'zip': '37243'},
                {'name': 'Centennial Park', 'address': '2500 West End Ave', 'city': 'Nashville', 'zip': '37203'},
                {'name': 'Memphis Public Library', 'address': '3030 Poplar Ave', 'city': 'Memphis', 'zip': '38111'},
                {'name': 'Knox County Library', 'address': '500 W Church Ave', 'city': 'Knoxville', 'zip': '37902'},
            ],
            'Texas': [
                {'name': 'Houston Public Library', 'address': '500 McKinney St', 'city': 'Houston', 'zip': '77002'},
                {'name': 'Dallas Public Library', 'address': '1515 Young St', 'city': 'Dallas', 'zip': '75201'},
                {'name': 'Austin Central Library', 'address': '710 W Cesar Chavez St', 'city': 'Austin', 'zip': '78701'},
                {'name': 'San Antonio Library', 'address': '600 Soledad St', 'city': 'San Antonio', 'zip': '78205'},
                {'name': 'Fort Worth Library', 'address': '500 W 3rd St', 'city': 'Fort Worth', 'zip': '76102'},
            ],
            'Utah': [
                {'name': 'Salt Lake City Library', 'address': '210 E 400 S', 'city': 'Salt Lake City', 'zip': '84111'},
                {'name': 'Utah State Capitol', 'address': '350 State St', 'city': 'Salt Lake City', 'zip': '84103'},
                {'name': 'Liberty Park', 'address': '600 E 900 S', 'city': 'Salt Lake City', 'zip': '84105'},
                {'name': 'Provo City Library', 'address': '550 N University Ave', 'city': 'Provo', 'zip': '84601'},
                {'name': 'Park City Library', 'address': '1255 Park Ave', 'city': 'Park City', 'zip': '84060'},
            ],
            'Vermont': [
                {'name': 'Fletcher Free Library', 'address': '235 College St', 'city': 'Burlington', 'zip': '05401'},
                {'name': 'Vermont State House', 'address': '115 State St', 'city': 'Montpelier', 'zip': '05633'},
                {'name': 'Waterfront Park', 'address': '1 College St', 'city': 'Burlington', 'zip': '05401'},
                {'name': 'Rutland Free Library', 'address': '10 Court St', 'city': 'Rutland', 'zip': '05701'},
                {'name': 'Kellogg-Hubbard Library', 'address': '135 Main St', 'city': 'Montpelier', 'zip': '05602'},
            ],
            'Virginia': [
                {'name': 'Richmond Public Library', 'address': '101 E Franklin St', 'city': 'Richmond', 'zip': '23219'},
                {'name': 'Virginia State Capitol', 'address': '1000 Bank St', 'city': 'Richmond', 'zip': '23219'},
                {'name': 'Byrd Park', 'address': '600 S Boulevard', 'city': 'Richmond', 'zip': '23220'},
                {'name': 'Virginia Beach Library', 'address': '4100 Virginia Beach Blvd', 'city': 'Virginia Beach', 'zip': '23452'},
                {'name': 'Norfolk Public Library', 'address': '235 E Plume St', 'city': 'Norfolk', 'zip': '23510'},
            ],
            'Washington': [
                {'name': 'Seattle Central Library', 'address': '1000 4th Ave', 'city': 'Seattle', 'zip': '98104'},
                {'name': 'Washington State Capitol', 'address': '416 Sid Snyder Ave SW', 'city': 'Olympia', 'zip': '98504'},
                {'name': 'Discovery Park', 'address': '3801 Discovery Park Blvd', 'city': 'Seattle', 'zip': '98199'},
                {'name': 'Spokane Public Library', 'address': '906 W Main Ave', 'city': 'Spokane', 'zip': '99201'},
                {'name': 'Tacoma Public Library', 'address': '1102 Tacoma Ave S', 'city': 'Tacoma', 'zip': '98402'},
            ],
            'West Virginia': [
                {'name': 'Charleston Library', 'address': '123 Capitol St', 'city': 'Charleston', 'zip': '25301'},
                {'name': 'West Virginia State Capitol', 'address': '1900 Kanawha Blvd E', 'city': 'Charleston', 'zip': '25305'},
                {'name': 'Coonskin Park', 'address': '2000 Coonskin Dr', 'city': 'Charleston', 'zip': '25311'},
                {'name': 'Huntington Library', 'address': '1445 5th Ave', 'city': 'Huntington', 'zip': '25701'},
                {'name': 'Morgantown Library', 'address': '373 Spruce St', 'city': 'Morgantown', 'zip': '26505'},
            ],
            'Wisconsin': [
                {'name': 'Milwaukee Public Library', 'address': '814 W Wisconsin Ave', 'city': 'Milwaukee', 'zip': '53233'},
                {'name': 'Wisconsin State Capitol', 'address': '2 E Main St', 'city': 'Madison', 'zip': '53703'},
                {'name': 'Lake Park', 'address': '2975 N Lake Park Rd', 'city': 'Milwaukee', 'zip': '53211'},
                {'name': 'Madison Public Library', 'address': '201 W Mifflin St', 'city': 'Madison', 'zip': '53703'},
                {'name': 'Green Bay Library', 'address': '515 Pine St', 'city': 'Green Bay', 'zip': '54301'},
            ],
            'Wyoming': [
                {'name': 'Laramie County Library', 'address': '2200 Pioneer Ave', 'city': 'Cheyenne', 'zip': '82001'},
                {'name': 'Wyoming State Capitol', 'address': '200 W 24th St', 'city': 'Cheyenne', 'zip': '82002'},
                {'name': 'Lions Park', 'address': '1100 S Lions Park Dr', 'city': 'Cheyenne', 'zip': '82001'},
                {'name': 'Natrona County Library', 'address': '307 E 2nd St', 'city': 'Casper', 'zip': '82601'},
                {'name': 'Teton County Library', 'address': '125 Virginian Ln', 'city': 'Jackson', 'zip': '83001'},
            ]
        }
        
        # State codes mapping
        self.state_codes = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
            'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
            'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
            'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
            'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
            'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
            'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
            'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
            'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
            'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
            'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
            'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
            'Wisconsin': 'WI', 'Wyoming': 'WY'
        }
        
        # Area codes by state for phone generation
        self.area_codes = {
            'Alabama': ['205', '251', '256', '334', '938'],
            'Alaska': ['907'],
            'Arizona': ['480', '520', '602', '623', '928'],
            'Arkansas': ['479', '501', '870'],
            'California': ['209', '213', '310', '323', '408', '415', '424', '442', '510', '530', '559', '562', '619', '626', '628', '650', '657', '661', '669', '707', '714', '747', '760', '805', '818', '831', '858', '909', '916', '925', '949', '951'],
            'Colorado': ['303', '719', '720', '970'],
            'Connecticut': ['203', '475', '860', '959'],
            'Delaware': ['302'],
            'Florida': ['239', '305', '321', '352', '386', '407', '561', '727', '754', '772', '786', '813', '850', '863', '904', '941', '954'],
            'Georgia': ['229', '404', '470', '478', '678', '706', '762', '770', '912'],
            'Hawaii': ['808'],
            'Idaho': ['208', '986'],
            'Illinois': ['217', '224', '309', '312', '618', '630', '708', '773', '779', '815', '847', '872'],
            'Indiana': ['219', '260', '317', '463', '574', '765', '812', '930'],
            'Iowa': ['319', '515', '563', '641', '712'],
            'Kansas': ['316', '620', '785', '913'],
            'Kentucky': ['270', '364', '502', '606', '859'],
            'Louisiana': ['225', '318', '337', '504', '985'],
            'Maine': ['207'],
            'Maryland': ['240', '301', '410', '443', '667'],
            'Massachusetts': ['339', '351', '413', '508', '617', '774', '781', '857', '978'],
            'Michigan': ['231', '248', '269', '313', '517', '586', '616', '734', '810', '906', '947', '989'],
            'Minnesota': ['218', '320', '507', '612', '651', '763', '952'],
            'Mississippi': ['228', '601', '662', '769'],
            'Missouri': ['314', '417', '573', '636', '660', '816'],
            'Montana': ['406'],
            'Nebraska': ['308', '402', '531'],
            'Nevada': ['702', '725', '775'],
            'New Hampshire': ['603'],
            'New Jersey': ['201', '551', '609', '732', '848', '856', '862', '908', '973'],
            'New Mexico': ['505', '575'],
            'New York': ['212', '315', '332', '347', '516', '518', '585', '607', '631', '646', '680', '716', '718', '838', '845', '914', '917', '929', '934'],
            'North Carolina': ['252', '336', '704', '743', '828', '910', '919', '980', '984'],
            'North Dakota': ['701'],
            'Ohio': ['216', '234', '330', '380', '419', '440', '513', '567', '614', '740', '937'],
            'Oklahoma': ['405', '539', '580', '918'],
            'Oregon': ['458', '503', '541', '971'],
            'Pennsylvania': ['215', '223', '267', '272', '412', '484', '570', '610', '717', '724', '814', '878'],
            'Rhode Island': ['401'],
            'South Carolina': ['803', '843', '854', '864'],
            'South Dakota': ['605'],
            'Tennessee': ['423', '615', '629', '731', '865', '901', '931'],
            'Texas': ['210', '214', '254', '281', '325', '346', '361', '409', '430', '432', '469', '512', '682', '713', '726', '737', '806', '817', '830', '832', '903', '915', '936', '940', '956', '972', '979'],
            'Utah': ['385', '435', '801'],
            'Vermont': ['802'],
            'Virginia': ['276', '434', '540', '571', '703', '757', '804'],
            'Washington': ['206', '253', '360', '425', '509', '564'],
            'West Virginia': ['304', '681'],
            'Wisconsin': ['262', '414', '534', '608', '715', '920'],
            'Wyoming': ['307']
        }
    
    def generate_unique_hash(self, *args):
        """Generate a hash from multiple arguments for uniqueness checking"""
        combined = '|'.join(str(arg) for arg in args)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def generate_phone_number(self, state):
        """Generate unique phone number with appropriate area code"""
        max_attempts = 100
        for attempt in range(max_attempts):
            area_code = random.choice(self.area_codes.get(state, ['555']))
            exchange = f"{random.randint(200, 999)}"
            subscriber = f"{random.randint(1000, 9999)}"
            phone = f"({area_code}) {exchange}-{subscriber}"
            
            if phone not in self.unique_tracker['phones']:
                self.unique_tracker['phones'].add(phone)
                return phone
            
            self.generation_stats['collision_attempts'] += 1
        
        # Fallback with guaranteed uniqueness
        unique_num = len(self.unique_tracker['phones'])
        phone = f"({area_code}) 999-{unique_num:04d}"
        self.unique_tracker['phones'].add(phone)
        return phone
    
    def generate_unique_email(self, first_name, last_name):
        """Generate unique email address"""
        domains = ['email.com', 'mail.com', 'inbox.com', 'webmail.com', 'postbox.com', 
                  'fastmail.com', 'promail.com', 'workmail.com']
        
        max_attempts = 50
        for attempt in range(max_attempts):
            # Try different email patterns
            patterns = [
                f"{first_name.lower()}.{last_name.lower()}",
                f"{first_name[0].lower()}{last_name.lower()}",
                f"{first_name.lower()}{last_name[0].lower()}",
                f"{first_name.lower()}_{last_name.lower()}"
            ]
            
            pattern = random.choice(patterns)
            num = random.randint(1, 9999) if attempt > 10 else random.randint(1, 99)
            email = f"{pattern}{num}@{random.choice(domains)}"
            
            if email not in self.unique_tracker['emails']:
                self.unique_tracker['emails'].add(email)
                return email
            
            self.generation_stats['collision_attempts'] += 1
        
        # Fallback with timestamp
        timestamp = int(datetime.now().timestamp() * 1000) % 1000000
        email = f"{first_name.lower()}.{last_name.lower()}{timestamp}@{domains[0]}"
        self.unique_tracker['emails'].add(email)
        return email
    
    def generate_unique_name(self):
        """Generate unique name combination"""
        max_attempts = 200
        
        for attempt in range(max_attempts):
            gender = random.choice(['male', 'female'])
            first_name = random.choice(self.first_names[gender])
            last_name = random.choice(self.last_names)
            full_name = f"{first_name} {last_name}"
            
            # Check both full name and hash
            name_hash = self.generate_unique_hash(first_name, last_name)
            
            if full_name not in self.unique_tracker['full_names'] and \
               name_hash not in self.unique_tracker['name_hashes']:
                self.unique_tracker['full_names'].add(full_name)
                self.unique_tracker['name_hashes'].add(name_hash)
                return first_name, last_name
            
            self.generation_stats['collision_attempts'] += 1
        
        # Fallback: add middle initial or number
        self.generation_stats['unique_regenerations'] += 1
        unique_id = len(self.unique_tracker['full_names'])
        middle_initial = chr(65 + (unique_id % 26))  # A-Z
        first_name = f"{first_name} {middle_initial}"
        full_name = f"{first_name} {last_name}"
        
        self.unique_tracker['full_names'].add(full_name)
        name_hash = self.generate_unique_hash(first_name, last_name)
        self.unique_tracker['name_hashes'].add(name_hash)
        
        return first_name, last_name
    
    def generate_unique_address(self, state):
        """Generate unique address from public places"""
        places = self.public_places[state]
        max_attempts = len(places) * 2
        
        for attempt in range(max_attempts):
            place = random.choice(places)
            full_address = f"{place['address']}, {place['city']}, {self.state_codes[state]} {place['zip']}"
            
            # Allow reuse of addresses but track for statistics
            if full_address not in self.unique_tracker['addresses'] or attempt > len(places):
                if full_address not in self.unique_tracker['addresses']:
                    self.unique_tracker['addresses'].add(full_address)
                return place
            
            self.generation_stats['collision_attempts'] += 1
        
        # If all addresses used, allow reuse
        return random.choice(places)
    
    def generate_persona(self, state=None):
        """Generate a single unique persona"""
        # Select state
        if state and state != 'Mixed':
            selected_state = state
        else:
            selected_state = random.choice(list(self.public_places.keys()))
        
        # Generate unique components
        first_name, last_name = self.generate_unique_name()
        email = self.generate_unique_email(first_name.split()[0], last_name)  # Use base first name
        phone = self.generate_phone_number(selected_state)
        place = self.generate_unique_address(selected_state)
        
        # Create persona
        persona = {
            'ID': f"P{self.generation_stats['total_generated'] + 1:06d}",
            'First Name': first_name,
            'Last Name': last_name,
            'Email': email,
            'Phone': phone,
            'Location Name': place['name'],
            'Street Address': place['address'],
            'City': place['city'],
            'State': self.state_codes[selected_state],
            'ZIP Code': place['zip'],
            'Full Address': f"{place['address']}, {place['city']}, {self.state_codes[selected_state]} {place['zip']}",
            'Type': 'Public Place',
            'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Generate and check persona hash for complete uniqueness
        persona_hash = self.generate_unique_hash(
            first_name, last_name, email, phone, persona['Full Address']
        )
        
        if persona_hash in self.unique_tracker['person_hashes']:
            # Extremely rare case - regenerate with modifications
            self.generation_stats['unique_regenerations'] += 1
            persona['Email'] = self.generate_unique_email(first_name.split()[0] + str(random.randint(1,99)), last_name)
            persona_hash = self.generate_unique_hash(
                first_name, last_name, persona['Email'], phone, persona['Full Address']
            )
        
        self.unique_tracker['person_hashes'].add(persona_hash)
        self.generation_stats['total_generated'] += 1
        
        return persona
    
    def generate_multiple_personas(self, count, state=None):
        """Generate multiple unique personas"""
        personas = []
        
        for i in range(count):
            personas.append(self.generate_persona(state))
        
        return personas
    
    def get_uniqueness_report(self):
        """Generate a report on data uniqueness"""
        return {
            'Total Generated': self.generation_stats['total_generated'],
            'Unique Names': len(self.unique_tracker['full_names']),
            'Unique Emails': len(self.unique_tracker['emails']),
            'Unique Phones': len(self.unique_tracker['phones']),
            'Unique Addresses Used': len(self.unique_tracker['addresses']),
            'Collision Attempts': self.generation_stats['collision_attempts'],
            'Fallback Regenerations': self.generation_stats['unique_regenerations'],
            'Uniqueness Rate': f"{(1 - self.generation_stats['unique_regenerations'] / max(self.generation_stats['total_generated'], 1)) * 100:.2f}%"
        }

# Streamlit App
def main():
    # Clean header
    st.title("Test Persona Generator")
    st.markdown("Generate test personas with public place addresses across all 50 US states")
    
    # Initialize generator in session state
    if 'generator' not in st.session_state:
        st.session_state['generator'] = PersonaGenerator()
    
    generator = st.session_state['generator']
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        num_personas = st.number_input(
            "Number of Personas",
            min_value=1,
            max_value=5000,
            value=10,
            step=1,
            help="Maximum 5000 for performance"
        )
        
        states = ['Mixed (All States)'] + sorted(list(generator.public_places.keys()))
        selected_state = st.selectbox(
            "Location",
            options=states,
            help="Select specific state or mixed"
        )
        
        if selected_state == 'Mixed (All States)':
            selected_state = 'Mixed'
        
        generate_button = st.button(
            "Generate Personas",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Information sections
        with st.expander("Features"):
            st.markdown("""
            - All 50 US states
            - 250+ public places
            - Real area codes
            - 100% unique data
            - Public institutions only
            """)
        
        with st.expander("Uniqueness"):
            st.markdown("""
            **Guaranteed unique:**
            - Full names
            - Email addresses  
            - Phone numbers
            - MD5 hash verification
            """)
            
            if st.button("Reset Tracking"):
                st.session_state['generator'] = PersonaGenerator()
                st.success("Tracking reset")
    
    # Main content area
    if generate_button:
        try:
            with st.spinner(f"Generating {num_personas} personas..."):
                personas = generator.generate_multiple_personas(
                    num_personas, 
                    selected_state if selected_state != 'Mixed' else None
                )
                
                df = pd.DataFrame(personas)
                st.session_state['generated_data'] = df
                st.session_state['timestamp'] = datetime.now()
                st.session_state['uniqueness_report'] = generator.get_uniqueness_report()
            
            st.success(f"Generated {len(personas)} unique personas")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display results
    if 'generated_data' in st.session_state:
        df = st.session_state['generated_data']
        timestamp = st.session_state['timestamp']
        uniqueness_report = st.session_state.get('uniqueness_report', {})
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Personas", len(df))
        with col2:
            st.metric("Unique States", df['State'].nunique())
        with col3:
            st.metric("Uniqueness", uniqueness_report.get('Uniqueness Rate', '100%'))
        with col4:
            st.metric("Generated", timestamp.strftime('%H:%M:%S'))
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Data & Copy",
            "Verification",
            "Analytics",
            "State View",
            "Export"
        ])
        
        with tab1:
            # Quick copy section
            st.subheader("Quick Copy for Call Sim")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Single Persona**")
                persona_index = st.selectbox(
                    "Select:",
                    range(len(df)),
                    format_func=lambda x: f"{df.iloc[x]['First Name']} {df.iloc[x]['Last Name']}"
                )
                
                selected_persona = df.iloc[persona_index]
                
                formatted_text = f"""Name: {selected_persona['First Name']} {selected_persona['Last Name']}
Email: {selected_persona['Email']}
Phone: {selected_persona['Phone']}
Address: {selected_persona['Full Address']}"""
                
                # Text area for displaying persona info
                st.text_area(
                    "Copy this:",
                    value=formatted_text,
                    height=150,
                    key="single_copy_area"
                )
                
                # Copy button below the text box
                if st.button("Copy one person information", key="copy_single_btn", use_container_width=True):
                    if CLIPBOARD_AVAILABLE:
                        try:
                            pyperclip.copy(formatted_text)
                            st.success("✓ Copied to clipboard!")
                        except Exception as e:
                            st.warning("Could not copy to clipboard. Please select the text manually and copy.")
                            st.info("For automatic copy, run this app locally with pyperclip installed: pip install pyperclip")
                    else:
                        st.warning("Automatic clipboard copy not available. Please select the text above and press Ctrl+C (or Cmd+C on Mac)")
                        st.info("For automatic copy, install pyperclip: pip install pyperclip")
            
            with col2:
                st.markdown("**Bulk Copy**")
                num_to_copy = st.slider("Number:", 1, min(10, len(df)), 3)
                
                bulk_text = ""
                for i in range(num_to_copy):
                    p = df.iloc[i]
                    bulk_text += f"{p['First Name']} {p['Last Name']} | {p['Phone']} | {p['Email']}\n{p['Full Address']}\n\n"
                
                st.text_area(
                    f"First {num_to_copy} personas:",
                    value=bulk_text,
                    height=200,
                    key="bulk_personas_text"
                )
            
            st.markdown("---")
            
            # Data table
            st.subheader("Full Data")
            
            available_columns = df.columns.tolist()
            default_columns = ['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Full Address']
            default_columns = [col for col in default_columns if col in available_columns]
            
            display_cols = st.multiselect(
                "Display columns:",
                options=available_columns,
                default=default_columns
            )
            
            if display_cols:
                st.dataframe(df[display_cols], use_container_width=True, height=400)
        
        with tab2:
            st.subheader("Data Verification")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Generation Metrics**")
                for metric, value in {
                    "Total Generated": uniqueness_report.get('Total Generated', 0),
                    "Unique Names": uniqueness_report.get('Unique Names', 0),
                    "Unique Emails": uniqueness_report.get('Unique Emails', 0),
                    "Unique Phones": uniqueness_report.get('Unique Phones', 0)
                }.items():
                    st.markdown(f"- {metric}: **{value:,}**")
            
            with col2:
                st.markdown("**Performance**")
                for metric, value in {
                    "Collisions": uniqueness_report.get('Collision Attempts', 0),
                    "Regenerations": uniqueness_report.get('Fallback Regenerations', 0),
                    "Success Rate": uniqueness_report.get('Uniqueness Rate', '100%')
                }.items():
                    st.markdown(f"- {metric}: **{value}**")
            
            st.markdown("---")
            st.markdown("**Uniqueness Tests**")
            
            tests = {
                'Emails': len(df['Email'].unique()) == len(df),
                'Phones': len(df['Phone'].unique()) == len(df),
                'Names': len(df[['First Name', 'Last Name']].drop_duplicates()) == len(df),
                'IDs': len(df['ID'].unique()) == len(df)
            }
            
            all_passed = all(tests.values())
            for test_name, passed in tests.items():
                st.markdown(f"- {test_name}: {'✓ PASSED' if passed else '✗ FAILED'}")
            
            if all_passed:
                st.success("All uniqueness tests passed")
        
        with tab3:
            st.subheader("Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**State Distribution**")
                state_counts = df['State'].value_counts()
                st.bar_chart(state_counts, height=250)
            
            with col2:
                st.markdown("**Top Locations**")
                location_counts = df['Location Name'].value_counts().head(5)
                st.bar_chart(location_counts, height=250)
            
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("States Used", f"{df['State'].nunique()}/50")
            with col2:
                st.metric("Coverage", f"{(df['State'].nunique()/50)*100:.1f}%")
            with col3:
                st.metric("Cities", df['City'].nunique())
            with col4:
                st.metric("ZIP Codes", df['ZIP Code'].nunique())
        
        with tab4:
            st.subheader("State View")
            
            state_counts = df['State'].value_counts().to_dict()
            
            selected_state_view = st.selectbox(
                "Select State:",
                options=sorted(df['State'].unique()),
                format_func=lambda x: f"{x} ({state_counts.get(x, 0)} personas)"
            )
            
            state_df = df[df['State'] == selected_state_view]
            
            st.info(f"State: **{selected_state_view}** | Personas: **{len(state_df)}**")
            
            display_columns = ['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'City']
            display_columns = [col for col in display_columns if col in state_df.columns]
            
            st.dataframe(state_df[display_columns], use_container_width=True, height=400)
        
        with tab5:
            st.subheader("Export Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**CSV Format**")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"personas_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.markdown("**Excel Format**")
                if EXCEL_AVAILABLE or OPENPYXL_AVAILABLE:
                    try:
                        output = io.BytesIO()
                        engine = 'xlsxwriter' if EXCEL_AVAILABLE else 'openpyxl'
                        
                        with pd.ExcelWriter(output, engine=engine) as writer:
                            df.to_excel(writer, index=False, sheet_name='Personas')
                            report_df = pd.DataFrame([uniqueness_report])
                            report_df.to_excel(writer, index=False, sheet_name='Report')
                        
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            label="Download Excel",
                            data=excel_data,
                            file_name=f"personas_{timestamp.strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.info("Excel unavailable")
                else:
                    st.info("Excel export requires xlsxwriter or openpyxl")
            
            with col3:
                st.markdown("**JSON Format**")
                json_str = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"personas_{timestamp.strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            st.markdown("---")
            st.markdown("**Preview (first 3 records)**")
            st.dataframe(df.head(3), use_container_width=True)
    
    else:
        # Welcome screen
        st.info("Configure settings in the sidebar and click **Generate Personas** to begin")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **100% Unique Data**  
            Advanced duplicate prevention
            """)
        
        with col2:
            st.markdown("""
            **All 50 States**  
            250+ public locations
            """)
        
        with col3:
            st.markdown("""
            **Ethical Testing**  
            Public institution addresses only
            """)

if __name__ == "__main__":
    main()
    
