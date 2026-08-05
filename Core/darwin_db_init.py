import json
import urllib.request
import urllib.error
import base64

def init_darwin_db():
    base_url = "http://localhost:6363"
    db_id = "darwin"
    auth = b"admin:root"
    b64_auth = base64.b64encode(auth).decode("ascii")
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json"
    }

    print("Connecting to local TerminusDB via HTTP API (bypassing heavy clients)...")

    # 1. Create the Database
    try:
        create_url = f"{base_url}/api/db/admin/{db_id}"
        req = urllib.request.Request(create_url, method="POST", headers=headers, data=json.dumps({"label": "DARWIN", "comment": "Sovereign 4D Engine"}).encode("utf-8"))
        urllib.request.urlopen(req)
        print(f"Database '{db_id}' successfully created.")
    except urllib.error.HTTPError as e:
        if e.code == 400: # Usually means it already exists
            print(f"Database '{db_id}' already exists.")
        else:
            print(f"Failed to create DB: {e.read().decode('utf-8')}")
            return
    except Exception as e:
        print(f"Connection failed. Is TerminusDB Docker container running? Error: {e}")
        return

    # 2. Push the Schema
    schema = [
        {
            "@type": "Class",
            "@id": "OntologyPhase",
            "@inherits": "Enum",
            "@value": ["Okra", "Kyinna", "Nnyini", "Ahodin", "Mogya"]
        },
        {
            "@type": "Class",
            "@id": "CapabilityAnchor",
            "intent_hash": "xsd:string",
            "content": "xsd:string",
            "phase": "OntologyPhase"
        },
        {
            "@type": "Class",
            "@id": "PhaseState",
            "timestamp": "xsd:dateTime",
            "anchor": "CapabilityAnchor",
            "accumulated_energy": "xsd:decimal",
            "current_action": "xsd:string"
        },
        {
            "@type": "Class",
            "@id": "PropagationEdge",
            "source": "CapabilityAnchor",
            "target": "CapabilityAnchor",
            "energy_transferred": "xsd:decimal",
            "timestamp": "xsd:dateTime"
        }
    ]

    print("Pushing 4D Event-Sourced Schema...")
    try:
        schema_url = f"{base_url}/api/document/admin/{db_id}?graph_type=schema&author=admin&message=Initial%20Structural%20Schema"
        req = urllib.request.Request(schema_url, method="POST", headers=headers, data=json.dumps(schema).encode("utf-8"))
        urllib.request.urlopen(req)
        print("Schema successfully synchronized with the 4th Dimension.")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        if "TerminusDB error" in err:
            print("Schema may already exist or there was a minor conflict.")
            print(err)
        else:
            print(f"Failed to push schema: {err}")

if __name__ == "__main__":
    init_darwin_db()
