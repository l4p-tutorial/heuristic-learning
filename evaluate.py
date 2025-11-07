import os
import argparse
import subprocess
import tempfile
import zipfile

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
GOOSE_SIF = f"{ROOT_DIR}/goose.sif"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a trained model on a dataset.")
    parser.add_argument("domain_pddl", type=str, help="Path to the domain PDDL file.")
    parser.add_argument("problem_pddl", type=str, help="Path to the problem PDDL file.")
    parser.add_argument("model_path", type=str, help="Path to the trained model file.")
    args = parser.parse_args()
    
    assert os.path.exists(args.domain_pddl), f"Domain PDDL file {args.domain_pddl} does not exist."
    assert os.path.exists(args.problem_pddl), f"Problem PDDL file {args.problem_pddl} does not exist."
    assert os.path.exists(args.model_path), f"Model file {args.model_path} does not exist."
    assert not os.path.isdir(args.model_path), f"Model path {args.model_path} is a directory, expected a file."
    
    if not os.path.exists(GOOSE_SIF):
        print("Goose apptainer image does not exist, downloading...")
        if subprocess.run(["which", "apptainer"], capture_output=True, text=True, check=False).stdout == 0:
            print("The command `apptainer` was not found. Please install with sudo apt install -y apptainer")
            exit(0)
        subprocess.run(["apptainer", "pull", GOOSE_SIF, "oras://ghcr.io/dillonzchen/goose:latest"], check=True)
    
    with tempfile.TemporaryDirectory() as tempdir:
        params_file = f"{tempdir}/blocksworld.model.params"
        opts_file = f"{tempdir}/blocksworld.model.opts"
        model_file = f"{tempdir}/blocksworld.model"
        subprocess.run(["cp", args.model_path, params_file], check=True)
        with open(opts_file, "w") as f:
            f.write('{"mode": "wlf", "policy_type": "search", "state_representation": "downward"}\n')
        with zipfile.ZipFile(model_file, 'w') as model_zip:
            model_zip.write(opts_file)
            model_zip.write(params_file)
            
        subprocess.run([GOOSE_SIF, "plan", args.domain_pddl, args.problem_pddl, "-m", model_file], check=True)
