from datetime import datetime

def is_in_scope_merger_acquisition(target_info, acquirer_info):
    # Exclude if acquirer is PE/VC firm
    if acquirer_info["is_pe_vc_firm"]:
        return False
    # Include if acquirer is operating company
    if acquirer_info["entity_type"] == "Operating Company":
        return True
    return False

def classify_deal_type(target_info, acquirer_info, summary):
    # Corporate Divestiture: Corp sells business unit to another Corp (non-PE)
    if (target_info["entity_type"] == "Operating Company" and
        acquirer_info["entity_type"] == "Operating Company" and
        not acquirer_info["is_pe_vc_firm"]):
        return "Corporate Divestiture"
    return "M&A"

def determine_round_status(summary):
    text = summary.lower()
    if any(word in text for word in ["completed", "has acquired", "closed", "became a part of"]):
        return "Completed"
    elif any(word in text for word in ["definitive agreement", "agreed to acquire", "agrees to"]):
        return "Announced"
    elif "rumored" in text or "people familiar" in text:
        return "Rumored"
    return "Announced"