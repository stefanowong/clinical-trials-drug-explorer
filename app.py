import streamlit as st
import requests

st.set_page_config(
    page_title="Clinical Trials Drug Explorer",
    page_icon="🧪",
    layout="wide"
)

base_url = "https://clinicaltrials.gov/api/v2"

# functions

def add_to_count(item, counts):
    if item in counts:
        counts[item] = counts[item] + 1
    else:
        counts[item] = 1


def get_title(identification):
    if "officialTitle" in identification:
        return identification["officialTitle"]
    else:
        return identification["briefTitle"]


def get_top_three(dictionary):
    top_three = sorted(
        dictionary.items(),
        key=lambda item: item[1],
        reverse=True
    )[:3]

    return top_three


# page title 
st.title("🧪 Clinical Trials Drug Explorer")

st.write(
    "Search ClinicalTrials.gov to explore study activity, "
    "participants, sponsors, health conditions, and recruiting trials."
)

with st.form("drug_search_form"):
    drug = st.text_input(
        "Enter a drug:",
        placeholder="Example: aspirin"
    )

    search = st.form_submit_button("Search")

# run search

if search:

    if not drug.strip():
        st.warning("Please enter a drug before searching.")

    else:

        params = {
            "query.term": drug.strip(),
            "pageSize": 100,
            "sort": "ResultsFirstPostDate"
        }

        try:
            with st.spinner(f"Searching for studies about {drug}..."):

                response = requests.get(
                    base_url + "/studies",
                    params=params,
                    timeout=30
                )

                response.raise_for_status()

                studies = response.json()["studies"]

        except requests.exceptions.RequestException as error:
            st.error("The app could not connect to ClinicalTrials.gov.")
            st.write("Technical details:", error)
            st.stop()

        except KeyError:
            st.error("The API response did not contain a studies section.")
            st.stop()


       # no results

        if len(studies) == 0:
            st.warning(
                f"No studies were found for '{drug}'. "
                "Check the spelling and try again."
            )

        else:

            # empty dicitonaries, etc

            status_counts = {}
            sponsor_counts = {}
            condition_counts = {}
            side_effect_count = {}

            total_participants = 0
            recruiting_studies = []


            

            for study in studies:

                protocol = study.get("protocolSection", {})

                identification = protocol.get(
                    "identificationModule",
                    {}
                )

                title = get_title(identification)

                sponsor_module = protocol.get(
                    "sponsorCollaboratorsModule",
                    {}
                )

                lead_sponsor = sponsor_module.get(
                    "leadSponsor",
                    {}
                )

                sponsor = lead_sponsor.get(
                    "name",
                    "Unknown sponsor"
                )

                conditions_module = protocol.get(
                    "conditionsModule",
                    {}
                )

                conditions = conditions_module.get(
                    "conditions",
                    []
                )

                for condition in conditions:
                    add_to_count(condition, condition_counts)


                # Participants

                design = protocol.get("designModule", {})

                enrollment_info = design.get(
                    "enrollmentInfo",
                    {}
                )

                participants = enrollment_info.get(
                    "count",
                    0
                )

                if isinstance(participants, int):
                    total_participants += participants


                # Status

                status_module = protocol.get(
                    "statusModule",
                    {}
                )

                status = status_module.get(
                    "overallStatus",
                    "UNKNOWN"
                )

                add_to_count(status, status_counts)
                add_to_count(sponsor, sponsor_counts)


                # recruiting studies

                if status == "RECRUITING":

                    recruiting = {
                        "title": title,
                        "conditions": conditions,
                        "participants": participants
                    }

                    recruiting_studies.append(recruiting)


                # side effects

                results_section = study.get(
                    "resultsSection",
                    {}
                )

                adverse_events = results_section.get(
                    "adverseEventsModule",
                    {}
                )

                side_effect_list = adverse_events.get(
                    "otherEvents",
                    []
                )

                for side_effect in side_effect_list:

                    side_effect_name = side_effect.get("term")

                    if side_effect_name:
                        add_to_count(
                            side_effect_name,
                            side_effect_count
                        )


            # Results

            top_side_effects = get_top_three(side_effect_count)
            top_sponsors = get_top_three(sponsor_counts)
            top_conditions = get_top_three(condition_counts)


            # metrics

            st.success(
                f"Analysis completed for: {drug.title()}"
            )

            metric1, metric2, metric3 = st.columns(3)

            with metric1:
                st.metric(
                    "Studies analyzed",
                    len(studies)
                )

            with metric2:
                st.metric(
                    "Total planned participants",
                    f"{total_participants:,}"
                )

            with metric3:
                st.metric(
                    "Recruiting studies",
                    len(recruiting_studies)
                )


            # MODES

            patient_tab, researcher_tab, participant_tab = st.tabs(
                [
                    "Patient Mode",
                    "Researcher Mode",
                    "Participant Mode"
                ]
            )


            # Patient mode

            with patient_tab:

                st.header("Patient Mode")

                st.subheader("Study Status Breakdown")

                st.write(
                    "This shows whether studies are completed, "
                    "currently active, recruiting, stopped, etc."
                )

                for status, count in status_counts.items():

                    readable_status = status.replace(
                        "_",
                        " "
                    ).title()

                    st.write(
                        f"**{readable_status}:** "
                        f"{count} studies"
                    )


                st.subheader(
                    "Most Frequently Reported Side Effects"
                )

                if len(top_side_effects) == 0:

                    st.info(
                        "No reported side effect results were "
                        "available in these studies."
                    )

                else:

                    for side_effect, count in top_side_effects:

                        st.write(
                            f"**{side_effect}:** reported in "
                            f"{count} studies"
                        )


            # Research mode

            with researcher_tab:

                st.header("Researcher Mode")

                st.subheader("Most Active Study Sponsors")

                if len(top_sponsors) == 0:

                    st.info("No sponsor information was found.")

                else:

                    for sponsor, count in top_sponsors:

                        st.write(
                            f"**{sponsor}:** led {count} studies"
                        )


                st.subheader(
                    "What This Drug Is Being Studied For"
                )

                if len(top_conditions) == 0:

                    st.info(
                        "No condition information was found."
                    )

                else:

                    for condition, count in top_conditions:

                        st.write(
                            f"**{condition}:** {count} studies"
                        )


            # Participant mode

            with participant_tab:

                st.header("Participant Mode")

                st.write(
                    "These studies are currently marked as "
                    "recruiting by ClinicalTrials.gov."
                )

                if len(recruiting_studies) == 0:

                    st.info(
                        "No recruiting studies were found "
                        "for this drug."
                    )

                else:

                    for number, recruit in enumerate(
                        recruiting_studies,
                        start=1
                    ):

                        with st.expander(
                            f"{number}. {recruit['title']}"
                        ):

                            st.write(
                                "**Health conditions being studied:**"
                            )

                            if len(recruit["conditions"]) == 0:

                                st.write(
                                    "No conditions were listed."
                                )

                            else:

                                for condition in recruit["conditions"]:
                                    st.write(f"- {condition}")

                            st.write(
                                "**Planned participants:**",
                                f"{recruit['participants']:,}"
                                if isinstance(
                                    recruit["participants"],
                                    int
                                )
                                else "Not available"
                            )


            st.caption(
                "This app analyzes up to 100 studies from "
                "ClinicalTrials.gov. It is an educational tool "
                "and does not provide medical advice." "Future updates might be released!"
            )