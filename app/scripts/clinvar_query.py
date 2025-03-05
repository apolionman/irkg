import subprocess
import xml.etree.ElementTree as ET

def fetch_clinvar_variations(gene_name: str):
    # Construct the esearch command
    esearch_command = (
        f'esearch -db clinvar -query "{gene_name}[Gene] AND Homo sapiens[Organism]" |'
        'efetch -format xml'
    )

    try:
        # Run the esearch command to get the variation IDs
        esearch_result = subprocess.run(esearch_command, capture_output=True, shell=True, check=True,
                text=True)
        
        # Parse the esearch XML result to extract Variation IDs
        tree = ET.ElementTree(ET.fromstring(esearch_result.stdout))
        root = tree.getroot()

        # Extract the Variation IDs
        variation_ids = [e.text for e in root.findall(".//IdList/Id")]

        # If no variations are found
        if not variation_ids:
            return {"message": "No variations found for the given gene"}

        clinvar_data = []
        for var_id in variation_ids:
            # Construct the efetch command to fetch detailed variation info
            efetch_command = [
                "efetch", "-db", "clinvar", "-id", var_id, "-format", "xml"
            ]

            # Run the efetch command to get detailed data for each variation
            efetch_result = subprocess.run(efetch_command, capture_output=True, shell=True, check=True,
               text=True)

            # Parse the efetch XML result to extract variation details
            var_tree = ET.ElementTree(ET.fromstring(efetch_result.stdout))
            var_root = var_tree.getroot()

            for variation in var_root.findall(".//Variation"):
                gene = variation.find(".//Gene/GeneSymbol").text
                protein_change = variation.find(".//ProteinChange").text if variation.find(".//ProteinChange") is not None else "N/A"
                variation_type = variation.find(".//Type").text
                consequence = variation.find(".//Consequence").text
                condition = variation.find(".//Condition").text
                classification = variation.find(".//Classification").text
                review_status = variation.find(".//ReviewStatus").text

                # Store the parsed information
                clinvar_data.append({
                    "VariationID": var_id,
                    "Gene": {"GeneSymbol": gene},
                    "ProteinChange": protein_change,
                    "Type": variation_type,
                    "Consequence": consequence,
                    "Condition": condition,
                    "Classification": classification,
                    "ReviewStatus": review_status
                })

        return {"ClinVarSet": {"ReferenceClinVarAssertion": [{"Variation": var} for var in clinvar_data]}}

    except subprocess.CalledProcessError as e:
        return {"message": f"Error occurred while fetching data: {e.stderr}"}
