from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate():
    req = request.get_json()

    # Initialize AdmissionReview response
    admission_response = {
        "uid": req["request"]["uid"],
        "allowed": True,
    }

    # Extract the deployment spec
    deployment = req["request"]["object"]
    containers = deployment["spec"]["template"]["spec"]["containers"]

    # Check each container for resource requests
    for container in containers:
        resources = container.get("resources", {})
        requests = resources.get("requests", {})

        if not requests:
            admission_response["allowed"] = False
            admission_response["status"] = {
                "status": "Failure",
                "message": f"Deployment '{deployment['metadata']['name']}' must have resource requests specified.",
                "reason": "Invalid",
                "code": 400
            }
            break

    # Build the AdmissionReview response
    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": admission_response
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('/etc/webhook/certs/tls.crt', '/etc/webhook/certs/tls.key'))
