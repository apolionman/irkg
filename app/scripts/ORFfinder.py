import subprocess
import re

def parse_orf_result(output: str):
    """
    Parses the ORFfinder output into a structured dictionary format.
    """
    orfs = []
    lines = output.strip().split("\n")
    
    current_orf = {}
    sequence = []
    
    for line in lines:
        if line.startswith(">lcl|"):
            if current_orf:
                # Store the previous ORF before moving to the next one
                current_orf[orf_key] = "".join(sequence)
                orfs.append(current_orf)
            
            # Extract ORF number
            match = re.search(r"ORF(\d+)", line)
            if match:
                orf_key = f"ORF{match.group(1)}"
            else:
                orf_key = "Unnamed_ORF"

            current_orf = {"header": line}
            sequence = []
        else:
            sequence.append(line.strip())
    
    # Add the last ORF
    if current_orf:
        current_orf[orf_key] = "".join(sequence)
        orfs.append(current_orf)
    
    return {"ORFs": orfs} 


def run_orffinder(input_file: str, output_file: str, minimal_length: int = 75, start_codon: int = 1):
    """
    This function runs the ORFfinder command-line tool with the given parameters.
    """
    command = [
        "./ORFfinder", "-in", input_file, "-out", output_file, "-ml", str(minimal_length), "-s", str(start_codon)
    ]
    try:
        # Run the ORFfinder command
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return f"Error occurred: {e}"
