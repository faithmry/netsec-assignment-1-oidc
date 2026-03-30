# OIDC Client Application

A minimalist OpenID Connect (OIDC) Relying Party application built with Python Flask. This project demonstrates the integration of a client application with a modern Identity Provider, specifically **Ory Hydra**.

This application implements the standard OIDC Authorization Code Flow, allowing users to authenticate and view their decoded ID Token (JWT) claims upon successful login.

## Project Structure

Based on the repository contents, here is the breakdown of the project files:

* `app.py`: The main Flask application handling OIDC routing, callback processing, and token validation.
* `templates/`: Contains the HTML templates for the frontend UI (`base.html`, `index.html`, `profile.html`).
* `docker-compose-ory-hydra.yml`: The Docker configuration file required to deploy Ory Hydra and its necessary services (like the database and consent app).
* `register-ory-hydra.sh`: A helper shell script to automate the creation and registration of the OAuth2 client inside the Hydra container.
* `contrib/quickstart/5-min/`: Contains dependencies and configurations related to the Ory Hydra quickstart environment.
* `requirements.txt`: The list of required Python libraries for the Flask application.
* `.gitignore`: Specifies intentionally untracked files to ignore (e.g., virtual environments, cache).

## Prerequisites

Before running this project, ensure you have the following installed on your system:
* [Docker](https://www.docker.com/) and Docker Compose (for running the Identity Provider)
* [Python 3.8+](https://www.python.org/) (for running the Flask client application)

## How to Run

Follow these steps to set up and run the environment locally.

### 1. Start the Ory Hydra Provider

Run the Identity Provider and its accompanying services using Docker:

```bash
docker compose -f docker-compose-ory-hydra.yml up -d
```

### 2. Register the Client App in Hydra
Before the Flask app can communicate with Hydra, it must be registered as a valid client. Run the provided shell script to automate this process:

```Bash
# Make the script executable
chmod +x register-ory-hydra.sh

# Execute the script
./register-ory-hydra.sh
```

### 3. Setup the Flask Client Environment
Open a new terminal window, navigate to the project directory, and set up a Python virtual environment:

Create a virtual environment:

```Bash
python -m venv venv
```

Activate the virtual environment:

```Bash
venv\Scripts\activate
```

Install the required dependencies:

```Bash
pip install -r requirements.txt
```

### 4. Run the Application
Start the Flask application:

```Bash
python app.py
```

### 5. Access the Application
Open your web browser and navigate to:
`http://127.0.0.1:5000` or `http://localhost:5000`

From the home page, you can select the provider to start the login process. Upon successful authentication, you will be redirected to the profile page to inspect your user claims and the decoded JWT ID Token.
