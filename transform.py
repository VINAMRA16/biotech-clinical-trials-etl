import pandas as pd 
import logging

# Initialize the module-level logger so all logs show they came from 'transform'
logger = logging.getLogger(__name__)

def transform_data(raw_data):

    # 1. THE SAFETY GATE: 
    # If extract.py failed and returned None, exit immediately to prevent crashes.
    if raw_data is None:
        return None

    # 2. TOP-LEVEL UNPACKING:
    # The API wraps the list of clinical trials inside the "studies" key.
    # The 'or []' ensures that if "studies" is missing or None, we get a safe empty list.
    studies = raw_data.get("studies") or []

    # Create an empty list to hold our flattened, clean dictionaries for each row.
    clean_list = []

    # 3. THE EXTRACTION LOOP:
    # Loop through every individual clinical study dictionary ('s') in the studies list.
    for s in studies:
        
        # SHORTCUT VARIABLE: 
        # Every field we want is buried inside "protocolSection". 
        # We unpack it once here (with an 'or {}' safety net) so we don't repeat ourselves 8 times.
        protocol = s.get("protocolSection") or {}
        
        clean_list.append({
            # 2-LEVEL DICT UNPACKING (nct_id):
            # Step 1: Grab "identificationModule" dict (or fall back to empty dict {} if missing).
            # Step 2: Grab "nctId" from inside that dict.
            "nct_id": (protocol.get("identificationModule") or {}).get("nctId"),
            
            # 3-LEVEL DICT UNPACKING (full_name):
            # Step 1: Grab "identificationModule" (or {}).
            # Step 2: Grab "organization" from inside that (or {}).
            # Step 3: Grab "fullName" from inside organization (defaulting to "Unknown" if missing).
            "full_name": ((protocol.get("identificationModule") or {}).get("organization") or {}).get("fullName", "Unknown"),
            
            # 2-LEVEL DICT UNPACKING (title):
            # Pulls the study's brief title from "identificationModule".
            "title": (protocol.get("identificationModule") or {}).get("briefTitle"),
            
            # 2-LEVEL DICT UNPACKING (status):
            # Pulls the trial's current status (e.g., "RECRUITING", "COMPLETED") from "statusModule".
            "status": (protocol.get("statusModule") or {}).get("overallStatus"),
            
            # 3-LEVEL DICT UNPACKING (sponsor_name):
            # Reaches into "sponsorCollaboratorsModule" -> "leadSponsor" -> "name".
            # Each level is shielded with 'or {}' so a missing middle layer never causes a NoneType crash.
            "sponsor_name": ((protocol.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}).get("name", "Unknown"),
            
            # NESTED LIST ARMOR (primary_condition):
            # Step 1: Grab "conditionsModule" (or {}).
            # Step 2: Grab the "conditions" list from inside it.
            # Step 3: If "conditions" is missing OR is an empty list [], 'or ["Unknown"]' forces a 1-item fallback list.
            # Step 4: [0] safely grabs the very first condition string from the list without an IndexError.
            "primary_condition": ((protocol.get("conditionsModule") or {}).get("conditions") or ["Unknown"])[0],
            
            # GHOST LIST ARMOR (primary_phase):
            # Observational trials don't have drug phases, so "phases" is often missing or empty [].
            # 'or ["NA"]' guarantees a non-empty list before [0] grabs the first item.
            "primary_phase": ((protocol.get("designModule") or {}).get("phases") or ["NA"])[0],
            
            # 3-LEVEL NUMBER UNPACKING (enrollment_count):
            # Reaches into "designModule" -> "enrollmentInfo" -> "count" to get the number of patients.
            "enrollment_count": ((protocol.get("designModule") or {}).get("enrollmentInfo") or {}).get("count")
        })

    # 4. TABLE CREATION:
    # Convert our list of flat dictionaries into a structured Pandas DataFrame (rows and columns).
    df = pd.DataFrame(clean_list)

    # Guard against an empty DataFrame if the API returned 0 studies
    if df.empty:
        return df

    # 5. NULL CLEANING:
    # Some trials don't list patient counts (resulting in None/NaN).
    # You cannot convert NaN to an integer, so we drop any row where "enrollment_count" is missing.
    df = df.dropna(subset=["enrollment_count"])

    # 6. DATA TYPE CASTING:
    # Convert "enrollment_count" from float/string into whole integers so we can run math filters on it.
    df["enrollment_count"] = df["enrollment_count"].astype(int)

    # 7. THE QUARANTINE FILTER:
    # Condition 1: df["status"].isin(["RECRUITING", "COMPLETED"]) checks if the status matches either word in our list.
    # Condition 2: df["enrollment_count"] >= 100 checks if the study has at least 100 patients.
    # The '&' operator requires BOTH conditions to be True for a row to survive into clean_df.
    clean_df = df[(df["status"].isin(["RECRUITING", "COMPLETED"])) & (df["enrollment_count"] >= 100)]

    # 8. AUDIT LOG:
    # Compare total raw studies extracted (len(studies)) vs. filtered studies surviving quarantine (len(clean_df)).
    logger.info(f"Total Studies Entering Gate: {len(studies)} | Large-Scale Trials Surviving Quarantine: {len(clean_df)}")

    clean_df.to_csv("PROTOCOL.csv",index=False)

    # Return the clean table back to main.py so it can be sent to load.py
    return clean_df