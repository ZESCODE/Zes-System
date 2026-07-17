#!/usr/bin/env python3
"""
ZES Pact System — Behavioral contract testing for phase-gated implementation
Inspired by devildev's pact system.
"""
import json
import os
import sys
import subprocess
from datetime import datetime

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
PACTS_DIR = os.path.join(HOME, ".zes", "pacts")

def ensure_dirs():
    os.makedirs(PACTS_DIR, exist_ok=True)

def create_pact(phase, name, description, tests, acceptance_criteria, depends_on=None):
    """Create a new pact file"""
    ensure_dirs()
    pact = {
        "id": f"pact-{phase}-{name}",
        "phase": phase,
        "name": name,
        "description": description,
        "tests": tests if isinstance(tests, list) else [tests],
        "acceptanceCriteria": acceptance_criteria if isinstance(acceptance_criteria, list) else [acceptance_criteria],
        "dependsOn": depends_on or [],
        "status": "pending",
        "createdAt": datetime.now().isoformat(),
        "results": []
    }
    fname = f"{phase}-{name}.pact.json"
    fpath = os.path.join(PACTS_DIR, fname)
    with open(fpath, "w") as f:
        json.dump(pact, f, indent=2)
    print(f"Created pact: {fname}")
    return pact

def list_pacts(phase=None):
    """List all pacts, optionally filtered by phase"""
    ensure_dirs()
    pacts = []
    for f in sorted(os.listdir(PACTS_DIR)):
        if f.endswith(".pact.json"):
            if phase and not f.startswith(str(phase)):
                continue
            with open(os.path.join(PACTS_DIR, f)) as fh:
                pacts.append(json.load(fh))
    return pacts

def run_pact(pact_id):
    """Run a pact by executing its tests"""
    ensure_dirs()
    pact_file = None
    for f in os.listdir(PACTS_DIR):
        if f.endswith(".pact.json"):
            with open(os.path.join(PACTS_DIR, f)) as fh:
                pact = json.load(fh)
                if pact["id"] == pact_id:
                    pact_file = os.path.join(PACTS_DIR, f)
                    break
    
    if not pact_file:
        print(f"Pact not found: {pact_id}")
        return False
    
    with open(pact_file) as fh:
        pact = json.load(fh)
    
    print(f"Running pact: {pact['name']}")
    print(f"  Description: {pact['description']}")
    print(f"  Tests ({len(pact['tests'])}):")
    
    results = []
    all_pass = True
    for i, test in enumerate(pact["tests"]):
        print(f"  [{i+1}/{len(pact['tests'])}] {test[:80]}...", end=" ")
        try:
            result = subprocess.run(test, shell=True, capture_output=True, 
                                     text=True, timeout=30)
            passed = result.returncode == 0
            results.append({
                "test": test,
                "passed": passed,
                "output": result.stdout[-200:] if result.stdout else result.stderr[-200:],
                "returnCode": result.returncode
            })
            print("✅ PASS" if passed else "❌ FAIL")
            if not passed:
                all_pass = False
        except subprocess.TimeoutExpired:
            results.append({"test": test, "passed": False, "output": "TIMEOUT", "returnCode": -1})
            print("❌ TIMEOUT")
            all_pass = False
        except Exception as e:
            results.append({"test": test, "passed": False, "output": str(e), "returnCode": -1})
            print(f"❌ ERROR: {e}")
            all_pass = False
    
    # Update pact status
    pact["status"] = "pass" if all_pass else "fail"
    pact["lastRun"] = datetime.now().isoformat()
    pact["results"] = results
    with open(pact_file, "w") as f:
        json.dump(pact, f, indent=2)
    
    print(f"\nResult: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
    return all_pass

def check_phase_gate(phase):
    """Check if all pacts for a given phase pass (phase gate)"""
    pacts = list_pacts(phase)
    if not pacts:
        print(f"No pacts found for phase {phase}")
        return True
    
    all_pass = True
    for pact in pacts:
        if pact["status"] != "pass":
            print(f"  ❌ {pact['name']}: {pact['status']}")
            all_pass = False
        else:
            print(f"  ✅ {pact['name']}: pass")
    
    if all_pass:
        print(f"\n✅ Phase {phase} gate: ALL PASS — can proceed to next phase")
    else:
        print(f"\n❌ Phase {phase} gate: SOME FAILED — fix before proceeding")
    
    return all_pass

def generate_phase_plan(architecture_json):
    """Generate phase plan with pacts from architecture document"""
    with open(architecture_json) as f:
        arch = json.load(f)
    
    phases = arch.get("phases", [])
    if not phases:
        # Auto-generate phases
        components = arch.get("components", arch.get("services", []))
        n = len(components)
        phase_size = max(1, n // 3)
        phases = []
        for i in range(0, n, phase_size):
            phase_comps = [c.get("id", c.get("name", f"comp{j}")) 
                          for j, c in enumerate(components[i:i+phase_size])]
            phases.append({
                "phase": len(phases) + 1,
                "components": phase_comps,
                "focus": f"Phase {len(phases) + 1}"
            })
    
    print(f"Generating pacts for {len(phases)} phases...")
    pacts_created = 0
    for phase in phases:
        pn = phase["phase"]
        comps = phase.get("components", [])
        pact = create_pact(
            phase=pn,
            name=f"phase-{pn}-gate",
            description=f"Phase {pn}: {phase.get('focus', 'implementation')}",
            tests=[f"echo 'Phase {pn} gate check — {len(comps)} components'"],
            acceptance_criteria=[f"All Phase {pn} components pass review"],
            depends_on=[f"pact-{p-1}-phase-{p-1}-gate" for p in range(1, pn)]
        )
        pacts_created += 1
    
    return pacts_created

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ZES Pact System")
    parser.add_argument("action", choices=["create", "list", "run", "gate", "plan"],
                       help="Action to perform")
    parser.add_argument("--phase", "-p", type=int, help="Phase number")
    parser.add_argument("--name", "-n", help="Pact name")
    parser.add_argument("--desc", "-d", help="Pact description")
    parser.add_argument("--test", "-t", action="append", help="Test command")
    parser.add_argument("--pact-id", help="Pact ID to run")
    parser.add_argument("--arch", help="Architecture JSON file")
    args = parser.parse_args()
    
    if args.action == "create":
        if not all([args.phase, args.name, args.desc, args.test]):
            parser.error("create requires --phase, --name, --desc, and --test")
        create_pact(args.phase, args.name, args.desc, args.test, [])
    
    elif args.action == "list":
        pacts = list_pacts(args.phase)
        print(f"Pacts ({len(pacts)}):")
        for p in pacts:
            status_icon = {"pass": "✅", "fail": "❌", "pending": "⬜"}
            print(f"  {status_icon.get(p['status'], '⬜')} {p['id']}: {p['description']}")
    
    elif args.action == "run":
        if not args.pact_id:
            parser.error("run requires --pact-id")
        run_pact(args.pact_id)
    
    elif args.action == "gate":
        if not args.phase:
            parser.error("gate requires --phase")
        check_phase_gate(args.phase)
    
    elif args.action == "plan":
        if not args.arch:
            parser.error("plan requires --arch")
        count = generate_phase_plan(args.arch)
        print(f"Created {count} pacts")

if __name__ == "__main__":
    main()
