import requests
from pprint import pprint

base_url = 'https://clinicaltrials.gov/api/v2'

# this function add_to_count adds numbers, if asked, to my status, sponsor, condition, and side_effect counts dictionaries:
def add_to_count(item, counts):
        if item in counts:
            counts[item] = counts[item] + 1
        else:
            counts[item] = 1

def get_title(identification):
        if 'officialTitle' in identification:
            return identification['officialTitle']
        else:
            return identification['briefTitle']

def show_drug(drug):
    print("Analyzing:", drug)


def organized(dictionary):
    for item, counts in dictionary.items():
        readable_status = item.replace("_", " ").title()
        print("   ", readable_status, "—", counts, "studies")

def get_top_three(dictionary):
     top_three = sorted(
          dictionary.items(),
          key=lambda item: item[1],
          reverse=True
     )[:3]
     return top_three

# Calling hte API and the user inputs the drug they wanna search for.
drugs = input("Enter a drug: ")

while drugs.strip() == "":
     print("You have to enter a drug")
     drugs = input("\nEnter a drug: ")

params = {
    'query.term': drugs,
    'pageSize': 100,
    'sort': 'ResultsFirstPostDate'
}

response = requests.get(base_url + '/studies', params=params)
studies = response.json()['studies']

if len(studies) == 0:
     print(f"\n[!] No studies found for '{drugs}'. Please check your spelling and try again.")
     exit()

study = studies[0]

status_counts = {}
sponsor_counts = {}
condition_counts = {}
side_effect_count = {}
total_participants = 0
recruiting_studies = []

# For loop begins (runs for every individual study):
for study in studies:
    
    identification = study['protocolSection']['identificationModule']
    title = get_title(identification)
    sponsor = study['protocolSection']['sponsorCollaboratorsModule']['leadSponsor']['name']
    conditions = study['protocolSection']['conditionsModule']['conditions']

    if 'resultsSection' in study:
            if 'adverseEventsModule' in study['resultsSection']:
                if 'otherEvents' in study['resultsSection']['adverseEventsModule']:
                    side_effect_list = study['resultsSection']['adverseEventsModule']['otherEvents']
                    
                    for side_effects in side_effect_list:
                        side_effect_name = side_effects['term']
                        add_to_count(side_effect_name, side_effect_count)

    for condition in conditions:
        
        add_to_count(condition, condition_counts)

    design = study['protocolSection']['designModule']
    if 'enrollmentInfo' in design:
        participants = design['enrollmentInfo']['count']
        total_participants = participants + total_participants
    else:
        participants = 0


    status = study['protocolSection']['statusModule']['overallStatus']

    if status == "RECRUITING":
         recruiting = {
              "title" : title,
              "condition" : conditions,
              "participants" : participants    
         }
         recruiting_studies.append(recruiting)

    add_to_count(status, status_counts)
    add_to_count(sponsor, sponsor_counts)


top_side_effects = get_top_three(side_effect_count)

top_sponsors = get_top_three(sponsor_counts)

top_conditions = get_top_three(condition_counts)


print("\n Choose how you want to view the data: ")
print("[1] Patient Mode")
print("[2] Researcher Mode")
print("[3] Participant Mode")

choice = input("\nSelect 1-3: ")

if choice == "1":
     print("\nPatient Mode")
     print("-" * 40 + "\nTotal studies found:", len(studies))
     print(f"\nTotal participants: {total_participants:,}")
     print("\nStudy Status Breakdown:")
     print("This shows how many studies are completed, stopped early,")
     print("or still active but no longer accepting new participants:")
     organized(status_counts)
     print("\nMost Frequently Reported Side Effects:")
     for side_effect, count in top_side_effects:
        print("   ", side_effect, "— reported in", count, "studies")
     
elif choice == "2":
     print("\nResearcher Mode")
     print("\nMost Active Study Sponsors:")
     for sponsor, count in top_sponsors:
        print("   ", sponsor, "— led", count, "studies")
     print("\nWhat This Drug Is Being Studied For:")
     for condition, count in top_conditions:
        print("   ", condition, "—", count, "studies")
        


elif choice == "3":
     print("Participant Mode")
     if len(recruiting_studies) == 0:
          print("\nNo recruiting studies were found for this drug. ")
     else:
          for recruit in recruiting_studies:
            print("\n" + "-" * 50)
            print("Study:", recruit["title"])
            print("\nHealth Conditions Being Studied:")
            
            for condition in recruit["condition"]:
                 print("\n   -", condition)
            print("\nPlanned Participants:", recruit["participants"])
                 
else:
     print("\nInvalid option. Please try again! ")

