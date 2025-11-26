"""
Format:


Report for case #{case_id}, type: {sample_type}
   Processor: {processor}
       key: value
       key:
            nested_key: nested_value
"""
def format_output(case_id, sample_type, processor, result):
    import pprint
    output = f"Report for case #{case_id}, type: {sample_type}\n"
    output += f"\tProcessor: {processor}\n"
    output += "\tResult:\n"
    output += "\t\t" + pprint.pformat(result).replace("\n", "\n\t\t") + "\n"
    return output