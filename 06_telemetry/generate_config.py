import os
from datetime import datetime

def parse_yaml(filepath):
    config = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Handle comments at the end of a line
            if '#' in line:
                line = line.split('#')[0].strip()
            if ':' not in line:
                continue
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            
            # Strip quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            else:
                # Try parsing to numeric types
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except ValueError:
                    pass
            config[key] = val
    return config

def generate_sas_config(config, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("/* ==============================================================================\n")
        f.write("   Generated automatically from study_config.yaml. Do not edit directly.\n")
        f.write("   Generated on: " + datetime.now().isoformat() + "\n")
        f.write("   ============================================================================== */\n\n")
        
        for key, val in config.items():
            # Format value for SAS
            if key == "STUDY_CUTOFF_DT":
                # Convert 2009-09-25 to '25SEP2009'd
                dt = datetime.strptime(val, "%Y-%m-%d")
                sas_val = f"'{dt.strftime('%d%b%Y').upper()}'d"
            elif isinstance(val, (int, float)):
                sas_val = str(val)
            else:
                sas_val = str(val)
            
            f.write(f"%global {key};\n")
            f.write(f"%let {key} = {sas_val};\n\n")

def main():
    # Resolve the study root from the current working directory first (multi-study:
    # cibuild chdirs into the active study root), falling back to the engine location
    # for a standalone/default invocation.
    proj_root = os.getcwd()
    if not os.path.exists(os.path.join(proj_root, "study_config.yaml")):
        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(proj_root, "study_config.yaml")
    sas_out_path = os.path.join(proj_root, "02_production_sas", "00_config_generated.sas")
    
    print(f"Reading configuration from: {yaml_path}")
    config = parse_yaml(yaml_path)
    print(f"Generating SAS configuration at: {sas_out_path}")
    generate_sas_config(config, sas_out_path)
    print("Configuration generation complete!")

if __name__ == "__main__":
    main()
