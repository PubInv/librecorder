"""
Format output as a structured JSON report with required fields.

Report JSON Schema:
{
    "report_version": "0.1.0",
    "classifier_name": "dark_light" | "mean_pixel" | "basic_classifier" | ...,
    "score_or_class": "Dark" | "Light" | <numeric_value>,
    "confidence": 0.95,
    "image_id": "filename.jpg",
    "case_id": "case-...",
    "sample_type": "urine",
    "raw_result": {...}  # Full processor output for reference
}
"""
import json
import pprint

# Valid classifier names
VALID_CLASSIFIERS = {
    "dark_light",
    "mean_pixel",
}


def extract_report_fields(processor_name, result):
    """
    Extract score/class and confidence from processor result.
    Adapts to different processor output formats.
    
    Returns: (score_or_class, confidence) tuple
    """
    score_or_class = None
    confidence = 0.0
    
    if processor_name == "dark_light":
        # Expected: {"sigmoid_score": 0.8, "classification": "Dark", ...}
        score_or_class = result.get("classification", "Unknown")
        confidence = result.get("sigmoid_score", 0.0)
    
    elif processor_name == "mean_pixel":
        # Expected: {"mean_pixel": 128.5}
        score_or_class = result.get("mean_pixel", 0)
        confidence = 1.0  # Mean pixel is deterministic
    
    elif processor_name in VALID_CLASSIFIERS:
        # Desired format of output is {"classification": str, "confidence": float} or {"score": float, "confidence": float}
        score_or_class = result.get("classification", "Unknown") or result.get("score", "Unknown")
        confidence = result.get("confidence", 0.0)
    
    else:
        raise ValueError(f"Unknown processor/classifier name: {processor_name}")
    
    return score_or_class, confidence


def format_output(case_id, sample_type, processor, result, image_id=None, report_version="0.1.0"):
    """
    Generate a structured JSON report from processor output.
    
    Args:
        case_id: Case identifier
        sample_type: Type of sample (e.g., "urine", "tongue")
        processor: Processor/classifier name
        result: Raw result dictionary from processor
        image_id: Filename/image identifier
        report_version: Semantic version string
    
    Returns:
        JSON string of the report
    """
    score_or_class, confidence = extract_report_fields(processor, result)
    
    # Build the report structure
    report = {
        "report_version": report_version,
        "classifier_name": processor,
        "score_or_class": score_or_class,
        "confidence": float(confidence),
        "image_id": image_id,
        "case_id": case_id,
        "sample_type": sample_type,
        "raw_result": result
    }

    # Build a human-readable text version of the report for convenience/logging
    output = f"Report for case #{case_id}, type: {sample_type}\n"
    output += f"\tProcessor: {processor}\n"
    output += "\t\t" + pprint.pformat(result).replace("\n", "\n\t\t") + "\n"
    print(output)

    return json.dumps(report, indent=2)